package com.skala.helpdesk;

import static org.assertj.core.api.Assertions.assertThat;

import com.skala.helpdesk.chat.AnswerDto;
import com.skala.helpdesk.chat.HelpDeskService;
import com.skala.helpdesk.eval.GoldenSet;
import java.util.stream.Stream;
import org.junit.jupiter.params.ParameterizedTest;
import org.junit.jupiter.params.provider.MethodSource;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.context.SpringBootTest;

@SpringBootTest(properties = "helpdesk.live-ai-enabled=false")
class GoldenSetTest {
    @Autowired HelpDeskService service;

    @ParameterizedTest(name = "GoldenSet: {0}")
    @MethodSource("goldenCases")
    void GoldenSet_16건을_deterministic_모드로_검증한다(GoldenSet.Case golden) {
        String sessionId = "golden-" + Math.abs(golden.question().hashCode());
        if (golden.expected().equals("createTicket")) {
            service.ask("주문 12345 어디예요?", "skala", "user1", sessionId);
        }

        AnswerDto actual = service.ask(golden.question(), "skala", "user1", sessionId);

        switch (golden.expected()) {
            case "return-policy.md", "shipping-policy.md" ->
                    assertThat(actual.sources()).extracting(AnswerDto.Source::document)
                            .contains(golden.expected());
            case "orderStatus", "createTicket" ->
                    assertThat(actual.toolsCalled()).contains(golden.expected());
            case "denied" -> assertThat(actual.answer()).contains("찾을 수 없습니다");
            case "unknown" -> assertThat(actual.answer()).contains("확인할 수 없습니다");
            case "blocked" -> assertThat(actual.answer())
                    .containsAnyOf("제공할 수 없습니다", "처리할 수 없습니다");
            case "empty" -> assertThat(actual.answer()).contains("질문을 입력");
            case "invalid-order" -> assertThat(actual.answer()).contains("올바른 5자리 주문번호");
            case "multiple-orders" -> assertThat(actual.answer()).contains("주문번호를 한 개만");
            case "too-long" -> assertThat(actual.answer()).contains("입력이 너무 깁니다");
            case "reapprove-denied" -> assertThat(actual.answer()).contains("관리자 API");
            default -> assertThat(actual.answer() + actual.toolsCalled()).contains(golden.expected());
        }
    }

    static Stream<GoldenSet.Case> goldenCases() {
        return GoldenSet.cases().stream();
    }
}
