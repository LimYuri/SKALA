package com.example.day2.lab3.web;

import jakarta.validation.constraints.NotBlank;
import java.util.List;

public final class ChatDtos {
    private ChatDtos() {}
    public record ChatRequest(@NotBlank String question, @NotBlank String sessionId) {}
    public record ChatResponse(String answer, List<String> sources, boolean grounded,
                               List<String> toolsCalled, String sessionId) {}
}
