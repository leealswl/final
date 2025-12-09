package com.example.backend.FastAPI;

import java.io.IOException;
import java.time.Duration;
import java.util.List;
import java.util.Map;

import org.springframework.beans.factory.annotation.Value;
import org.springframework.core.ParameterizedTypeReference;
import org.springframework.core.io.ByteArrayResource;
import org.springframework.http.MediaType;
import org.springframework.http.client.MultipartBodyBuilder;
import org.springframework.http.client.reactive.ReactorClientHttpConnector;
import org.springframework.stereotype.Service;
import org.springframework.web.multipart.MultipartFile;
import org.springframework.web.reactive.function.BodyInserters;
import org.springframework.web.reactive.function.client.WebClient;

import com.example.backend.domain.AiChat;
import com.example.backend.domain.Verify;

import reactor.core.publisher.Mono;
import reactor.netty.http.client.HttpClient;

/**
 * FastAPI 서버와의 통신을 담당하는 서비스
 * - 파일을 FastAPI로 전송하여 AI 기반 문서 분석 수행
 * - 챗봇 메시지를 FastAPI로 전달하고 메시지 내용에 따라 LangGraph로 라우팅
 * - WebClient를 사용한 비동기 HTTP 통신
 */
@Service
public class FastAPIService {

    private final WebClient webClient;
    private final String analyzePath;
    
    // 💡 수정/추가: LangGraph 최초 호출 경로 및 재개 호출 경로 정의
    private final String generatePath = "/generate"; 
    private final String resumePath = "/resume_generation"; // LangGraph 실행 재개 엔드포인트

    /**
     * FastAPI 클라이언트 초기화
     */
    public FastAPIService(
        @Value("${fastapi.base-url:http://localhost:8001}") String baseUrl,
        @Value("${fastapi.path:/analyze}") String analyzePath,
        @Value("${fastapi.timeout-seconds:3000}") long timeoutSeconds
    ) {
        this.analyzePath = analyzePath;
        // WebClient 설정: 타임아웃, 메모리 버퍼 크기 등
        this.webClient = WebClient.builder()
            .baseUrl(baseUrl)
            .clientConnector(new ReactorClientHttpConnector(
                HttpClient.create()
                    .responseTimeout(Duration.ofSeconds(timeoutSeconds))  // 응답 타임아웃
                    .option(io.netty.channel.ChannelOption.CONNECT_TIMEOUT_MILLIS, (int)(timeoutSeconds * 1000))  // 연결 타임아웃
                    .doOnConnected(conn -> conn
                        .addHandlerLast(new io.netty.handler.timeout.ReadTimeoutHandler(timeoutSeconds, java.util.concurrent.TimeUnit.SECONDS))  // Read 타임아웃
                        .addHandlerLast(new io.netty.handler.timeout.WriteTimeoutHandler(timeoutSeconds, java.util.concurrent.TimeUnit.SECONDS))  // Write 타임아웃
                    )
            ))
            .codecs(c -> c.defaultCodecs().maxInMemorySize(50 * 1024 * 1024)) // 50MB 버퍼
            .build();
    }

    public Map<String, Object> verifyLaw(Verify verify){

        Map<String, Object> requestBody = Map.of(
                "text", verify.getText(), 
                "focus", verify.getFocus()
            );

        try {
            System.out.println("fastapi 보내기 전");
            Map<String, Object> result = webClient.post()
                .uri("/verify/law")
                .bodyValue(requestBody)
                .retrieve()
                .bodyToMono(new ParameterizedTypeReference<Map<String, Object>>() {})
                .block(); 

            System.out.println("fastapi 작동 완료");
            return result;
        } catch (Exception e) {
            System.err.println("[FastAPI] 연동 실패: " + e.getMessage());
            throw e;
        }

    }

