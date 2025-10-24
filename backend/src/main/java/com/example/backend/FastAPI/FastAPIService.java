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

import reactor.netty.http.client.HttpClient;

@Service
public class FastAPIService {

    private final WebClient webClient;
    private final String analyzePath;

    public FastAPIService(
        @Value("${fastapi.base-url:http://localhost:8001}") String baseUrl,
        @Value("${fastapi.path:/analyze}") String analyzePath,
        @Value("${fastapi.timeout-seconds:60}") long timeoutSeconds
    ) {
        this.analyzePath = analyzePath;
        this.webClient = WebClient.builder()
            .baseUrl(baseUrl)
            .clientConnector(new ReactorClientHttpConnector(
                HttpClient.create().responseTimeout(Duration.ofSeconds(timeoutSeconds))
            ))
            .codecs(c -> c.defaultCodecs().maxInMemorySize(50 * 1024 * 1024)) // 50MB
            .build();
    }

    public Map<String, Object> sendFilesToFastAPI(
        List<MultipartFile> files, List<Long> folders, String userid
    ) throws IOException {
        System.out.println("fastapi 작동 시작");

        MultipartBodyBuilder builder = new MultipartBodyBuilder();

        for (int i = 0; i < files.size(); i++) {
            MultipartFile f = files.get(i);
            String folder = folders.get(i).toString();

            // 파일 파트 (filename 보장)
            ByteArrayResource resource = new ByteArrayResource(f.getBytes()) {
                @Override
                public String getFilename() {
                    return f.getOriginalFilename();
                }
            };

            builder.part("files", resource)
                   .filename(f.getOriginalFilename())
                   .contentType(MediaType.parseMediaType(
                       f.getContentType() != null ? f.getContentType() : "application/octet-stream"
                   ));

            // folders는 파일 개수만큼 반복
            builder.part("folders", folder);
        }

        // ✅ 키 이름 꼭 'userid' (소문자)로 맞추기
        builder.part("userid", userid);

        try {
            Map<String, Object> result = webClient.post()
                .uri(analyzePath) // 예: /analyze
                .contentType(MediaType.MULTIPART_FORM_DATA)
                .body(BodyInserters.fromMultipartData(builder.build()))
                .retrieve()
                .bodyToMono(new ParameterizedTypeReference<Map<String, Object>>() {})
                .block(Duration.ofSeconds(60));

            System.out.println("fastapi 작동 완료");
            return result;
        } catch (Exception e) {
            // 여기서 예외를 그대로 던지면 컨트롤러가 500. 경고로 처리하고 컨트롤러에서 OK로 내려도 됨.
            System.err.println("[FastAPI] 연동 실패: " + e.getMessage());
            throw e;
        }
    }

    // 필요 시 간단 헬스체크
    public String CallFastApiWithAnalsys() {
        return "test";
    }
}
