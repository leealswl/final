package com.example.backend.FastAPI;

import java.util.List;
import java.util.Map;

import org.springframework.core.io.InputStreamResource;
import org.springframework.http.client.MultipartBodyBuilder;
import org.springframework.stereotype.Service;
import org.springframework.web.multipart.MultipartFile;
import org.springframework.web.reactive.function.client.WebClient;

import reactor.core.publisher.Mono;

import org.springframework.http.MediaType;

@Service
public class FastAPIService {

    private final WebClient webClient = WebClient.create("http://localhost:8001");

    public String CallFastApiWithAnalsys() {

        return "test";
    }

    public Map<String, Object> sendFilesToFastAPI(List<MultipartFile> files, List<Long> folders, String userId) {
        try {
            MultipartBodyBuilder builder = new MultipartBodyBuilder();

            for (int i = 0; i < files.size(); i++) {
                MultipartFile file = files.get(i);
                String folder = folders.get(i).toString();

                builder.part("files", new InputStreamResource(file.getInputStream()))
                        .filename(file.getOriginalFilename())
                        .contentType(MediaType.APPLICATION_OCTET_STREAM);

                builder.part("folders", folder);
            }

            builder.part("userId", userId);

            // Map으로 JSON 응답 받기
            Mono<Map> response = webClient.post()
                    .uri("/analyze")
                    .contentType(MediaType.MULTIPART_FORM_DATA)
                    .bodyValue(builder.build())
                    .retrieve()
                    .bodyToMono(Map.class);

            // 동기 호출
            return response.block();
        } catch (Exception e) {
            e.printStackTrace();
            return null;
        }
    }
    
}
