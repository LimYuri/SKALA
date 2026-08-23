package com.skala.helpdesk.config;

import com.skala.helpdesk.advisor.AuditAdvisor;
import com.skala.helpdesk.advisor.AuditService;
import com.skala.helpdesk.advisor.SafeGuardAdvisor;
import com.skala.helpdesk.advisor.TokenMeterAdvisor;
import com.skala.helpdesk.repository.JdbcConversationRepository;
import com.skala.helpdesk.tools.OrderTools;
import com.skala.helpdesk.tools.TicketTools;
import io.micrometer.core.instrument.MeterRegistry;
import java.nio.charset.StandardCharsets;
import java.util.List;
import org.springframework.ai.chat.client.ChatClient;
import org.springframework.ai.chat.client.advisor.MessageChatMemoryAdvisor;
import org.springframework.ai.chat.client.advisor.api.Advisor;
import org.springframework.ai.chat.client.advisor.vectorstore.QuestionAnswerAdvisor;
import org.springframework.ai.chat.memory.ChatMemory;
import org.springframework.ai.chat.memory.MessageWindowChatMemory;
import org.springframework.ai.embedding.EmbeddingModel;
import org.springframework.ai.vectorstore.SearchRequest;
import org.springframework.ai.vectorstore.SimpleVectorStore;
import org.springframework.ai.vectorstore.VectorStore;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.context.annotation.Profile;
import org.springframework.core.io.ClassPathResource;

@Configuration
public class AiConfig {
    // 기본은 인메모리 SimpleVectorStore. pgvector 프로필일 때만 PgVectorConfig 쪽 빈으로 교체됨
    @Bean
    @Profile("!pgvector")
    public VectorStore vectorStore(EmbeddingModel embeddingModel) {
        return SimpleVectorStore.builder(embeddingModel).build();
    }
    @Bean public ChatMemory chatMemory(JdbcConversationRepository repository, HelpDeskProperties props) {
        return MessageWindowChatMemory.builder().chatMemoryRepository(repository)
                .maxMessages(props.memory().maxMessages()).build();
    }
    // Advisor 체인 순서가 핵심 요구사항: 감사(0) -> 토큰/비용 계측(50) -> 안전장치(100) -> 대화메모리(200) -> RAG(300)
    // 순서를 안 지키면 예를 들어 차단된 요청까지 토큰이 집계되거나, 메모리에 쌓이기 전에 RAG가 붙는 등 앞뒤가 꼬임
    @Bean public List<Advisor> helpDeskAdvisors(AuditService audit, MeterRegistry meters, ChatMemory memory,
                                         VectorStore vectorStore, HelpDeskProperties props) {
        return List.of(
                new AuditAdvisor(audit),
                new TokenMeterAdvisor(meters),
                new SafeGuardAdvisor(),
                MessageChatMemoryAdvisor.builder(memory).order(200).build(),
                QuestionAnswerAdvisor.builder(vectorStore)
                        .searchRequest(SearchRequest.builder().topK(props.rag().topK())
                                .similarityThreshold(props.rag().threshold()).build())
                        .order(300).build());
    }
    // 시스템 프롬프트는 리소스 파일로 분리해서 관리(prompts/system.st), 여기서는 조립만 담당
    @Bean public ChatClient helpDeskClient(ChatClient.Builder builder, List<Advisor> helpDeskAdvisors,
                                    OrderTools orderTools, TicketTools ticketTools) throws Exception {
        String systemPrompt = new ClassPathResource("prompts/system.st")
                .getContentAsString(StandardCharsets.UTF_8);
        return builder.defaultSystem(systemPrompt).defaultAdvisors(helpDeskAdvisors)
                .defaultTools(orderTools, ticketTools).build();
    }
}
