package com.example.backend.domain;

import java.util.Date;

import lombok.Data;

@Data
public class Document {
    private Long documentIdx;
    private Long projectIdx;
    private String folder;
    private String fileName;
    private String filePath;
    private Date createdAt;
    
}
