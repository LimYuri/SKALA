package com.example.day2.lab2;

import jakarta.validation.constraints.NotBlank;

public record AskRequest(@NotBlank String question, Integer topK, Double threshold) {
}
