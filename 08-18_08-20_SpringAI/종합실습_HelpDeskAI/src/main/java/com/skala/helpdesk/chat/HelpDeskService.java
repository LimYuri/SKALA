package com.skala.helpdesk.chat;

import com.skala.helpdesk.advisor.AuditService;
import com.skala.helpdesk.advisor.SafetyService;
import com.skala.helpdesk.chat.AnswerDto.Source;
import com.skala.helpdesk.config.HelpDeskProperties;
import com.skala.helpdesk.tools.OrderTools;
import com.skala.helpdesk.tools.TicketTools;
import com.skala.helpdesk.tools.ToolRequestContext;
import io.micrometer.core.instrument.MeterRegistry;
import io.micrometer.core.instrument.Timer;
import java.time.Duration;
import java.util.List;
import java.util.Locale;
import java.util.concurrent.CopyOnWriteArrayList;
import java.util.regex.Matcher;
import java.util.regex.Pattern;
import org.springframework.ai.chat.client.ChatClient;
import org.springframework.ai.chat.client.ChatClientResponse;
import org.springframework.ai.chat.client.advisor.vectorstore.QuestionAnswerAdvisor;
import org.springframework.ai.chat.memory.ChatMemory;
import org.springframework.ai.chat.messages.AssistantMessage;
import org.springframework.ai.chat.messages.Message;
import org.springframework.ai.chat.messages.UserMessage;
import org.springframework.ai.document.Document;
import org.springframework.ai.openai.OpenAiChatOptions;
import org.springframework.ai.vectorstore.SearchRequest;
import org.springframework.ai.vectorstore.VectorStore;
import org.springframework.stereotype.Service;
import org.slf4j.MDC;
import reactor.core.publisher.Flux;

// 상담 요청 처리의 중심 서비스. 크게 3단계로 나뉨:
// 1) safety.inspect()로 1차 차단  2) validateEdgeInput()으로 엣지케이스 처리
// 3) 라이브 AI 모드면 live(), 아니면 deterministic()(정규식 기반 규칙 응답)로 분기
@Service
public class HelpDeskService {
    private static final Pattern ORDER_ID = Pattern.compile("(?<!\\d)(\\d{5})(?!\\d)");
    private static final Pattern ANY_NUMBER = Pattern.compile("(?<!\\d)\\d+(?!\\d)");
    private static final Pattern TICKET_ID = Pattern.compile("(?i)HD-\\d+");
    private final ChatClient chat;
    private final ChatMemory memory;
    private final OrderTools orderTools;
    private final TicketTools ticketTools;
    private final SafetyService safety;
    private final AuditService audit;
    private final MeterRegistry meters;
    private final HelpDeskProperties props;
    private final ModelFallbackExecutor fallbackExecutor;
    private final VectorStore vectorStore;
    public HelpDeskService(ChatClient helpDeskClient, ChatMemory memory, OrderTools orderTools,
                           TicketTools ticketTools, SafetyService safety, AuditService audit,
                           MeterRegistry meters, HelpDeskProperties props, ModelFallbackExecutor fallbackExecutor,
                           VectorStore vectorStore) {
        this.chat = helpDeskClient; this.memory = memory; this.orderTools = orderTools; this.ticketTools = ticketTools;
        this.safety = safety; this.audit = audit; this.meters = meters; this.props = props;
        this.fallbackExecutor = fallbackExecutor;
        this.vectorStore = vectorStore;
    }
    public AnswerDto ask(String question, String tenantId, String userId, String sessionId) {
        return askWithTrace(question, tenantId, userId, sessionId, "no-trace");
    }
    public AnswerDto askWithTrace(String question, String tenantId, String userId, String sessionId, String traceId) {
        String previous = MDC.get("traceId");
        MDC.put("traceId", traceId);
        try { return askInternal(question, tenantId, userId, sessionId); }
        finally {
            if (previous == null) MDC.remove("traceId"); else MDC.put("traceId", previous);
        }
    }
    private AnswerDto askInternal(String question, String tenantId, String userId, String sessionId) {
        String conversationId = conversationId(tenantId, userId, sessionId);
        meters.counter("ai.requests", "feature", "helpdesk").increment();
        Timer.Sample timer = Timer.start(meters);
        try {
            // 1차 검사 - 여기서 막히면 모델 호출 자체를 안 함
            SafetyService.Decision decision = safety.inspect(question);
            if (!decision.allowed()) {
                audit.record("SAFETY_BLOCKED", userId, question, decision.message());
                return new AnswerDto(decision.message(), List.of(), false, List.of(), false, conversationId);
            }
            // GoldenSet에 있는 빈 입력/잘못된 주문번호/재승인 시도 같은 케이스는 모델까지 안 가고 여기서 바로 응답
            AnswerDto edgeCase = validateEdgeInput(question, conversationId);
            if (edgeCase != null) return edgeCase;
            if (props.liveAiEnabled()) return live(question, userId, conversationId);
            return deterministic(question, userId, conversationId);
        } finally {
            timer.stop(meters.timer("ai.latency", "phase", "total", "feature", "helpdesk"));
        }
    }
    // 실제 OpenAI 모델을 호출하는 경로. 폴백 처리는 ModelFallbackExecutor한테 위임
    private AnswerDto live(String question, String userId, String conversationId) {
        List<String> calls = new CopyOnWriteArrayList<>();
        ModelFallbackExecutor.Result result;
        try {
            result = fallbackExecutor.execute(userId,
                    props.model().primary(), props.model().fallback(),
                    () -> callModel(question, userId, conversationId, calls, props.model().primary()),
                    () -> callModel(question, userId, conversationId, calls, props.model().fallback()),
                    () -> null);
        } catch (RuntimeException exception) {
            throw exception;
        } catch (Exception exception) {
            throw new IllegalStateException("모델 호출에 실패했습니다.", exception);
        }
        if (result.localUsed()) return deterministic(question, userId, conversationId, true);
        return fromResponse((ChatClientResponse) result.value(), calls,
                result.fallbackUsed(), conversationId);
    }
    private ChatClientResponse callModel(String question, String userId, String conversationId,
                                         List<String> calls, String model) {
        return chat.prompt().user(question)
                .options(OpenAiChatOptions.builder().model(model).build())
                .advisors(a -> a.param(ChatMemory.CONVERSATION_ID, conversationId).param("auditUserId", userId))
                .toolContext(ToolRequestContext.create(userId, calls).getContext())
                .call().chatClientResponse();
    }

