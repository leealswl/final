package com.example.backend.onlyoffice;

import java.util.HashMap;
import java.util.Map;

import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

import com.auth0.jwt.JWT;
import com.auth0.jwt.algorithms.Algorithm;

@RestController
@RequestMapping("/onlyoffice")
public class OnlyOfficeController {
    private final OnlyOfficeProps props;
    private final FileService files;
    public OnlyOfficeController(OnlyOfficeProps props, FileService files) {
        this.props = props; this.files = files;
    }

    @GetMapping("/config/{fileId}")
    public ResponseEntity<?> getConfig(@PathVariable String fileId) {
        FileMeta f = files.getById(fileId);
        if (f == null) return ResponseEntity.notFound().build();

        String fileUrl = props.getPublicBase() + "/uploads/" + f.storageKey; // 문서서버가 직접 GET
        String key = f.id + "-" + System.currentTimeMillis();                // 콜백 식별자

        Map<String,Object> doc = new HashMap<>();
        doc.put("title", f.name);
        doc.put("url", fileUrl);
        doc.put("fileType", "docx");
        doc.put("key", key);
        doc.put("permissions", Map.of("edit", true, "download", true, "print", true));

        Map<String,Object> editorCfg = new HashMap<>();
        editorCfg.put("callbackUrl", props.getCallbackUrl());
        editorCfg.put("customization", Map.of("autosave", true));

        Map<String,Object> config = new HashMap<>();
        config.put("document", doc);
        config.put("documentType", "word");
        config.put("editorConfig", editorCfg);
        config.put("height", "100%");
        config.put("width", "100%");
        config.put("type", "desktop");

        String token = JWT.create()
                .withClaim("document", doc)
                .withClaim("documentType", "word")
                .withClaim("editorConfig", editorCfg)
                .withClaim("height", "100%")
                .withClaim("width", "100%")
                .withClaim("type", "desktop")
                .sign(Algorithm.HMAC256(props.getJwtSecret()));

        return ResponseEntity.ok(Map.of("config", config, "token", token));
    }

    // 저장 콜백(추후: status==2면 payload.url에서 파일 다운로드 → 새 버전 저장)
    @PostMapping("/callback")
    public Map<String,Object> callback(@RequestBody Map<String,Object> body) {
        System.out.println("OnlyOffice callback: " + body);
        return Map.of("error", 0);
    }
}
