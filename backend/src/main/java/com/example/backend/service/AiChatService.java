package com.example.backend.service;

import java.util.List;

import com.example.backend.domain.AiChat;

public interface AiChatService {

    AiChat processChat(String userMessage, Long userIDx, Long projectIDx);
    // 사용자가 받은 메시지 처리하고 ai응답 반환

    List<AiChat> getChatHistory();
    // 채팅기록 조회
} 
