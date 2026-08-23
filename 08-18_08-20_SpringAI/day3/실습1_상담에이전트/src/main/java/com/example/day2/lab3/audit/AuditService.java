package com.example.day2.lab3.audit;

import java.time.Instant;
import java.util.List;
import java.util.concurrent.CopyOnWriteArrayList;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.slf4j.MDC;
import org.springframework.stereotype.Service;

@Service
public class AuditService {
    private static final Logger log = LoggerFactory.getLogger(AuditService.class);
    private final List<AuditEvent> events = new CopyOnWriteArrayList<>();
    public void record(String action, String userId, String arguments, String result) {
        String traceId = MDC.get("traceId");
        AuditEvent event = new AuditEvent(Instant.now(), traceId == null ? "no-trace" : traceId,
                action, userId, mask(arguments), mask(result));
        events.add(event);
        log.info("LAB3_AUDIT traceId={} action={} user={} args={} result={}",
                event.traceId(), action, userId, event.arguments(), event.result());
    }
    public List<AuditEvent> events() { return List.copyOf(events); }
    private String mask(String value) {
        return value == null ? "" : value.replaceAll("(\\d{6})[- ]?[1-4]\\d{6}", "$1-*******");
    }
    public record AuditEvent(Instant time, String traceId, String action, String userId, String arguments, String result) {}
}
