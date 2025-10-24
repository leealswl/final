package com.example.backend.config;

import java.nio.file.Paths;

import org.springframework.beans.factory.annotation.Value;
import org.springframework.context.annotation.Configuration;
import org.springframework.web.servlet.config.annotation.ResourceHandlerRegistry;
import org.springframework.web.servlet.config.annotation.WebMvcConfigurer;

@Configuration
public class StaticResourceConfig implements WebMvcConfigurer {

  @Value("${upload.dir:C:/vs/final/uploads}") 
  private String uploadDir;
  
  @Override 
  public void addResourceHandlers(ResourceHandlerRegistry registry) {
    String location = Paths.get(uploadDir).toUri().toString();
    if (!location.endsWith("/")) location += "/";
    registry.addResourceHandler("/uploads/**")
            .addResourceLocations(location);
    }
  }
