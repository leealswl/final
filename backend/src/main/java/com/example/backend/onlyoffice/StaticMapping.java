package com.example.backend.onlyoffice;

import java.nio.file.Path;

import org.springframework.context.annotation.Configuration;
import org.springframework.web.servlet.config.annotation.ResourceHandlerRegistry;
import org.springframework.web.servlet.config.annotation.WebMvcConfigurer;



@Configuration
public class StaticMapping implements WebMvcConfigurer{
    @Override
    public void addResourceHandlers(ResourceHandlerRegistry reg) {
        // 프로젝트 루트의 ./uploads 폴더를 http://localhost:8081/uploads/** 로 공개
        Path uploadDir = Path.of("uploads").toAbsolutePath();
        reg.addResourceHandler("/uploads/**")
           .addResourceLocations(uploadDir.toUri().toString());
    }
}
