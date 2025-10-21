package com.example.backend.controller;

import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

import com.example.backend.FastAPI.FastAPIService;

@RestController
@RequestMapping("/api/analysis/*")
public class AnalysisController {

    @Autowired
    FastAPIService fastApi;
    
}
