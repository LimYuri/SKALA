package com.example.day2.lab3.security;

import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Service;

@Service
public class SafetyService {
    private final int maxLength;
    public SafetyService(@Value("${lab3.input-max-length:1000}") int maxLength) { this.maxLength = maxLength; }
    public SafetyDecision inspect(String input) {
        if (input == null || input.isBlank()) return new SafetyDecision(false, "질문을 입력해 주세요.");
        if (input.length() > maxLength) return new SafetyDecision(false, "입력이 너무 깁니다. " + maxLength + "자 이하로 줄여 주세요.");
        String q = input.toLowerCase();
        if (q.matches(".*(ignore (all|previous)|system prompt|시스템 프롬프트|이전 지시.*무시|개발자 메시지).*"))
            return new SafetyDecision(false, "보안상 내부 지시나 시스템 프롬프트는 제공할 수 없습니다.");
        if (q.matches(".*(주민등록번호|주민번호).*"))
            return new SafetyDecision(false, "민감한 개인정보는 입력하거나 조회할 수 없습니다.");
        if (q.matches(".*(다른 고객|타인.*주소|고객.*명단|모든 고객).*"))
            return new SafetyDecision(false, "다른 고객의 개인정보는 제공할 수 없습니다.");
        return new SafetyDecision(true, "");
    }
    public record SafetyDecision(boolean allowed, String message) {}
}
