package com.example.backend.config;

import org.springframework.beans.factory.annotation.Value;
import org.springframework.context.annotation.Configuration;
import org.springframework.web.servlet.config.annotation.ResourceHandlerRegistry;
import org.springframework.web.servlet.config.annotation.WebMvcConfigurer;

@Configuration
public class StaticResourceConfig implements WebMvcConfigurer {

  @Value("${upload.dir:uploads}") 
    String uploadDir;
  @Override public void addResourceHandlers(ResourceHandlerRegistry r) {
    String loc = "file:" + (uploadDir.endsWith("/") ? uploadDir : uploadDir + "/");
    r.addResourceHandler("/uploads/**").addResourceLocations(loc);
  }
}

