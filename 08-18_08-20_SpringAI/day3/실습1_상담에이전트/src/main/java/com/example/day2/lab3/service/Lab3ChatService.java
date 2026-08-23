package com.example.day2.lab3.service;

import com.example.day2.lab3.audit.AuditService;
import com.example.day2.lab3.security.SafetyService;
import com.example.day2.lab3.tool.OrderTools;
import com.example.day2.lab3.web.ChatDtos.ChatResponse;
import io.micrometer.core.instrument.MeterRegistry;
import io.micrometer.core.instrument.Timer;
import java.util.List;
import java.util.Map;
import java.util.regex.Matcher;
import java.util.regex.Pattern;
import java.util.concurrent.atomic.AtomicInteger;
import java.util.concurrent.CopyOnWriteArrayList;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.ai.chat.client.ChatClient;
import org.springframework.ai.chat.client.ChatClientResponse;
import org.springframework.ai.chat.client.advisor.vectorstore.QuestionAnswerAdvisor;
import org.springframework.ai.chat.memory.ChatMemory;
import org.springframework.ai.chat.model.ToolContext;
import org.springframework.ai.document.Document;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.beans.factory.annotation.Qualifier;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Service;

@Service
public class Lab3ChatService {
    private static final Logger log = LoggerFactory.getLogger(Lab3ChatService.class);
    private static final Pattern ORDER_ID = Pattern.compile("(?<!\\d)(\\d{5})(?!\\d)");
    private final OrderTools tools;
    private final SafetyService safety;
    private final PolicyRagService rag;
    private final ConversationService conversations;
    private final AuditService audit;
    private final MeterRegistry metrics;
    private final ChatClient liveChat;
    private final boolean liveAiEnabled;

    // 외부 API를 쓰지 않는 단위 테스트용 생성자
    public Lab3ChatService(OrderTools tools, SafetyService safety, PolicyRagService rag,
                           ConversationService conversations, AuditService audit, MeterRegistry metrics) {
        this(tools, safety, rag, conversations, audit, metrics, null, false);
    }

    @Autowired
    public Lab3ChatService(OrderTools tools, SafetyService safety, PolicyRagService rag,
                           ConversationService conversations, AuditService audit, MeterRegistry metrics,
                           @Qualifier("lab3ChatClient") ChatClient liveChat,
                           @Value("${lab3.live-ai-enabled:false}") boolean liveAiEnabled) {
        this.tools = tools; this.safety = safety; this.rag = rag; this.conversations = conversations;
        this.audit = audit; this.metrics = metrics; this.liveChat = liveChat; this.liveAiEnabled = liveAiEnabled;
    }

    public ChatResponse chat(String userId, String sessionId, String question) {
        Timer.Sample sample = Timer.start(metrics);
        try {
            SafetyService.SafetyDecision decision = safety.inspect(question);
            if (!decision.allowed()) {
                audit.record("SAFETY_BLOCKED", userId, question, decision.message());
                return blocked(sessionId, decision.message());
            }
            metrics.counter("ai.tokens", "type", "input", "feature", "lab3").increment(estimateTokens(question));
            String q = question.replaceAll("(?i)나 관리자야[., ]*", "").trim();
            String orderId = extractOrderId(q);
            if (orderId == null && q.matches(".*(그거|그 주문|그럼).*")) orderId = conversations.lastOrderId(userId, sessionId);
            List<String> toolCalls = new CopyOnWriteArrayList<>();
            ToolContext context = toolContext(userId, toolCalls);

            if (q.matches(".*(전부|모든).*환불.*")) {
                return finish(userId, sessionId, question, "환불은 주문별 확인과 담당자 승인이 필요합니다. 주문번호 한 개를 알려 주세요.",
                        List.of(), false, List.of(), null);
            }
            boolean refundIntent = q.matches(".*(환불.*(접수|신청|해 ?줘)|환불로 접수).*" );
            if (refundIntent && orderId == null)
                orderId = conversations.lastOrderId(userId, sessionId);
            if (refundIntent && orderId == null) return clarify(userId, sessionId, question);
            if (orderId == null && q.matches(".*(내 주문|주문 어디|주문 상태).*"))
                return clarify(userId, sessionId, question);

            if (liveAiEnabled && liveChat != null) {
                try {
                    return liveAnswer(userId, sessionId, question, orderId, toolCalls);
                } catch (RuntimeException exception) {
                    log.error("LAB3_GENERATION_FAILURE question={} reason={}", question,
                            exception.getClass().getSimpleName());
                    // 외부 모델 장애 시 아래의 근거 기반 결정적 응답으로 폴백한다.
                }
            }
            if (refundIntent) {
                String answer = tools.requestRefund(orderId, "고객 상담 요청", context);
                return finish(userId, sessionId, question, answer, List.of(), true, List.copyOf(toolCalls), orderId);
            }
            if (orderId != null && q.matches(".*(주문|어디|상태|배송|조회|보여).*")) {
                String answer = tools.getOrder(orderId, context);
                String rememberedOrderId = answer.contains("찾을 수 없습니다") ? null : orderId;
                return finish(userId, sessionId, question, answer, List.of(), true, List.copyOf(toolCalls), rememberedOrderId);
            }
            List<PolicyRagService.PolicyHit> hits = rag.retrieve(q);
            if (hits.isEmpty()) log.warn("LAB3_SEARCH_FAILURE question={} reason=no_document", question);
            if (!hits.isEmpty()) {
                PolicyRagService.PolicyHit hit = hits.getFirst();
                String answer = policyAnswer(q, hit.source());
                return finish(userId, sessionId, question, answer, List.of(hit.source()), true, List.of(), orderId);
            }
            return finish(userId, sessionId, question, "안녕하세요. 주문번호를 알려 주시면 배송 조회나 환불 요청을 도와드릴게요.",
                    List.of(), false, List.of(), orderId);
        } finally {
            sample.stop(metrics.timer("ai.latency", "phase", "model", "feature", "lab3"));
        }
    }

