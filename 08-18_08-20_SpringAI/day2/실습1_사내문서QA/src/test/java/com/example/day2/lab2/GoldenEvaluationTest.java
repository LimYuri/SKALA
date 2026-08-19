package com.example.day2.lab2;

import static org.assertj.core.api.Assertions.assertThat;
import com.fasterxml.jackson.core.type.TypeReference;
import com.fasterxml.jackson.databind.ObjectMapper;
import java.io.InputStream;
import java.util.List;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.condition.EnabledIfSystemProperty;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.context.SpringBootTest;

@SpringBootTest
@EnabledIfSystemProperty(named = "lab2.eval.enabled", matches = "true")
class GoldenEvaluationTest {
    private static final Logger log = LoggerFactory.getLogger(GoldenEvaluationTest.class);
    @Autowired Lab2Controller controller;
    @Autowired Lab2AnswerService service;
    @Autowired ObjectMapper mapper;

    @Test
    void 골든_세트_평가() throws Exception {
        controller.ingest();
        try (InputStream in = getClass().getResourceAsStream("/golden.json")) {
            List<Golden> golden = mapper.readValue(in, new TypeReference<>() {});
            int pass = 0;
            for (Golden g : golden) {
                AnswerDto answer = service.ask(g.q(), null, null);
                boolean hit = g.must().stream().allMatch(answer.answer()::contains);
                boolean cite = g.src() == null
                        ? answer.sources().isEmpty() && !answer.grounded()
                        : answer.sources().stream().anyMatch(s -> s.contains(g.src()));
                if (hit && cite) {
                    pass++;
                    log.info("EVAL_PASS question={} sources={}", g.q(), answer.sources());
                } else if (answer.sources().isEmpty()) {
                    log.warn("EVAL_SEARCH_FAILURE question={} answer={}", g.q(), answer.answer());
                } else {
                    log.warn("EVAL_GENERATION_FAILURE question={} answer={} sources={}",
                            g.q(), answer.answer(), answer.sources());
                }
            }
            log.info("EVAL_RESULT pass={}/{}", pass, golden.size());
            assertThat(pass).isGreaterThanOrEqualTo(8);
        }
    }

    record Golden(String q, List<String> must, String src) {}
}
