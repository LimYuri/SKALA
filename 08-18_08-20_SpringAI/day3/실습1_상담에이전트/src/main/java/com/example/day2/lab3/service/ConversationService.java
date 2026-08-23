package com.example.day2.lab3.service;

import java.util.List;
import java.util.Map;
import java.util.concurrent.ConcurrentHashMap;
import java.util.concurrent.CopyOnWriteArrayList;
import org.springframework.stereotype.Service;

@Service
public class ConversationService {
    private final Map<String, List<Turn>> history = new ConcurrentHashMap<>();
    public String conversationId(String userId, String sessionId) { return userId + ":" + sessionId; }
    public void add(String userId, String sessionId, String question, String answer, String orderId) {
        history.computeIfAbsent(conversationId(userId, sessionId), k -> new CopyOnWriteArrayList<>())
                .add(new Turn(question, answer, orderId));
    }
    public List<Turn> history(String userId, String sessionId) {
        return List.copyOf(history.getOrDefault(conversationId(userId, sessionId), List.of()));
    }
    public String lastOrderId(String userId, String sessionId) {
        List<Turn> turns = history(userId, sessionId);
        for (int i = turns.size() - 1; i >= 0; i--) if (turns.get(i).orderId() != null) return turns.get(i).orderId();
        return null;
    }
    public record Turn(String question, String answer, String orderId) {}
}
