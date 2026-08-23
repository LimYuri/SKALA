package com.example.day2.lab2;

import org.springframework.boot.context.properties.ConfigurationProperties;

@ConfigurationProperties("lab2.rag")
public record Lab2Properties(
        int chunkSize,
        int minChunkSizeChars,
        int minChunkLengthToEmbed,
        int maxNumChunks,
        boolean keepSeparator,
        int overlapChars,
        int topK,
        double threshold,
        String version
) {
}
