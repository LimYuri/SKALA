package com.skala.helpdesk.chat;

import java.util.List;

// 응답 본문 외에 프론트/테스트에서 확인할 부가 정보(출처 문서, 툴 호출 여부, 폴백 여부)까지 같이 내려줌
public record AnswerDto(String answer, List<Source> sources, boolean toolUsed,
                        List<String> toolsCalled, boolean fallbackUsed, String conversationId) {
    public record Source(String document, String version) {}
}