    /**
     * 파일들을 FastAPI 서버로 전송하여 분석 요청 (변경 없음)
     */
    public Map<String, Object> sendFilesToFastAPI(
        List<MultipartFile> files, List<Long> folders, String userid, Long projectidx
    ) throws IOException {
        System.out.println("fastapi 작동 시작");

        MultipartBodyBuilder builder = new MultipartBodyBuilder();
        
        // 파일과 폴더 정보를 하나씩 multipart body에 추가
        for (int i = 0; i < files.size(); i++) {
            MultipartFile f = files.get(i);
            String folder = folders.get(i).toString();

            // 파일 파트 (filename 보장)
            // ByteArrayResource로 파일 데이터를 변환하며 원본 파일명 유지
            ByteArrayResource resource = new ByteArrayResource(f.getBytes()) {
                @Override
                public String getFilename() {
                    return f.getOriginalFilename();
                }
            };

            // files 파트: 파일 데이터와 메타정보 (파일명, Content-Type) 추가
            builder.part("files", resource)
                   .filename(f.getOriginalFilename())
                   .contentType(MediaType.parseMediaType(
                       f.getContentType() != null ? f.getContentType() : "application/octet-stream"
                   ));

            // folders는 파일 개수만큼 반복
            // 각 파일이 어느 폴더에 속하는지 정보 추가
            builder.part("folders", folder);
        }

        // ✅ 키 이름 꼭 'userid' (소문자)로 맞추기
        // FastAPI 측에서 사용자별 분석 결과 관리에 사용
        // 데이터들 추가가 다 이루어짐.
        builder.part("userid", userid);

        // ✅ 프로젝트 ID 추가 (FastAPI 필수 파라미터)
        builder.part("projectidx", projectidx.toString());



        try {
            System.out.println("fastapi 보내기 전");
            Map<String, Object> result = webClient.post()
                .uri(analyzePath)
                .contentType(MediaType.MULTIPART_FORM_DATA)
                .body(BodyInserters.fromMultipartData(builder.build()))
                .retrieve()
                .bodyToMono(new ParameterizedTypeReference<Map<String, Object>>() {})
                .block(); 

            System.out.println("fastapi 작동 완료");
            return result;
        } catch (Exception e) {
            System.err.println("[FastAPI] 연동 실패: " + e.getMessage());
            throw e;
        }
    }

    /**
     * FastAPI 헬스체크용 메서드 (추후 구현 예정)
     */
    public String CallFastApiWithAnalsys() {
        return "test";
    }

