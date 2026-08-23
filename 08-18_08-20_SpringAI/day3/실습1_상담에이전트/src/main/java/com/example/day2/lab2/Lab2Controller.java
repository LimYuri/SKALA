package com.example.day2.lab2;

import jakarta.validation.Valid;
import java.util.List;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.core.io.Resource;
import org.springframework.http.HttpStatus;
import org.springframework.web.bind.annotation.*;

@RestController
@RequestMapping("/lab2")
public class Lab2Controller {
    private final Lab2IngestService ingestService;
    private final Lab2RetrievalService retrievalService;
    private final Lab2AnswerService answerService;
    private final Lab2Properties properties;

    @Value("classpath:lab2-docs/return-policy.md") Resource returnPolicy;
    @Value("classpath:lab2-docs/shipping-policy.md") Resource shippingPolicy;
    @Value("classpath:lab2-docs/membership.md") Resource membership;

    public Lab2Controller(Lab2IngestService ingestService, Lab2RetrievalService retrievalService,
                          Lab2AnswerService answerService, Lab2Properties properties) {
        this.ingestService = ingestService;
        this.retrievalService = retrievalService;
        this.answerService = answerService;
        this.properties = properties;
    }

    @PostMapping("/ingest")
    public List<IngestResult> ingest() {
        String version = properties.version();
        return List.of(
                ingestService.ingest(returnPolicy, "return-policy.md", version),
                ingestService.ingest(shippingPolicy, "shipping-policy.md", version),
                ingestService.ingest(membership, "membership.md", version));
    }

    @GetMapping("/retrieve")
    public List<ChunkDto> retrieve(@RequestParam("q") String q,
                                   @RequestParam(defaultValue = "4") Integer topK,
                                   @RequestParam(required = false) Double threshold) {
        return retrievalService.retrieve(q, topK, threshold);
    }

    @PostMapping("/ask")
    public AnswerDto ask(@Valid @RequestBody AskRequest request) {
        return answerService.ask(request.question(), request.topK(), request.threshold());
    }

    @ExceptionHandler(RuntimeException.class)
    @ResponseStatus(HttpStatus.SERVICE_UNAVAILABLE)
    public ApiError generationFailure(RuntimeException ex) {
        return new ApiError("GENERATION_FAILED", "답변 생성에 실패했습니다. 잠시 후 다시 시도해 주세요.");
    }

    public record ApiError(String code, String message) {}
}
