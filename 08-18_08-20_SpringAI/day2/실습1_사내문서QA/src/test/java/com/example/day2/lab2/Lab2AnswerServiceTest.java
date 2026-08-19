package com.example.day2.lab2;

import static org.assertj.core.api.Assertions.assertThat;
import static org.mockito.Mockito.*;
import java.util.List;
import org.junit.jupiter.api.Test;
import org.springframework.ai.chat.client.ChatClient;

class Lab2AnswerServiceTest {
    @Test
    void 검색결과가_없으면_모델을_호출하지_않는다() {
        Lab2RetrievalService retrieval = mock(Lab2RetrievalService.class);
        ChatClient.Builder builder = mock(ChatClient.Builder.class);
        when(retrieval.retrieveDocuments("우주 배송", null, null)).thenReturn(List.of());

        AnswerDto answer = new Lab2AnswerService(retrieval, builder).ask("우주 배송", null, null);

        assertThat(answer).isEqualTo(AnswerDto.unknown());
        verify(builder).build();
        verifyNoMoreInteractions(builder);
    }
}
