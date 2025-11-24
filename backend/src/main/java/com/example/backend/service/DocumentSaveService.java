package com.example.backend.service;

import com.example.backend.domain.DocumentSave;

public interface DocumentSaveService {
    Long saveDocument(DocumentSave request);
}