    @SuppressWarnings("unchecked")
    private ChatResponse liveAnswer(String userId, String sessionId, String question, String orderId,
                                    List<String> toolCalls) {
        String conversationId = conversations.conversationId(userId, sessionId);
        ChatClientResponse response = liveChat.prompt()
                .user(question)
                .advisors(spec -> spec.param(ChatMemory.CONVERSATION_ID, conversationId))
                .toolContext(toolContext(userId, toolCalls).getContext())
                .call().chatClientResponse();
        List<Document> retrieved = (List<Document>) response.context()
                .getOrDefault(QuestionAnswerAdvisor.RETRIEVED_DOCUMENTS, List.of());
        List<String> sources = retrieved.stream()
                .map(document -> String.valueOf(document.getMetadata().get("source"))).distinct().toList();
        if (sources.isEmpty()) log.warn("LAB3_SEARCH_FAILURE question={} reason=no_document", question);
        String answer = response.chatResponse().getResult().getOutput().getText();
        return finish(userId, sessionId, question, answer, sources,
                !sources.isEmpty() || !toolCalls.isEmpty(), List.copyOf(toolCalls), orderId);
    }

    private ChatResponse clarify(String userId, String sessionId, String question) {
        return finish(userId, sessionId, question, "확인할 주문번호를 알려 주세요.", List.of(), false, List.of(), null);
    }
    private ChatResponse blocked(String sessionId, String answer) {
        metrics.counter("ai.tokens", "type", "output", "feature", "lab3").increment(estimateTokens(answer));
        return new ChatResponse(answer, List.of(), false, List.of(), sessionId);
    }
    private ToolContext toolContext(String userId, List<String> toolCalls) {
        return new ToolContext(Map.of(
                "userId", userId,
                "toolCallCount", new AtomicInteger(),
                "toolCalls", toolCalls));
    }
    private ChatResponse finish(String userId, String sessionId, String question, String answer,
                                List<String> sources, boolean grounded, List<String> called, String orderId) {
        conversations.add(userId, sessionId, question, answer, orderId);
        metrics.counter("ai.tokens", "type", "output", "feature", "lab3").increment(estimateTokens(answer));
        return new ChatResponse(answer, sources, grounded, called, sessionId);
    }
    private String policyAnswer(String q, String source) {
        if (source.startsWith("return")) return "상품 수령 후 7일 이내에 반품을 신청할 수 있으며, 환불은 담당자 승인 후 처리됩니다.";
        return "결제 완료 후 1~2영업일 안에 출고되며, 출고 후 배송은 보통 1~3영업일이 걸립니다.";
    }
    private String extractOrderId(String q) { Matcher m = ORDER_ID.matcher(q); return m.find() ? m.group(1) : null; }
    private double estimateTokens(String text) { return Math.max(1, Math.ceil(text.length() / 3.0)); }
}
