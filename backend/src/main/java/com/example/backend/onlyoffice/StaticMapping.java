package com.example.backend.onlyoffice;

import java.nio.file.Path;

import org.springframework.context.annotation.Configuration;
import org.springframework.web.servlet.config.annotation.ResourceHandlerRegistry;
import org.springframework.web.servlet.config.annotation.WebMvcConfigurer;



@Configuration
public class StaticMapping implements WebMvcConfigurer {
    @Override
    public void addResourceHandlers(ResourceHandlerRegistry reg) {
        // ★ Spring Boot가 backend 디렉토리에서 실행되므로 상대 경로는 "uploads"
        Path uploadDir = Path.of("uploads").toAbsolutePath();

        String location = uploadDir.toUri().toString(); // file:///Users/.../backend/uploads/
        if (!location.endsWith("/")) location += "/";   // ★ 중요: 디렉터리 표시
        System.out.println("[StaticMapping] uploads location: " + location);
        reg.addResourceHandler("/uploads/**")
           .addResourceLocations(location);
    }
}