    // SSE 스트리밍 경로. Flux는 리액티브라서 ModelFallbackExecutor의 @Retryable을 그대로 쓸 수 없어서
    // 여기는 onErrorResume 체이닝으로 직접 1차->2차->로컬 순서 폴백을 구현함(로직은 동일, 구현 방식만 다름)
    public Flux<String> streamAnswer(String question, String tenantId, String userId,
                                     String sessionId, String traceId) {
        return Flux.defer(() -> {
            String previous = MDC.get("traceId");
            MDC.put("traceId", traceId);
            String conversationId = conversationId(tenantId, userId, sessionId);
            meters.counter("ai.requests", "feature", "helpdesk-stream").increment();
            Timer.Sample timer = Timer.start(meters);

            SafetyService.Decision decision = safety.inspect(question);
            if (!decision.allowed()) {
                audit.record("SAFETY_BLOCKED", userId, question, decision.message());
                restoreTrace(previous);
                timer.stop(meters.timer("ai.latency", "phase", "stream", "feature", "helpdesk"));
                return localTokens(decision.message());
            }

            Flux<String> tokens;
            if (!props.liveAiEnabled()) {
                tokens = localTokens(deterministic(question, userId, conversationId).answer());
            } else {
                List<String> calls = new CopyOnWriteArrayList<>();
                tokens = streamModel(question, userId, conversationId, calls, props.model().primary())
                        .onErrorResume(primaryFailure -> {
                            meters.counter("ai.fallback", "from", props.model().primary(),
                                    "to", props.model().fallback()).increment();
                            audit.record("MODEL_FALLBACK", userId,
                                    props.model().primary(), props.model().fallback());
                            return streamModel(question, userId, conversationId, calls,
                                    props.model().fallback());
                        })
                        .onErrorResume(fallbackFailure -> {
                            audit.record("MODEL_LOCAL_FALLBACK", userId,
                                    fallbackFailure.getClass().getSimpleName(), "deterministic");
                            return localTokens(deterministic(question, userId, conversationId, true).answer());
                        });
            }

            restoreTrace(previous);
            return tokens.filter(token -> token != null && !token.isEmpty())
                    .doFinally(signal -> timer.stop(
                            meters.timer("ai.latency", "phase", "stream", "feature", "helpdesk")));
        });
    }

