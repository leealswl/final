package com.example.backend.domain;

import lombok.Data;

@Data
public class AiChat {
    private Long userIDx;
    private Long projectIDx;
    private String userMessage;
    private String aiResponse;
}
