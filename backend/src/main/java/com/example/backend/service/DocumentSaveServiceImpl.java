package com.example.backend.service;

import org.springframework.stereotype.Service;

import com.example.backend.domain.DocumentSave;
import com.example.backend.mapper.DocumentSaveMapper;

import lombok.RequiredArgsConstructor;

@Service
@RequiredArgsConstructor
public class DocumentSaveServiceImpl implements DocumentSaveService {

    private final DocumentSaveMapper documentSaveMapper;

    @Override
    public Long saveDocument(DocumentSave request) {
        if (request.getProjectIdx() == null) {
            throw new IllegalArgumentException("projectIdx는 필수입니다.");
        }

        // 새 문서 생성
        if (request.getDocumentIdx() == null) {
            int rows = documentSaveMapper.insertDocument(request);

            if (rows != 1) {
                throw new IllegalStateException("문서 INSERT 실패: rows=" + rows);
            }

            Long generatedId = request.getDocumentIdx();  // ← selectKey가 여기 채워줌
            System.out.println("새 문서 생성: documentIdx=" + generatedId);
            return generatedId;
        }

        // 기존 문서 업데이트
        documentSaveMapper.updateDocumentContent(request);
        return request.getDocumentIdx();
    }
}