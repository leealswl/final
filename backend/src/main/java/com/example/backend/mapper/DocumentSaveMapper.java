package com.example.backend.mapper;

import org.apache.ibatis.annotations.Mapper;

import com.example.backend.domain.DocumentSave;

@Mapper
public interface DocumentSaveMapper {
    int insertDocument(DocumentSave document); 
    int updateDocumentContent(DocumentSave request);
}
