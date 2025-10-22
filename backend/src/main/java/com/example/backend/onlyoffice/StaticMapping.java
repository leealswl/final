package com.example.backend.onlyoffice;

import java.nio.file.Path;

import org.springframework.context.annotation.Configuration;
import org.springframework.web.servlet.config.annotation.ResourceHandlerRegistry;
import org.springframework.web.servlet.config.annotation.WebMvcConfigurer;



@Configuration
public class StaticMapping implements WebMvcConfigurer {
    @Override
    public void addResourceHandlers(ResourceHandlerRegistry reg) {
        Path uploadDir = Path.of("backend/uploads").toAbsolutePath();
        String location = uploadDir.toUri().toString(); // file:///C:/.../uploads/
        if (!location.endsWith("/")) location += "/";   // ★ 중요: 디렉터리 표시
        reg.addResourceHandler("/uploads/**")
           .addResourceLocations(location);
    }
}
