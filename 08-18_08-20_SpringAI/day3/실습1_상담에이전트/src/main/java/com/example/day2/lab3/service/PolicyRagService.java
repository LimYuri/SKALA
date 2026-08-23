package com.example.day2.lab3.service;

import java.io.IOException;
import java.nio.charset.StandardCharsets;
import java.util.List;
import java.util.Map;
import org.springframework.ai.document.Document;
import org.springframework.ai.transformer.splitter.TokenTextSplitter;
import org.springframework.ai.vectorstore.SearchRequest;
import org.springframework.ai.vectorstore.VectorStore;
import org.springframework.ai.vectorstore.filter.FilterExpressionBuilder;
import org.springframework.core.io.ResourceLoader;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Service;

@Service
public class PolicyRagService {
    private final String returns;
    private final String shipping;
    private final VectorStore vectorStore;
    private final boolean liveAiEnabled;
    private volatile boolean indexed;
    @Autowired
    public PolicyRagService(ResourceLoader loader, VectorStore vectorStore,
                            @Value("${lab3.live-ai-enabled:false}") boolean liveAiEnabled) throws IOException {
        this.vectorStore = vectorStore;
        this.liveAiEnabled = liveAiEnabled;
        this.returns = loader.getResource("classpath:lab3-docs/return-policy.md").getContentAsString(StandardCharsets.UTF_8);
        this.shipping = loader.getResource("classpath:lab3-docs/shipping-policy.md").getContentAsString(StandardCharsets.UTF_8);
    }
    public PolicyRagService(ResourceLoader loader) throws IOException { this(loader, null, false); }

    public List<IngestResult> ingest() {
        if (vectorStore == null) return List.of();
        List<IngestResult> results = new java.util.ArrayList<>();
        results.add(index("return-policy.md", returns));
        results.add(index("shipping-policy.md", shipping));
        indexed = true;
        return results;
    }
    private IngestResult index(String source, String content) {
        Document original = new Document(content, Map.of("source", source, "version", "v1"));
        List<Document> chunks = TokenTextSplitter.builder().withChunkSize(400).build().apply(List.of(original));
        chunks.forEach(d -> { d.getMetadata().put("source", source); d.getMetadata().put("version", "v1"); });
        vectorStore.delete(new FilterExpressionBuilder().eq("source", source).build());
        vectorStore.add(chunks);
        return new IngestResult(source, chunks.size());
    }
    public List<PolicyHit> retrieve(String question) {
        if (liveAiEnabled && vectorStore != null) {
            try {
                // Day 2의 /lab2/ingest가 채운 동일 VectorStore를 그대로 검색한다.
                List<Document> documents = vectorStore.similaritySearch(SearchRequest.builder()
                        .query(question).topK(3).similarityThreshold(0.5).build());
                if (!documents.isEmpty()) return documents.stream()
                        .map(d -> new PolicyHit(String.valueOf(d.getMetadata().get("source")), d.getText())).toList();
            } catch (RuntimeException ignored) {
                // API 키가 없는 로컬 단위 테스트에서는 아래 고정 문서 검색으로 안전하게 폴백한다.
            }
        }
        String q = question.toLowerCase();
        if (q.matches(".*(반품|환불|교환).*")) return List.of(new PolicyHit("return-policy.md", returns));
        if (q.matches(".*(배송|출고|도착).*")) return List.of(new PolicyHit("shipping-policy.md", shipping));
        return List.of();
    }
    public record PolicyHit(String source, String content) {}
    public record IngestResult(String source, int chunks) {}
}
