package com.skala.helpdesk.advisor;

import java.util.ArrayList;
import java.util.List;
import org.aspectj.lang.ProceedingJoinPoint;
import org.aspectj.lang.annotation.Around;
import org.aspectj.lang.annotation.Aspect;
import org.springframework.ai.chat.model.ToolContext;
import org.springframework.stereotype.Component;

// @Tool 붙은 메서드마다 로그 남기는 코드를 반복해서 넣기 싫어서 AOP로 한 곳에 모음.
// OrderTools/TicketTools 쪽에는 감사 로그 코드가 없는 이유가 이거임 - 여기서 전부 가로채서 처리
@Aspect
@Component
public class ToolAuditAspect {
    private final AuditService audit;

    public ToolAuditAspect(AuditService audit) {
        this.audit = audit;
    }

    @Around("@annotation(org.springframework.ai.tool.annotation.Tool)")
    public Object auditToolCall(ProceedingJoinPoint joinPoint) throws Throwable {
        long started = System.nanoTime();
        String toolName = joinPoint.getSignature().getName();
        String userId = userId(joinPoint.getArgs());
        String arguments = arguments(joinPoint.getArgs());

        try {
            Object result = joinPoint.proceed();
            audit.record(toolName, userId, arguments,
                    "status=SUCCESS,durationMs=%d,result=%s".formatted(
                            elapsedMillis(started), String.valueOf(result)));
            return result;
        } catch (Throwable failure) {
            audit.record(toolName, userId, arguments,
                    "status=FAILED,durationMs=%d,error=%s,message=%s".formatted(
                            elapsedMillis(started), failure.getClass().getSimpleName(),
                            String.valueOf(failure.getMessage())));
            throw failure;
        }
    }

    private String userId(Object[] args) {
        for (Object arg : args) {
            if (arg instanceof ToolContext context) {
                Object value = context.getContext().get("userId");
                if (value != null && !value.toString().isBlank()) return value.toString();
            }
        }
        return "server";
    }

    private String arguments(Object[] args) {
        List<String> values = new ArrayList<>();
        for (int i = 0; i < args.length; i++) {
            if (!(args[i] instanceof ToolContext)) {
                values.add("arg%d=%s".formatted(i, mask(args[i])));
            }
        }
        return String.join(",", values);
    }

    // 인자 전체를 로그에 다 남기면 개인정보성 값(주문번호, 사유 등)이 그대로 노출되니 앞뒤 2글자만 남기고 가림
    private String mask(Object value) {
        if (value == null) return "null";
        String text = String.valueOf(value);
        if (text.length() <= 4) return "***";
        return text.substring(0, 2) + "***" + text.substring(text.length() - 2);
    }

    private long elapsedMillis(long started) {
        return (System.nanoTime() - started) / 1_000_000;
    }
}
