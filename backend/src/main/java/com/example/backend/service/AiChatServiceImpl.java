package com.example.backend.service;

import com.example.backend.domain.AiChat;
import com.example.backend.mapper.AiChatMapper;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.http.*;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;
import org.springframework.web.client.RestTemplate;

import java.util.HashMap;
import java.util.List;
import java.util.Map;

/**
 * AiChatServiceImpl
 *  - FastAPI /chat 호출
 *  - 응답 DB 저장
 *  - 히스토리 DB 조회
 */
@Service
public class AiChatServiceImpl implements AiChatService {

    private static final Logger logger = LoggerFactory.getLogger(AiChatServiceImpl.class);

    @Autowired
    private AiChatMapper aiChatMapper;

    @Autowired
    private RestTemplate restTemplate;

    // FastAPI URL + /chat 경로 포함
    @Value("${fastapi.url}/chat")
    private String fastApiUrl;

    @Override
    @Transactional
    public AiChat processChat(String userMessage, Long userIDx, Long projectIDx) {

        // 1️⃣ FastAPI 요청 바디 생성
        Map<String, Object> requestBody = new HashMap<>();
        requestBody.put("userMessage", userMessage);
        requestBody.put("userIDx", userIDx);
        requestBody.put("projectIDx", projectIDx);

        HttpHeaders headers = new HttpHeaders();
        headers.setContentType(MediaType.APPLICATION_JSON);

        HttpEntity<Map<String, Object>> request = new HttpEntity<>(requestBody, headers);

        // 2️⃣ AiChat 객체 초기화
        AiChat chat = new AiChat();
        chat.setUserIDx(userIDx);
        chat.setProjectIDx(projectIDx);
        chat.setUserMessage(userMessage);

        // 3️⃣ FastAPI 호출
        try {
            ResponseEntity<AiChatResponse> response =
                    restTemplate.postForEntity(fastApiUrl, request, AiChatResponse.class);

            if (response.getBody() != null) {
                chat.setAiResponse(response.getBody().getAiResponse());
                logger.info("FastAPI 응답 성공: {}", chat.getAiResponse());
            } else {
                chat.setAiResponse("FastAPI 응답이 없습니다.");
                logger.warn("FastAPI 응답이 null입니다. userMessage={}", userMessage);
            }

        } catch (Exception e) {
            chat.setAiResponse("FastAPI 호출 실패, 더미 응답입니다.");
            logger.error("FastAPI 호출 실패: {}", e.getMessage(), e);
        }

        // 4️⃣ DB 저장
        try {
            aiChatMapper.insertChat(chat);
        } catch (Exception e) {
            logger.error("DB 저장 실패: {}", e.getMessage(), e);
        }

        // 5️⃣ 최종 반환
        return chat;
    }

    @Override
    public List<AiChat> getChatHistory() {
        try {
            return aiChatMapper.getAllChats();
        } catch (Exception e) {
            logger.error("DB 조회 실패: {}", e.getMessage(), e);
            return List.of();
        }
    }

    /**
     * FastAPI 응답 DTO
     *  FastAPI에서 반환하는 JSON 구조: { "userMessage": "...", "aiResponse": "..." }
     */
    public static class AiChatResponse {
        private String userMessage;
        private String aiResponse;

        public String getUserMessage() { return userMessage; }
        public void setUserMessage(String userMessage) { this.userMessage = userMessage; }

        public String getAiResponse() { return aiResponse; }
        public void setAiResponse(String aiResponse) { this.aiResponse = aiResponse; }
    }
}