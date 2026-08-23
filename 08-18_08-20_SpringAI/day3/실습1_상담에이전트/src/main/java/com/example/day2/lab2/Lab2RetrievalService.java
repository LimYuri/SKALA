package com.example.day2.lab2;

import java.util.List;
import org.springframework.ai.document.Document;
import org.springframework.ai.vectorstore.SearchRequest;
import org.springframework.ai.vectorstore.VectorStore;
import org.springframework.stereotype.Service;

@Service
public class Lab2RetrievalService {
    private final VectorStore vectorStore;
    private final Lab2Properties properties;

    public Lab2RetrievalService(VectorStore vectorStore, Lab2Properties properties) {
        this.vectorStore = vectorStore;
        this.properties = properties;
    }

    public List<Document> retrieveDocuments(String question, Integer topK, Double threshold) {
        int effectiveTopK = topK == null ? properties.topK() : topK;
        double effectiveThreshold = threshold == null ? properties.threshold() : threshold;
        return vectorStore.similaritySearch(SearchRequest.builder()
                .query(question).topK(effectiveTopK)
                .similarityThreshold(effectiveThreshold).build());
    }

    public List<ChunkDto> retrieve(String question, Integer topK, Double threshold) {
        return retrieveDocuments(question, topK, threshold).stream()
                .map(d -> new ChunkDto(String.valueOf(d.getMetadata().get("source")),
                        d.getScore(), snippet(d.getText(), 120)))
                .toList();
    }

    private String snippet(String text, int max) {
        String oneLine = text.replaceAll("\\s+", " ").trim();
        return oneLine.length() <= max ? oneLine : oneLine.substring(0, max) + "...";
    }
}
