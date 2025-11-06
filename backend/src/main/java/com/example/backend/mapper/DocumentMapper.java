package com.example.backend.mapper;

import org.apache.ibatis.annotations.Mapper;

import com.example.backend.domain.Document;



@Mapper
public interface DocumentMapper {
    public int insertDocument(Document document);
    
}