    private Flux<String> streamModel(String question, String userId, String conversationId,
                                     List<String> calls, String model) {
        return chat.prompt().user(question)
                .options(OpenAiChatOptions.builder().model(model).build())
                .advisors(a -> a.param(ChatMemory.CONVERSATION_ID, conversationId)
                        .param("auditUserId", userId))
                .toolContext(ToolRequestContext.create(userId, calls).getContext())
                .stream().content();
    }

    private Flux<String> localTokens(String answer) {
        return Flux.fromArray(answer.split("(?<=\\s)"))
                .delayElements(Duration.ofMillis(5));
    }

    public List<Source> streamSources(String question) {
        String q = question.toLowerCase(Locale.ROOT);
        if (!props.liveAiEnabled()) {
            if (q.matches(".*(반품|돌려보내|교환 규|환불 규).*") ) {
                return List.of(new Source("return-policy.md", "local-v1"));
            }
            if (q.matches(".*(배송 규|출고).*") ) {
                return List.of(new Source("shipping-policy.md", "local-v1"));
            }
            return List.of();
        }
        return vectorStore.similaritySearch(SearchRequest.builder()
                        .query(question).topK(props.rag().topK())
                        .similarityThreshold(props.rag().threshold()).build()).stream()
                .map(document -> new Source(String.valueOf(document.getMetadata().get("source")),
                        String.valueOf(document.getMetadata().get("version"))))
                .distinct().toList();
    }

