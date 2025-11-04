package com.example.backend.domain;

import java.util.Date;

import lombok.Data;

@Data
public class Analysis {
    private Long analysisIdx;
    private Long projectIdx;
    private Date createdAt;
    
}
