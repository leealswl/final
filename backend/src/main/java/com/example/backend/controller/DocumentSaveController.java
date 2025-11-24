package com.example.backend.controller;

import java.util.Map;

import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

import com.example.backend.domain.DocumentSave;
import com.example.backend.service.DocumentSaveService;

import lombok.RequiredArgsConstructor;

@RestController
@RequestMapping("/api/documents")
@RequiredArgsConstructor
public class DocumentSaveController {

    private final DocumentSaveService documentSaveService;

    @PostMapping("/save")
    public ResponseEntity<Map<String, Long>> saveDocument(@RequestBody DocumentSave request) {
    Long documentIdx = documentSaveService.saveDocument(request);
    return ResponseEntity.ok(Map.of("documentIdx", documentIdx));
}
}
