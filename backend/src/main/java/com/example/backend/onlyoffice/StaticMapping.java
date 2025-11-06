package com.example.backend.onlyoffice;

import java.nio.file.Path;

import org.springframework.context.annotation.Configuration;
import org.springframework.web.servlet.config.annotation.ResourceHandlerRegistry;
import org.springframework.web.servlet.config.annotation.WebMvcConfigurer;



@Configuration
public class StaticMapping implements WebMvcConfigurer {
    @Override
    public void addResourceHandlers(ResourceHandlerRegistry reg) {
        // ★ Windows (팀원용): backend/uploads
        Path uploadDir = Path.of("backend/uploads").toAbsolutePath();

        // ★ Mac (현재 사용): uploads (프로젝트 루트)
        // Path uploadDir = Path.of("uploads").toAbsolutePath();

        String location = uploadDir.toUri().toString(); // file:///C:/.../uploads/
        if (!location.endsWith("/")) location += "/";   // ★ 중요: 디렉터리 표시
        // mac용 확인
        // System.out.println("[StaticMapping] uploads location: " + location);
        reg.addResourceHandler("/uploads/**")
           .addResourceLocations(location);
    }
}
