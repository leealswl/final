package com.example.backend.onlyoffice;

import java.util.HashMap;
import java.util.Map;
import java.util.UUID;

import org.springframework.http.ResponseEntity;
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

    public OnlyOfficeController(OnlyOfficeProps props) {
        this.props = props;
    }

    /**
     * OnlyOffice DocEditor에 줄 config와 JWT를 생성해서 반환
     * - 문서서버(local.json) 설정: token.enable.browser=true, inBody=false
     * - JWT는 "루트 클레임" 방식으로 서명 (payload에 넣지 않음)
     */
        // 프론트가 { url, title }로 요청
    @PostMapping("/config")
    public ResponseEntity<?> buildConfig(@RequestBody Map<String, Object> body) {
        String url = (String) body.get("url");     // 예: http://127.0.0.1:8081/uploads/userId/1/1/abc.docx
        System.out.println("url: " + url);
        String title = (String) body.getOrDefault("title", "document.docx");
        if (url == null || url.isBlank()) {
            return ResponseEntity.badRequest().body(Map.of("error", "url is required"));
        }

        // 문서 캐시 구분용 키
        String key = UUID.randomUUID().toString();

        Map<String, Object> doc = new HashMap<>();
        doc.put("title", title);
        doc.put("url", url);
        doc.put("fileType", "docx");
        doc.put("key", key);
        doc.put("permissions", Map.of("edit", true, "download", true, "print", true));

        Map<String, Object> editorCfg = new HashMap<>();
        editorCfg.put("callbackUrl", props.getCallbackUrl()); // 필요 없으면 null/생략
        editorCfg.put("customization", Map.of("autosave", true));
        editorCfg.put("mode", "edit");
        editorCfg.put("lang", "ko");

        Map<String, Object> config = new HashMap<>();
        config.put("document", doc);
        config.put("documentType", "word");
        config.put("editorConfig", editorCfg);
        config.put("type", "desktop");
        config.put("width", "100%");
        config.put("height", "100%");

        // 7) 브라우저 모드용 JWT (루트 클레임으로 서명)
        String token = JWT.create()
                .withClaim("document", doc)
                .withClaim("documentType", "word")
                .withClaim("editorConfig", editorCfg)
                .withClaim("type", "desktop")
                .withClaim("width", "100%")
                .withClaim("height", "100%")
                .sign(Algorithm.HMAC256(props.getJwtSecret()));

        // 프론트는 {config, token}을 그대로 DocEditor에 전달하면 됨
        return ResponseEntity.ok(Map.of("config", config, "token", token));
    }

    /**
     * OnlyOffice 저장 콜백 (status==2 등일 때 url로 새 버전 다운로드 가능)
     */
    @PostMapping("/callback")
    public Map<String, Object> callback(@RequestBody Map<String, Object> body) {
        System.out.println("OnlyOffice callback: " + body);
        // TODO: status가 2일 때 body.get("url")로 파일 받아 저장하는 로직 추가 가능
        return Map.of("error", 0);
    }
}
