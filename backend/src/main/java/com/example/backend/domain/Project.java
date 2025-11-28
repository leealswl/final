package com.example.backend.domain;

import java.util.Date;

import lombok.Data;

@Data
public class Project {
    private Long projectIdx;
    private Long userIdx;
    private String projectName = "새 프로젝트";
    private Date createdAt;
    private Date updatedAt;
    private String threadId;

    private User user;

    
}
