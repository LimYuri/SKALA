package com.skala.helpdesk.repository;

import java.util.List;
import org.springframework.ai.chat.memory.ChatMemoryRepository;
import org.springframework.ai.chat.messages.AssistantMessage;
import org.springframework.ai.chat.messages.Message;
import org.springframework.ai.chat.messages.MessageType;
import org.springframework.ai.chat.messages.SystemMessage;
import org.springframework.ai.chat.messages.UserMessage;
import org.springframework.jdbc.core.JdbcTemplate;
import org.springframework.stereotype.Repository;
import org.springframework.transaction.annotation.Transactional;

// Spring AI의 ChatMemory가 대화 기록을 DB에 두고 쓸 수 있게 붙인 JDBC 구현체.
// 재시작해도 대화가 안 날아가게 하려는 목적(인메모리 VectorStore랑 다르게 여긴 DB로 감)
@Repository
public class JdbcConversationRepository implements ChatMemoryRepository {
    private final JdbcTemplate jdbc;
    public JdbcConversationRepository(JdbcTemplate jdbc) { this.jdbc = jdbc; }

    @Override public List<String> findConversationIds() {
        return jdbc.queryForList("select distinct conversation_id from helpdesk_chat_memory", String.class);
    }
    @Override public List<Message> findByConversationId(String id) {
        return jdbc.query("select message_type, message_text from helpdesk_chat_memory where conversation_id=? order by seq",
                (rs, row) -> toMessage(rs.getString(1), rs.getString(2)), id);
    }
    @Override @Transactional public void saveAll(String id, List<Message> messages) {
        deleteByConversationId(id);
        long seq = 0;
        for (Message message : messages) {
            // TOOL 메시지(함수 호출 원본 응답)는 굳이 저장 안 함 - 다음 턴 프롬프트에 필요없는 노이즈라서 제외
            if (message.getMessageType() == MessageType.TOOL) continue;
            jdbc.update("insert into helpdesk_chat_memory(conversation_id,seq,message_type,message_text) values(?,?,?,?)",
                    id, seq++, message.getMessageType().name(), message.getText());
        }
    }
    @Override public void deleteByConversationId(String id) {
        jdbc.update("delete from helpdesk_chat_memory where conversation_id=?", id);
    }
    private Message toMessage(String type, String text) {
        return switch (MessageType.valueOf(type)) {
            case USER -> new UserMessage(text);
            case SYSTEM -> new SystemMessage(text);
            default -> new AssistantMessage(text);
        };
    }
}
