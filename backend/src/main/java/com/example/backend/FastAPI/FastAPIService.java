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

import reactor.core.publisher.Mono;
import reactor.netty.http.client.HttpClient;

/**
 * FastAPI 서버와의 통신을 담당하는 서비스
 * - 파일을 FastAPI로 전송하여 AI 기반 문서 분석 수행
 * - WebClient를 사용한 비동기 HTTP 통신
 */
@Service
public class FastAPIService {

    private final WebClient webClient;
    private final String analyzePath;

    /**
     * FastAPI 클라이언트 초기화
     * @param baseUrl FastAPI 서버 주소 (기본값: http://localhost:8001)
     * @param analyzePath 분석 API 경로 (기본값: /analyze)
     * @param timeoutSeconds 타임아웃 설정 (기본값: 60초)
     */
    public FastAPIService(
        @Value("${fastapi.base-url:http://localhost:8001}") String baseUrl,
        @Value("${fastapi.path:/analyze}") String analyzePath,
        @Value("${fastapi.timeout-seconds:300}") long timeoutSeconds
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

    /**
     * 파일들을 FastAPI 서버로 전송하여 분석 요청
     *
     * @param files 업로드된 파일 목록
     * @param folders 각 파일이 속한 폴더 ID 목록
     * @param userid 사용자 ID
     * @param projectidx 프로젝트 ID
     * @return FastAPI 분석 결과 (status, message, data 등)
     * @throws IOException 파일 읽기 실패 시
     *
     * 동작 흐름:
     * 1. MultipartBodyBuilder로 폼 데이터 구성 (files, folders, userid, projectidx)
     * 2. FastAPI 서버로 POST 요청 전송
     * 3. FastAPI는 파일을 분석하고 결과를 반환
     */
    public Map<String, Object> sendFilesToFastAPI(
        List<MultipartFile> files, List<Long> folders, String userid, Long projectidx
    ) throws IOException {
        System.out.println("fastapi 작동 시작");

        // Multipart 폼 데이터 생성
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
            // FastAPI 서버로 POST 요청 전송
            Map<String, Object> result = webClient.post()
                .uri(analyzePath) // 예: /analyze
                .contentType(MediaType.MULTIPART_FORM_DATA)
                .body(BodyInserters.fromMultipartData(builder.build()))
                .retrieve()
                .bodyToMono(new ParameterizedTypeReference<Map<String, Object>>() {})
                .block(); // WebClient 생성 시 설정한 timeoutSeconds를 그대로 사용

            System.out.println("fastapi 작동 완료");
            return result;
        } catch (Exception e) {
            // 여기서 예외를 그대로 던지면 컨트롤러가 500. 경고로 처리하고 컨트롤러에서 OK로 내려도 됨.
            // FastAPI 연동 실패 시 예외를 던져 컨트롤러에서 적절한 에러 응답 처리
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
// 챗봇메세지 호출 - fastapi 연동
    public AiChat ChatbotMessage(String message) {

        System.out.println("fastapi 호출 성공");
        
        Mono<AiChat> response = webClient.post().uri("/chat").bodyValue(Map.of("userMessage", message)).retrieve().bodyToMono(AiChat.class);
        System.out.println("agent 송신 후");
        System.out.println(response);
        AiChat result = response.block();
        System.out.println("agent 송신 후123123");
        return result;
        
    }
}
