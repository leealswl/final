package com.example.backend.controller;

import java.io.IOException;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.Paths;
import java.util.Map;

import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

import com.example.backend.domain.Document;
import com.example.backend.service.DocumentService;
import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;

@RestController
@RequestMapping("/api/documents")
public class DocumentContentController {

    @Autowired
    DocumentService documentService;
    

    private final Path storageDir;
    private final ObjectMapper objectMapper = new ObjectMapper();

    public DocumentContentController(@Value("${upload.dir}") String uploadDir) {
        this.storageDir = Paths.get(uploadDir, "admin").toAbsolutePath();
        System.out.println("storageDir: " + storageDir);
        try {
            Files.createDirectories(this.storageDir);
        } catch (IOException e) {
            throw new IllegalStateException("문서 JSON 저장 디렉터리를 생성할 수 없습니다.", e);
        }
    }

    @GetMapping("/{docId}/content")
    public ResponseEntity<Map<String, Object>> getDocument(@PathVariable String docId) throws IOException {
        Path target = storageDir.resolve(docId + ".json");
        if (!Files.exists(target)) {
            return ResponseEntity.ok(Map.of("content", null));
        }

        JsonNode content = objectMapper.readTree(Files.readString(target, StandardCharsets.UTF_8));
        return ResponseEntity.ok(Map.of("content", content));
    }

    // @PostMapping("/{docId}/content")
    // public ResponseEntity<Map<String, Object>> saveDocument(
    //     @PathVariable String docId,
    //     @RequestBody SaveRequest request
    // ) throws IOException {
    //     System.out.println("작동하는거니?");
    //     // Path target = storageDir.resolve(docId + ".json");
    //     Path target = storageDir.resolve("1/1/234.json");
    //     JsonNode content = request.content == null ? objectMapper.createObjectNode() : request.content;
    //     objectMapper.writerWithDefaultPrettyPrinter().writeValue(target.toFile(), content);
    //     return ResponseEntity.ok(Map.of("status", "success"));
    // }

    @PostMapping("/1/content")
    public ResponseEntity<Map<String, Object>> saveDocument(
        @RequestBody SaveRequest content
    ) throws IOException {
        System.out.println("작동하는거니?");
        // Path target = storageDir.resolve(docId + ".json");
        Path target = storageDir.resolve("1/1/234.json");
        System.out.println("target: " + target);
        JsonNode result = content.content == null ? objectMapper.createObjectNode() : content.content;
        objectMapper.writerWithDefaultPrettyPrinter().writeValue(target.toFile(), result);
        return ResponseEntity.ok(Map.of("status", "success"));
    }

        @PostMapping("/save")
    public ResponseEntity<Map<String, Long>> saveDocument(@RequestBody Document request) {
    Long documentIdx = documentService.saveDocument(request);
    return ResponseEntity.ok(Map.of("documentIdx", documentIdx));
}

    public static class SaveRequest {
        public JsonNode content;
    }
}

