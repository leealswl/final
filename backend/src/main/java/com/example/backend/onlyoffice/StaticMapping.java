package com.example.backend.onlyoffice;

import java.nio.file.Path;

import org.springframework.beans.factory.annotation.Value;
import org.springframework.context.annotation.Configuration;
import org.springframework.web.servlet.config.annotation.ResourceHandlerRegistry;
import org.springframework.web.servlet.config.annotation.WebMvcConfigurer;



@Configuration
public class StaticMapping implements WebMvcConfigurer {
    @Value("${upload.dir:uploads}")
    private String uploadDir;

    @Override
    public void addResourceHandlers(ResourceHandlerRegistry reg) {
        // 2025-11-09 suyeon: 설정된 upload.dir 기반으로 절대 경로 계산
        Path uploadPath = Path.of(uploadDir).toAbsolutePath();

        String location = uploadPath.toUri().toString();
        if (!location.endsWith("/")) location += "/";   // ★ 중요: 디렉터리 표시
        System.out.println("[StaticMapping] uploads location: " + location);
        reg.addResourceHandler("/uploads/**")
           .addResourceLocations(location);
    }
}
