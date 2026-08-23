package com.example.day2.lab2;

import java.util.List;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.ai.document.Document;
import org.springframework.ai.reader.TextReader;
import org.springframework.ai.transformer.splitter.TokenTextSplitter;
import org.springframework.ai.vectorstore.VectorStore;
import org.springframework.ai.vectorstore.filter.FilterExpressionBuilder;
import org.springframework.core.io.Resource;
import org.springframework.stereotype.Service;

@Service
public class Lab2IngestService {
    private static final Logger log = LoggerFactory.getLogger(Lab2IngestService.class);
    private final VectorStore vectorStore;
    private final Lab2Properties properties;

    public Lab2IngestService(VectorStore vectorStore, Lab2Properties properties) {
        this.vectorStore = vectorStore;
        this.properties = properties;
    }

    public IngestResult ingest(Resource resource, String source, String version) {
        TextReader reader = new TextReader(resource);
        reader.getCustomMetadata().put("source", source);
        reader.getCustomMetadata().put("version", version);

        TokenTextSplitter splitter = TokenTextSplitter.builder()
                .withChunkSize(properties.chunkSize())
                .withMinChunkSizeChars(properties.minChunkSizeChars())
                .withMinChunkLengthToEmbed(properties.minChunkLengthToEmbed())
                .withMaxNumChunks(properties.maxNumChunks())
                .withKeepSeparator(properties.keepSeparator())
                .build();
        List<Document> chunks = splitter.apply(reader.get());
        chunks = addCharacterOverlap(chunks, properties.overlapChars());

        // TextReader가 기본 파일명 메타데이터를 추가하더라도 삭제 조건과 저장값이
        // 반드시 동일하도록 최종 청크에 canonical source/version을 다시 주입한다.
        chunks.forEach(chunk -> {
            chunk.getMetadata().put("source", source);
            chunk.getMetadata().put("version", version);
        });

        vectorStore.delete(new FilterExpressionBuilder().eq("source", source).build());
        vectorStore.add(chunks);
        log.info("LAB2_INGEST source={} version={} chunks={}", source, version, chunks.size());
        return new IngestResult(source, chunks.size());
    }

    private List<Document> addCharacterOverlap(List<Document> chunks, int overlap) {
        if (overlap <= 0 || chunks.size() < 2) return chunks;
        for (int i = 1; i < chunks.size(); i++) {
            String previous = chunks.get(i - 1).getText();
            String current = chunks.get(i).getText();
            String prefix = previous.substring(Math.max(0, previous.length() - overlap));
            chunks.set(i, new Document(prefix + "\n" + current, chunks.get(i).getMetadata()));
        }
        return chunks;
    }
}
