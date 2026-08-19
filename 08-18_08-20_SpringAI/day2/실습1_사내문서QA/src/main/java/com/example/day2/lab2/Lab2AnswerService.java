package com.example.day2.lab2;

import java.util.LinkedHashSet;
import java.util.List;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.ai.chat.client.ChatClient;
import org.springframework.ai.document.Document;
import org.springframework.stereotype.Service;

@Service
public class Lab2AnswerService {
    private static final Logger log = LoggerFactory.getLogger(Lab2AnswerService.class);
    private final Lab2RetrievalService retrievalService;
    private final ChatClient chatClient;

    public Lab2AnswerService(Lab2RetrievalService retrievalService, ChatClient.Builder builder) {
        this.retrievalService = retrievalService;
        this.chatClient = builder.build();
    }

    public AnswerDto ask(String question, Integer topK, Double threshold) {
        List<Document> docs = retrievalService.retrieveDocuments(question, topK, threshold);
        if (docs.isEmpty()) {
            log.warn("LAB2_SEARCH_FAILURE question={} reason=no_document", question);
            return AnswerDto.unknown();
        }

        List<String> allowedSources = docs.stream()
                .map(d -> String.valueOf(d.getMetadata().get("source")))
                .collect(java.util.stream.Collectors.collectingAndThen(
                        java.util.stream.Collectors.toCollection(LinkedHashSet::new), List::copyOf));
        try {
            AnswerDto generated = chatClient.prompt()
                    .system("""
                            아래 [근거]만 사용해 답한다.
                            근거에 없으면 정확히 "확인되지 않습니다."라고 답한다.
                            추측하거나 외부 지식을 사용하지 않는다.
                            sources에는 실제 사용한 source만 넣는다.
                            answer 끝에는 [출처: source] 형식으로 출처를 표시한다.
                            grounded는 근거로 답할 수 있을 때만 true다.
                            """)
                    .user(u -> u.text("[근거]\n{context}\n\n[질문]\n{question}")
                            .param("context", format(docs))
                            .param("question", question))
                    .call().entity(AnswerDto.class);
            return normalize(generated, allowedSources);
        } catch (RuntimeException ex) {
            log.error("LAB2_GENERATION_FAILURE question={} sources={} message={}",
                    question, allowedSources, ex.getMessage(), ex);
            throw ex;
        }
    }

    private AnswerDto normalize(AnswerDto answer, List<String> allowedSources) {
        if (answer == null || answer.answer() == null || answer.answer().contains("확인되지")) {
            return AnswerDto.unknown();
        }
        List<String> safeSources = answer.sources() == null ? List.of() : answer.sources().stream()
                .filter(allowedSources::contains).distinct().toList();
        if (safeSources.isEmpty()) return AnswerDto.unknown();
        return new AnswerDto(answer.answer(), safeSources, true);
    }

    private String format(List<Document> docs) {
        return docs.stream().map(d -> "[source=" + d.getMetadata().get("source") + "]\n" + d.getText())
                .collect(java.util.stream.Collectors.joining("\n\n---\n\n"));
    }
}
