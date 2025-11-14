package com.example.backend.domain;

import lombok.Data;

@Data
public class AiChat {
    private Long userIdx;
    private Long projectIdx;
    private String userMessage;
    private String aiResponse;
}
