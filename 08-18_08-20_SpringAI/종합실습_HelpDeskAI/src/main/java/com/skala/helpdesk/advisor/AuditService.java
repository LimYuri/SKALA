package com.skala.helpdesk.advisor;

import java.time.Instant;
import java.util.List;
import java.util.concurrent.CopyOnWriteArrayList;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.slf4j.MDC;
import org.springframework.stereotype.Service;

// 감사 로그를 메모리 리스트 + 슬랙/파일 대신 그냥 로그로도 남김.
// 재부팅하면 사라지는 건 알지만 이번 과제 범위에서는 DB 테이블까지는 안 만들어도 될 것 같아서 이렇게 함
@Service
public class AuditService {
    private static final Logger log = LoggerFactory.getLogger(AuditService.class);
    private final List<AuditEvent> events = new CopyOnWriteArrayList<>();
    public void record(String action, String userId, String arguments, String result) {
        String traceId = MDC.get("traceId");
        AuditEvent event = new AuditEvent(Instant.now(), traceId == null ? "no-trace" : traceId,
                action, userId, mask(arguments), mask(result));
        events.add(event);
        log.info("HELPDESK_AUDIT traceId={} action={} user={} args={} result={}",
                event.traceId(), action, userId, event.arguments(), event.result());
    }
    public List<AuditEvent> events() { return List.copyOf(events); }
    // 주민등록번호/카드번호 패턴이 감사 로그에 그대로 찍히면 안 되니 여기서 한 번 더 마스킹
    private String mask(String value) {
        return value == null ? "" : value.replaceAll("(\\d{6})[- ]?[1-4]\\d{6}", "$1-*******")
                .replaceAll("(\\d{4})[- ]?\\d{4}[- ]?\\d{4}[- ]?(\\d{4})", "$1-****-****-$2");
    }
    public record AuditEvent(Instant time, String traceId, String action, String userId,
                             String arguments, String result) {}
}
