package com.skala.helpdesk.config;

import org.springframework.ai.embedding.EmbeddingModel;
import org.springframework.ai.vectorstore.VectorStore;
import org.springframework.ai.vectorstore.pgvector.PgVectorStore;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.context.annotation.Profile;
import org.springframework.jdbc.core.JdbcTemplate;

// pgvector 프로필로 띄울 때만 활성화되는 대체 VectorStore.
// 기본 실행(AiConfig의 SimpleVectorStore)에는 영향 없음 - 필요하면 --spring.profiles.active=pgvector로만 켜짐
@Configuration
@Profile("pgvector")
public class PgVectorConfig {
    @Bean
    public VectorStore vectorStore(JdbcTemplate jdbcTemplate, EmbeddingModel embeddingModel) {
        // OpenAI text-embedding 차원(1536)에 맞춤, 스키마는 최초 기동시 자동 생성
        return PgVectorStore.builder(jdbcTemplate, embeddingModel)
                .dimensions(1536)
                .initializeSchema(true)
                .build();
    }
}