    private void restoreTrace(String previous) {
        if (previous == null) MDC.remove("traceId"); else MDC.put("traceId", previous);
    }
    @SuppressWarnings("unchecked")
    private AnswerDto fromResponse(ChatClientResponse response, List<String> calls, boolean fallback,
                                   String conversationId) {
        List<Document> used = (List<Document>) response.context()
                .getOrDefault(QuestionAnswerAdvisor.RETRIEVED_DOCUMENTS, List.of());
        List<Source> sources = used.stream().map(d -> new Source(
                String.valueOf(d.getMetadata().get("source")), String.valueOf(d.getMetadata().get("version"))))
                .distinct().toList();
        return new AnswerDto(response.chatResponse().getResult().getOutput().getText(), sources,
                !calls.isEmpty(), List.copyOf(calls), fallback, conversationId);
    }
    private AnswerDto deterministic(String question, String userId, String conversationId) {
        return deterministic(question, userId, conversationId, false);
    }
    // 라이브 AI 없이(또는 모델이 전부 실패했을 때) 정규식으로 의도를 파악해서 답하는 규칙 기반 응답.
    // API 키 없이도 테스트/데모가 되게 하려고 만든 경로라 순서가 중요함 - 위에서부터 먼저 매칭되는 걸로 처리
    private AnswerDto deterministic(String question, String userId, String conversationId, boolean fallback) {
        String q = question.toLowerCase(Locale.ROOT);
        String orderId = extractOrderId(question);
        if (orderId == null && q.matches(".*(그거|그건|그 주문|내 주문|교환|환불).*")) orderId = lastOrderId(conversationId);
        List<String> calls = new CopyOnWriteArrayList<>();
        var context = ToolRequestContext.create(userId, calls);
        AnswerDto answer;
        if (q.matches(".*(전부|모든).*?(교환|환불).*") ) {
            answer = dto("주문번호 한 건씩 확인한 뒤 승인 대기 티켓으로만 접수할 수 있습니다.", List.of(), calls, fallback, conversationId);
        } else if (q.matches(".*(교환|환불).*(접수|신청|바꿔|해 ?줘).*") ) {
            if (orderId == null) answer = dto("처리할 주문번호를 알려 주세요.", List.of(), calls, fallback, conversationId);
            else {
                String type = q.contains("교환") ? "EXCHANGE" : "REFUND";
                answer = dto(ticketTools.createTicket(orderId, type, "HelpDesk 상담 요청", context),
                        List.of(), calls, fallback, conversationId);
            }
        } else if (orderId != null && q.matches(".*(주문|어디|상태|배송|도착).*") ) {
            answer = dto(orderTools.orderStatus(orderId, context), List.of(), calls, fallback, conversationId);
        } else if (q.matches(".*(반품|돌려보내|교환 규정|환불 규정).*") ) {
            answer = dto("상품 수령 후 7일 이내 반품·교환을 신청할 수 있으며 담당자 승인 후 처리됩니다.",
                    List.of(new Source("return-policy.md", "local-v1")), calls, fallback, conversationId);
        } else if (q.matches(".*(배송 규정|출고).*") ) {
            answer = dto("결제 후 1~2영업일 이내 출고하며 배송에는 보통 1~3영업일이 걸립니다.",
                    List.of(new Source("shipping-policy.md", "local-v1")), calls, fallback, conversationId);
        } else answer = dto("확인할 수 없습니다. 규정 질문 또는 주문번호를 알려 주세요.", List.of(), calls, fallback, conversationId);
        remember(conversationId, question, answer.answer());
        estimateTokens(question, answer.answer());
        return answer;
    }
    // GoldenSet 확장분(엣지케이스 6종) 처리하는 곳. 여기서 걸리면 null이 아니라 바로 응답을 리턴하고,
    // 해당 없으면 null을 리턴해서 askInternal이 원래 흐름(live/deterministic)으로 넘어가게 함
    private AnswerDto validateEdgeInput(String question, String conversationId) {
        String q = question.toLowerCase(Locale.ROOT);
        List<String> orderIds = ORDER_ID.matcher(question).results().map(result -> result.group(1)).toList();
        // 주문번호가 두 개 이상 섞여 들어온 질문(다중 주문 조회 시도)
        if (orderIds.size() > 1) {
            return dto("한 번에 주문번호를 한 개만 입력해 주세요.", List.of(), List.of(), false, conversationId);
        }
        // 00000처럼 형식은 맞지만 존재할 수 없는 주문번호, 혹은 자릿수 안 맞는 번호
        if (q.contains("주문") && (orderIds.contains("00000")
                || (orderIds.isEmpty() && ANY_NUMBER.matcher(question).find()))) {
            return dto("올바른 5자리 주문번호를 입력해 주세요.", List.of(), List.of(), false, conversationId);
        }
        // 이미 승인된 티켓(HD-xxxx)을 다시 승인해달라는 중복 요청
        if (TICKET_ID.matcher(question).find() && q.matches(".*(재승인|다시.*승인|승인.*다시).*")) {
            return dto("승인 완료 티켓은 다시 승인할 수 없습니다. 티켓 승인은 관리자 API에서만 처리합니다.",
                    List.of(), List.of(), false, conversationId);
        }
        return null;
    }
    private AnswerDto dto(String text, List<Source> sources, List<String> calls, boolean fallback, String id) {
        return new AnswerDto(text, sources, !calls.isEmpty(), List.copyOf(calls), fallback, id);
    }
    private void remember(String id, String question, String answer) {
        memory.add(id, List.of(new UserMessage(question), new AssistantMessage(answer)));
    }
    private String lastOrderId(String id) {
        List<Message> messages = memory.get(id);
        for (int i = messages.size() - 1; i >= 0; i--) {
            String found = extractOrderId(messages.get(i).getText());
            if (found != null) return found;
        }
        return null;
    }
    private String extractOrderId(String text) { Matcher m = ORDER_ID.matcher(text); return m.find() ? m.group(1) : null; }
    private void estimateTokens(String input, String output) {
        double total = Math.max(1, Math.ceil(input.length() / 3.0))
                + Math.max(1, Math.ceil(output.length() / 3.0));
        meters.counter("ai.tokens", "type", "prompt", "feature", "helpdesk-local")
                .increment(Math.max(1, Math.ceil(input.length() / 3.0)));
        meters.counter("ai.tokens", "type", "completion", "feature", "helpdesk-local")
                .increment(Math.max(1, Math.ceil(output.length() / 3.0)));
        meters.counter("ai.cost.usd", "feature", "helpdesk-local").increment(total * 0.000001);
    }
    public String conversationId(String tenantId, String userId, String sessionId) {
        return "%s:%s:%s".formatted(tenantId, userId, sessionId);
    }
    public List<Message> history(String tenantId, String userId, String sessionId) {
        return memory.get(conversationId(tenantId, userId, sessionId));
    }
}
