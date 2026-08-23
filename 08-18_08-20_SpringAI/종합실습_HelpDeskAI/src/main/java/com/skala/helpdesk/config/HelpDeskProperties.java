package com.skala.helpdesk.config;

import org.springframework.boot.context.properties.ConfigurationProperties;

// application.yml의 helpdesk.* 값들을 묶어놓은 설정 - 코드에 하드코딩 안 하려고 여기로 다 뺌
@ConfigurationProperties("helpdesk")
public record HelpDeskProperties(
        Rag rag,
        Memory memory,
        Safety safety,
        Model model,
        boolean liveAiEnabled,
        long p95TargetMillis,
        double averageTokenLimit) {
    public record Rag(int topK, double threshold, int chunkSize, int minChunkSizeChars) {}
    public record Memory(int maxMessages) {}
    public record Safety(int maxInputChars, int maxToolCalls) {}
    public record Model(String primary, String fallback) {}
}
