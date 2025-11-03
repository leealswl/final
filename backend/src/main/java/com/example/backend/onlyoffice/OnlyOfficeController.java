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

         // 1) 확장자 추출
        String ext = getExt(title != null ? title : url); // ex: "txt", "hwp", "hwpx", "docx", "xlsx", "pptx"
        // 2) OO 문서 유형 매핑(word/cell/slide)
        String documentType = toDocumentType(ext); // "word" | "cell" | "slide"
        // 3) fileType은 확장자 그대로
        String fileType = ext;

        // 문서 캐시 구분용 키
        String key = UUID.randomUUID().toString();

        // document
        Map<String, Object> doc = new HashMap<>();
        doc.put("title", title);
        doc.put("url", url);
        doc.put("fileType", fileType);
        doc.put("key", key);
        doc.put("permissions", Map.of("edit", true, "download", true, "print", true));
        
        // editorConfig
        Map<String, Object> editorCfg = new HashMap<>();
        editorCfg.put("callbackUrl", props.getCallbackUrl()); // 필요 없으면 null/생략
        editorCfg.put("customization", Map.of("autosave", true));
        editorCfg.put("mode", "edit");
        editorCfg.put("lang", "ko");


        //// 최종 config
        Map<String, Object> config = new HashMap<>();
        config.put("document", doc);
        config.put("documentType", documentType);
        config.put("editorConfig", editorCfg);
        config.put("type", "desktop");
        config.put("width", "100%");
        config.put("height", "100%");
        System.out.println("[OO] final config: " + config);

        // 7) 브라우저 모드용 JWT (루트 클레임으로 서명)
        String token = JWT.create()
                .withClaim("document", doc)
                .withClaim("documentType", documentType)
                .withClaim("editorConfig", editorCfg)
                .withClaim("type", "desktop")
                .withClaim("width", "100%")
                .withClaim("height", "100%")
                .sign(Algorithm.HMAC256(props.getJwtSecret()));

        // 프론트는 {config, token}을 그대로 DocEditor에 전달하면 됨
        return ResponseEntity.ok(Map.of("config", config, "token", token));
    }
        private static String getExt(String nameOrUrl) {
        String s = nameOrUrl;
        int q = s.indexOf('?');
        if (q >= 0) s = s.substring(0, q);
        int hash = s.indexOf('#');
        if (hash >= 0) s = s.substring(0, hash);
        int slash = s.lastIndexOf('/');
        if (slash >= 0) s = s.substring(slash + 1);
        int dot = s.lastIndexOf('.');
        if (dot < 0) return "docx"; // 기본값
        return s.substring(dot + 1).toLowerCase();
    }

        private static String toDocumentType(String ext) {
            switch (ext) {
            // 워드류
            case "doc": case "docx": case "odt": case "rtf": case "txt":
            case "pdf": case "md": case "hwp": case "hwpx":
                return "word";
            // 스프레드시트
            case "xls": case "xlsx": case "ods": case "csv":
                return "cell";
            // 프레젠테이션
            case "ppt": case "pptx": case "odp":
                return "slide";
            default:
              return "word"; // 모르는 확장자는 word로
        }
    }

    /* OnlyOffice 저장 콜백 (status==2 등일 때 url로 새 버전 다운로드 가능)*/
    @PostMapping("/callback")
    public Map<String, Object> callback(@RequestBody Map<String, Object> body) {
        System.out.println("OnlyOffice callback: " + body);
        // TODO: status가 2일 때 body.get("url")로 파일 받아 저장하는 로직 추가 가능
        return Map.of("error", 0);
    }
}
