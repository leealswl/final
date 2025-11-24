package com.example.backend.domain;

import lombok.Data;

@Data
public class DocumentSave {
    private Long projectIdx;
    private Long documentIdx;
    private String fileName;
    private String content;
    
}
