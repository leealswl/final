package com.example.backend.controller;

import java.util.List;

import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RestController;

import com.example.backend.domain.AiChat;
import com.example.backend.service.AiChatService;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.GetMapping;




@RestController
@RequestMapping("/ai-chat")
public class AiChatController {

    private final AiChatService aiChatService;

    @Autowired
    public AiChatController(AiChatService aiChatService){
        this.aiChatService = aiChatService;
    }

    // 응답처리 - 사용자 채팅
    @PostMapping("/response")
    public AiChat sendMesaage(@RequestBody String userMessage){
        return aiChatService.processChat(userMessage);
    }

    @GetMapping("/history")
    public List<AiChat> getChatHistory(){
        return aiChatService.getChatHistory();
    }
}
    

    
    