    /**
     * 챗봇 메시지를 FastAPI로 전달하고, 메시지 내용과 threadId에 따라 LangGraph 생성 또는 재개로 라우팅합니다.
     * 💡 [필수 수정] 인자 4개로 변경하여 threadId를 받습니다.
     * * @param message 사용자 메시지
     * @param userIdx 사용자 ID
     * @param projectIdx 프로젝트 ID
     * @param threadId LangGraph 세션 ID (재개 요청 시 필수)
     * @return FastAPI 응답 (AiChat 객체)
     */
    public AiChat ChatbotMessage(String message, String userIdx, Long projectIdx, String userId, String threadId) {

        System.out.println("message: "+ message);
        System.out.println("userIdx: "+ userIdx);
        System.out.println("projectIdx: "+ projectIdx);
        System.out.println("userId: "+ userId);
        System.out.println("threadId (현재 세션 ID): "+ threadId); // 💡 세션 ID 확인

        // 1. 의도 분류 (Dispatcher)
        // List<String> generationKeywords = List.of("기획서", "만들어줘", "써줘", "생성");
        // boolean isGenerationRequest = generationKeywords.stream().anyMatch(message::contains);
        
        // 2. 호출할 엔드포인트 결정 및 요청 바디 구성
        String endpointPath;
        Map<String, Object> requestBody;

        endpointPath = this.generatePath; 
            System.out.println("➡️ 자바 백엔드 라우팅: 기획서 생성 최초 요청 -> " + endpointPath);

            // 💡 [ChatRequest 모델]에 맞게 요청 바디 구성
            requestBody = Map.of(
                "userMessage", message, 
                "userIdx", userIdx, 
                "projectIdx", projectIdx,
                "userId", userId,
                "threadId", threadId
            );

        
        
        // 💡 LangGraph 멀티턴 라우팅 로직 (핵심)
        // if (threadId != null && !threadId.isEmpty()) {
        //     // 턴 2 이상: 이전 세션이 존재하면 무조건 재개 요청 (사용자 답변)
        //     endpointPath = this.resumePath; 
        //     System.out.println("➡️ 자바 백엔드 라우팅: LangGraph 재개 요청 -> " + endpointPath);
            
        //     // 💡 [ResumeRequest 모델]에 맞게 요청 바디 구성
        //     requestBody = Map.of(
        //         "thread_id", threadId,
        //         "userMessage", message, 
        //         "userIdx", userIdx, 
        //         "projectIdx", projectIdx 
        //     );

        // } else if (isGenerationRequest) {
        //     // 턴 1: 기획서 생성 키워드가 있고 세션이 없으면 최초 실행
        //     endpointPath = this.generatePath; 
        //     System.out.println("➡️ 자바 백엔드 라우팅: 기획서 생성 최초 요청 -> " + endpointPath);

        //     // 💡 [ChatRequest 모델]에 맞게 요청 바디 구성
        //     requestBody = Map.of(
        //         "userMessage", message, 
        //         "userIdx", userIdx, 
        //         "projectIdx", projectIdx 
        //     );

        // } else {
        //     // 일반 Chat
        //     endpointPath = "/chat"; 
        //     System.out.println("➡️ 자바 백엔드 라우팅: 일반 Chat 요청 -> " + endpointPath);

        //     // 💡 [ChatRequest 모델]에 맞게 요청 바디 구성
        //     requestBody = Map.of(
        //         "userMessage", message, 
        //         "userIdx", userIdx, 
        //         "projectIdx", projectIdx 
        //     );
        // }

        try {
            // 4. WebClient를 사용하여 FastAPI 호출
            Mono<AiChat> response = webClient.post()
                .uri(endpointPath)
                .bodyValue(requestBody) // 구성된 바디를 전송
                .retrieve()
                .bodyToMono(AiChat.class);

            AiChat result = response.block();
            System.out.println("✅ FastAPI 응답 수신 완료");
            
            // 🔍 [디버깅] FastAPI Raw Response 확인
            System.out.println("🔍 [디버깅] FastAPI Raw Response - aiResponse: " + (result != null ? result.getAiResponse() : "null"));
            System.out.println("🔍 [디버깅] FastAPI Raw Response - message: " + (result != null ? result.getMessage() : "null"));
            System.out.println("🔍 [디버깅] FastAPI Raw Response - completedContent: " + (result != null ? result.getCompletedContent() : "null"));
            System.out.println("🔍 [디버깅] FastAPI Raw Response - generatedContent: " + (result != null ? result.getGeneratedContent() : "null"));
            System.out.println("🔍 [디버깅] FastAPI Raw Response - status: " + (result != null ? result.getStatus() : "null"));
            System.out.println("🔍 [디버깅] FastAPI Raw Response - threadId: " + (result != null ? result.getThreadId() : "null"));
            
            // 💡 중요: 호출하는 서비스(예: AiChatServiceImpl)는 이 AiChat 객체에서 
            // threadId와 status 필드를 확인하고 관리해야 합니다.
            return result;
        } catch (Exception e) {
            System.err.println("❌ FastAPI 호출 실패 (" + endpointPath + "): " + e.getMessage());
            throw new RuntimeException("FastAPI 호출 중 오류 발생: " + e.getMessage(), e);
        }
    }


    /**
     * FastAPI에서 분석된 목차(TOC) 데이터를 가져옴 (변경 없음)
     */
    public Map<String, Object> getTocData(Long projectIdx) {
        // ... (기존 로직 유지) ...
        try {
            System.out.println("📚 FastAPI에서 목차 데이터 요청: projectIdx=" + projectIdx);
            
            Map<String, Object> result = webClient.get()
                .uri(uriBuilder -> uriBuilder
                    .path("/toc")
                    .queryParam("projectidx", projectIdx)
                    .build())
                .retrieve()
                .bodyToMono(new ParameterizedTypeReference<Map<String, Object>>() {})
                .block();
            
            System.out.println("✅ 목차 데이터 수신 완료");
            return result;
        } catch (Exception e) {
            System.err.println("❌ 목차 데이터 가져오기 실패: " + e.getMessage());
            throw e;
        }
    }
}