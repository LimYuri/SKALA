package com.skala.helpdesk.chat;

import com.skala.helpdesk.advisor.AuditService;
import io.micrometer.core.instrument.MeterRegistry;
import java.io.IOException;
import org.springframework.ai.retry.TransientAiException;
import org.springframework.retry.annotation.Backoff;
import org.springframework.retry.annotation.Recover;
import org.springframework.retry.annotation.Retryable;
import org.springframework.stereotype.Component;

// 1차 모델 -> 2차 모델 -> 로컬(결정론적 응답) 3단계 폴백.
// primary 호출은 Spring Retry가 최대 3번(1s, 2s 백오프)까지 재시도하고, 그래도 안 되면 recover()로 넘어가서
// fallback 모델을 시도하고, 그것마저 실패하면 local을 씀 - 즉 모델이 전부 죽어도 서비스는 절대 죽지 않게 설계
@Component
public class ModelFallbackExecutor {
    private final AuditService audit;
    private final MeterRegistry meters;
    public ModelFallbackExecutor(AuditService audit, MeterRegistry meters) {
        this.audit = audit; this.meters = meters;
    }

    @Retryable(
            retryFor = {TransientAiException.class, IOException.class},
            noRetryFor = {IllegalArgumentException.class},
            notRecoverable = {IllegalArgumentException.class},
            maxAttempts = 3,
            backoff = @Backoff(delay = 1000, multiplier = 2.0),
            recover = "recover"
    )
    public Result execute(String userId, String primaryName, String fallbackName,
                          Operation primary, Operation fallback,
                          Operation local) throws Exception {
        return new Result(primary.run(), false, false);
    }

    // primary가 재시도까지 다 소진하고 실패하면 Spring Retry가 여기로 넘겨줌
    @Recover
    public Result recover(Exception primaryFailure, String userId,
                          String primaryName, String fallbackName,
                          Operation primary, Operation fallback,
                          Operation local) throws Exception {
        audit.record("MODEL_FALLBACK", userId, primaryName,
                primaryFailure.getClass().getSimpleName());
        meters.counter("ai.model.fallback", "stage", "secondary").increment();

        try {
            return new Result(fallback.run(), true, false);
        } catch (Exception fallbackFailure) {
            // 2차 모델까지 죽으면 마지막 안전망으로 로컬 결정론적 응답 사용
            audit.record("MODEL_FALLBACK", userId, fallbackName,
                    fallbackFailure.getClass().getSimpleName());
            meters.counter("ai.model.fallback", "stage", "local").increment();
            return new Result(local.run(), true, true);
        }
    }

    @FunctionalInterface
    public interface Operation {
        Object run() throws Exception;
    }

    public record Result(Object value, boolean fallbackUsed, boolean localUsed) {}
}
