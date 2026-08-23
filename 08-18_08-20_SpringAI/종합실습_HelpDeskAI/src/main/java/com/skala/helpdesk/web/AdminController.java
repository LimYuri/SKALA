package com.skala.helpdesk.web;

import com.skala.helpdesk.advisor.AuditService;
import com.skala.helpdesk.config.HelpDeskProperties;
import com.skala.helpdesk.rag.IngestService;
import com.skala.helpdesk.repository.TicketRepository;
import io.micrometer.core.instrument.MeterRegistry;
import java.security.Principal;
import java.util.List;
import org.springframework.http.HttpStatus;
import org.springframework.security.access.prepost.PreAuthorize;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RestController;
import org.springframework.web.server.ResponseStatusException;
import org.springframework.web.server.ServerWebExchange;
import org.slf4j.MDC;
import reactor.core.publisher.Flux;
import reactor.core.publisher.Mono;
import reactor.core.scheduler.Schedulers;

// 클래스 레벨에 @PreAuthorize 걸어놔서 이 컨트롤러 전체가 ADMIN role 없으면 403.
// 일반 유저(user1/user2)가 여기 아무거나 호출하면 무조건 막힘 - 권한 분리 요구사항 담당
@RestController
@RequestMapping("/api/admin")
@PreAuthorize("hasRole('ADMIN')")
public class AdminController {
    private final IngestService ingest;
    private final TicketRepository tickets;
    private final AuditService audit;
    private final MeterRegistry meters;
    private final HelpDeskProperties props;

    public AdminController(IngestService ingest, TicketRepository tickets, AuditService audit,
                           MeterRegistry meters, HelpDeskProperties props) {
        this.ingest = ingest; this.tickets = tickets; this.audit = audit; this.meters = meters; this.props = props;
    }

    @PostMapping("/ingest")
    public Mono<List<IngestService.IngestResult>> ingest() {
        return Mono.fromCallable(ingest::ingestAll).subscribeOn(Schedulers.boundedElastic());
    }

    @GetMapping("/chunks")
    public Mono<List<IngestService.ChunkView>> chunks(@RequestParam String q,
            @RequestParam(defaultValue = "5") int topK) {
        return Mono.fromCallable(() -> ingest.inspect(q, topK)).subscribeOn(Schedulers.boundedElastic());
    }

    @GetMapping("/tickets/pending")
    public Flux<TicketRepository.Ticket> pending() {
        return Flux.fromIterable(tickets.pending());
    }

    // 티켓 승인은 여기서만 가능함 - createTicket 툴은 절대 이 상태로 못 넘어감(PENDING까지만 만듦)
    @PostMapping("/tickets/{no}/approve")
    public Mono<TicketRepository.Ticket> approve(@PathVariable String no, Principal admin,
                                                 ServerWebExchange exchange) {
        return Mono.fromCallable(() -> {
            TicketRepository.Ticket ticket = tickets.approve(no)
                    .orElseThrow(() -> new ResponseStatusException(HttpStatus.NOT_FOUND));
            String traceId = String.valueOf(exchange.getAttributeOrDefault("traceId", "no-trace"));
            MDC.put("traceId", traceId);
            try { audit.record("TICKET_APPROVED", admin.getName(), "ticket=" + no, "APPROVED"); }
            finally { MDC.remove("traceId"); }
            return ticket;
        }).subscribeOn(Schedulers.boundedElastic());
    }

    @GetMapping("/audit")
    public Flux<AuditService.AuditEvent> audit() { return Flux.fromIterable(audit.events()); }

    // p95 목표(props.p95TargetMillis)랑 비교할 수 있게 실측 p95도 같이 내려줌.
    // Micrometer가 percentile 히스토그램을 안 켜둔 상태일 수도 있어서 없으면 max로 대체
    @GetMapping("/metrics/summary")
    public Mono<MetricsSummary> metrics() {
        return Mono.fromCallable(() -> {
            double requests = value("ai.requests");
            double tokens = value("ai.tokens");
            double p95 = meters.find("ai.latency").timers().stream().mapToDouble(timer -> {
                double percentile = java.util.Arrays.stream(timer.takeSnapshot().percentileValues())
                        .filter(v -> Math.abs(v.percentile() - 0.95) < 0.001)
                        .map(v -> v.value(java.util.concurrent.TimeUnit.MILLISECONDS)).findFirst().orElse(0.0);
                return percentile > 0 ? percentile : timer.max(java.util.concurrent.TimeUnit.MILLISECONDS);
            }).max().orElse(0.0);
            return new MetricsSummary(p95, props.p95TargetMillis(), requests == 0 ? 0 : tokens / requests,
                    props.averageTokenLimit(), value("ai.cost.usd"), value("ai.model.fallback"));
        }).subscribeOn(Schedulers.boundedElastic());
    }

    private double value(String name) {
        return meters.getMeters().stream().filter(meter -> meter.getId().getName().equals(name))
                .flatMap(meter -> java.util.stream.StreamSupport.stream(meter.measure().spliterator(), false))
                .filter(measurement -> measurement.getStatistic() == io.micrometer.core.instrument.Statistic.COUNT)
                .mapToDouble(io.micrometer.core.instrument.Measurement::getValue).sum();
    }

    public record MetricsSummary(double p95Millis, long p95TargetMillis, double averageTokens,
                                 double averageTokenLimit, double estimatedCostUsd, double fallbackCount) {}
}