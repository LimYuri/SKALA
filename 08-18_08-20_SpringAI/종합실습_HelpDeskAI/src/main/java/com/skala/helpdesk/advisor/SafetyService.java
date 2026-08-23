package com.skala.helpdesk.advisor;

import com.skala.helpdesk.config.HelpDeskProperties;
import org.springframework.stereotype.Service;

// HelpDeskService.askInternal()에서 제일 먼저 호출되는 1차 검사.
// 여기서 걸리면 모델 호출 자체를 안 하니까 토큰/비용도 안 나감
@Service
public class SafetyService {
    private final int maxChars;
    public SafetyService(HelpDeskProperties props) { this.maxChars = props.safety().maxInputChars(); }
    public Decision inspect(String input) {
        if (input == null || input.isBlank()) return new Decision(false, "질문을 입력해 주세요.");
        if (input.length() > maxChars) return new Decision(false, "입력이 너무 깁니다. 길이 제한 내로 줄여 주세요.");
        String q = input.toLowerCase();
        if (q.matches(".*(이전 지시.*무시|system prompt|시스템 프롬프트|개발자 메시지).*"))
            return new Decision(false, "내부 지시와 시스템 프롬프트는 제공할 수 없습니다.");
        if (q.matches(".*(주민등록번호|주민번호|카드번호|다른 고객|고객 명단).*"))
            return new Decision(false, "민감정보나 다른 고객 정보는 처리할 수 없습니다.");
        return new Decision(true, "");
    }
    public record Decision(boolean allowed, String message) {}
}
