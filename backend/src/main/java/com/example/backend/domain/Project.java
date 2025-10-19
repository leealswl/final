package com.example.backend.domain;

import java.util.Date;

import lombok.Data;

@Data
public class Project {
    private Long projectIdx;
    private Long uIdx;
    private String projectName = "새 프로젝트";
    private Date createdAt;
    private Date updatedAt;

    private User user;

    
}
