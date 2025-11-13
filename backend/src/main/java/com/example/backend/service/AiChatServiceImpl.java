package com.example.backend.service;

import java.util.ArrayList;
import java.util.List;

import org.springframework.stereotype.Service;

import com.example.backend.domain.AiChat;

@Service
public class AiChatServiceImpl implements AiChatService {

    // 채팅 히스토리
    private final List<AiChat> chatHistory = new ArrayList<>();

    @Override
    public AiChat processChat(String userMessage) {
    
        AiChat chat = new AiChat();
        chat.setUserMessage(userMessage);  
               
        chat.setAiResponse("사용자 채팅 : " + userMessage);
     
        // 히스토리에 저장 DB 미연결 상태임
        chatHistory.add(chat);
        
        return chat;
    }
    @Override
    public List<AiChat> getChatHistory() {
        return chatHistory;
    }
}
