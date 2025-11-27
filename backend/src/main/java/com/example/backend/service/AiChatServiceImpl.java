package com.example.backend.service;

import com.example.backend.domain.AiChat;
import com.example.backend.mapper.AiChatMapper;
import com.example.backend.FastAPI.FastAPIService;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.util.List;

/**
 * AiChatServiceImpl
 * - FastAPI 호출 위임 (FastAPIService 이용, LangGraph 라우팅 포함)
 * - 응답 DB 저장
 * - 히스토리 DB 조회
 */
@Service
public class AiChatServiceImpl implements AiChatService {

    private static final Logger logger = LoggerFactory.getLogger(AiChatServiceImpl.class);

    @Autowired
    private AiChatMapper aiChatMapper;

    // WebClient 기반의 FastAPIService 주입
    @Autowired
    private FastAPIService fastAPIService;

    @Override
    @Transactional
    public AiChat processChat(String userMessage, Long userIdx, Long projectIdx, String userId) {

        System.out.println("userMessage: " + userMessage);
        System.out.println("userIdx: " + userIdx);
        System.out.println("projectIdx: " + projectIdx);
        System.out.println("userId: " + userId);

        // 1️⃣ AiChat 객체 초기화 (DB 저장을 위해)
        AiChat chat = new AiChat();
        chat.setUserIdx(userIdx);
        chat.setProjectIdx(projectIdx);
        chat.setUserMessage(userMessage);
        chat.setUserId(userId);

        System.out.println("chat: " + chat);


        // 2️⃣ FastAPIService를 통한 LangGraph/Chat 라우팅 호출
        AiChat fastApiResponse;
        try {
            
            // 💡 [수정된 부분 A: threadId 처리] 💡
            // (실제 서비스에서는 projectIdx나 userIdx에 연결된 활성 threadId를 DB나 세션에서 조회해야 합니다.)
            String activeThreadId = null; 

            // 🔑 [수정된 부분 B: 메서드 시그니처 맞춤] 🔑
            fastApiResponse = fastAPIService.ChatbotMessage(
                userMessage, 
                userIdx.toString(), // Long을 String으로 변환하여 전달
                projectIdx,
                userId,
                activeThreadId // 🚨 필수 수정: 네 번째 인자(threadId)로 null 전달
            );

            System.out.println("fastApiResponse: " + fastApiResponse);

            // 💡 LangGraph 또는 Chatbot 응답을 최종 응답 필드에 매핑
            if (fastApiResponse != null) {
                
                // 🔑 [핵심 수정]: LangGraph의 질문(message)을 최우선으로 사용하여 화면 출력 문제를 해결합니다.
                String finalResponse = fastApiResponse.getMessage() != null
                    ? fastApiResponse.getMessage() // 1. LangGraph의 질문/상태 메시지
                    : (fastApiResponse.getGeneratedContent() != null
                        ? fastApiResponse.getGeneratedContent() // 2. 최종 기획서 초안 내용
                        : fastApiResponse.getAiResponse()); // 3. 일반 챗봇 응답
                
                chat.setAiResponse(finalResponse);
                
                // 💡 [수정된 부분 C: LangGraph 상태 필드 매핑] 💡
                // FastAPI에서 반환된 threadId, status, message 등을 AiChat 객체에 매핑합니다.
                chat.setGeneratedContent(fastApiResponse.getGeneratedContent());
                chat.setFullProcessResult(fastApiResponse.getFullProcessResult());
                
                // 🔑 추가 매핑: 멀티턴 실행을 위한 상태 관리
                chat.setThreadId(fastApiResponse.getThreadId()); 
                chat.setStatus(fastApiResponse.getStatus());
                chat.setMessage(fastApiResponse.getMessage()); // ⬅️ NEW: message 필드도 명시적으로 매핑
                
                // 🔑 ProseMirror JSON 형식의 완성된 콘텐츠 매핑 (에디터용)
                chat.setCompletedContent(fastApiResponse.getCompletedContent());
                
                // 🔍 [디버깅] completedContent 설정 확인
                logger.info("🔍 [디버깅] FastAPI에서 받은 completedContent: {}", 
                            fastApiResponse.getCompletedContent() != null ? "존재함" : "null");
                logger.info("🔍 [디버깅] chat 객체에 설정된 completedContent: {}", 
                            chat.getCompletedContent() != null ? "존재함" : "null");

                logger.info("FastAPI 응답 성공 (Type: {}): {}", 
                            fastApiResponse.getGeneratedContent() != null ? "LangGraph Draft" : (fastApiResponse.getMessage() != null ? "LangGraph Query" : "Chat"),
                            finalResponse);
                if (fastApiResponse.getCompletedContent() != null) {
                    logger.info("✅ completedContent 포함됨 (ProseMirror JSON)");
                } else {
                    logger.warn("⚠️ completedContent가 null입니다. generate_draft 노드가 실행되지 않았을 수 있습니다.");
                }
            } else {
                chat.setAiResponse("FastAPI 응답이 없습니다.");
                logger.warn("FastAPI 응답이 null입니다. userMessage={}", userMessage);
            }

        } catch (Exception e) {
            String errorMsg = "⚠️ FastAPI 호출 실패: " + e.getMessage();
            chat.setAiResponse(errorMsg);
            logger.error("FastAPI 호출 실패 - userMessage: {}, error: {}", userMessage, e.getMessage(), e);
        }

        // // 3️⃣ DB 저장 (주석 처리됨)
        // ...

        // 4️⃣ 최종 반환
        // 🔍 [디버깅] 최종 반환 전 completedContent 확인
        logger.info("🔍 [디버깅] 최종 반환 전 chat.completedContent: {}", 
                    chat.getCompletedContent() != null ? "존재함" : "null");
        logger.info("🔍 [디버깅] 최종 반환 전 chat.aiResponse: {}", chat.getAiResponse());
        logger.info("🔍 [디버깅] 최종 반환 전 chat.message: {}", chat.getMessage());
        
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
}