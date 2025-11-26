import { useCallback } from 'react';
import { useDocumentSaveStore } from '../store/useDocumentSaveStore';
import api from '../utils/api';

export default function useDocumentSave() {
    const {
        projectIdx,
        documentIdx,
        fileName,
        content,
        isDirty,
        saving,
        saveError,
        setSaving,
        markSaved,
        setSaveError,
        setMeta,
    } = useDocumentSaveStore();
    

    // 실제 저장 함수
    const saveDocument = useCallback(
        async (override = {}) => {
            // 이미 저장 중이면 중복 요청 방지
            if (saving) {
                return { ok: false, error: '이미 저장 중입니다.' };
            }

            if (!projectIdx) {
                const msg = 'projectIdx가 설정되어 있지 않습니다.';
                console.error(msg, { projectIdx, documentIdx });
                setSaveError(msg);
                return { ok: false, error: msg };
            }

            // 변경사항이 없으면 굳이 저장 안 함 (DOCX 쪽에서 강제 저장하려면 override.force 사용)
            if (!isDirty && !override.force) {
                return { ok: true, message: '변경된 내용이 없어 저장하지 않았습니다.' };
            }

            if (!content) {
                const msg = '저장할 문서 내용이 없습니다.';
                console.error(msg);
                setSaveError(msg);
                return { ok: false, error: msg };
            }

            const finalFileName = override.fileName ?? fileName ?? 'document';

            setSaving(true);

            try {
                const payload = {
                    projectIdx,
                    documentIdx: documentIdx ?? null, // ★ 새 문서면 null 그대로 보냄
                    fileName: finalFileName,
                    content: JSON.stringify(content), // ★ Tiptap JSON → 문자열
                };
                console.log('[saveDocument] 서버로 보낼 payload:', payload);

                const { data } = await api.post('/api/documents/save', payload);

                // ★ 여기서부터: 항상 최종 documentIdx를 계산해서 리턴해 주기
                let finalDocIdx = documentIdx ?? null;

                // 백엔드가 새 documentIdx를 내려줬다면 스토어에 반영
                if (data?.documentIdx) {
                    finalDocIdx = data.documentIdx;

                    // 기존에 documentIdx가 없던 경우(완전 새 문서)만 메타 업데이트
                    if (!documentIdx) {
                        setMeta({
                            projectIdx,
                            documentIdx: data.documentIdx,
                            fileName: finalFileName,
                        });
                    }
                }

                markSaved();
                setSaveError(null); // 성공했으니 에러 상태 초기화

                // ✅ DOCX 버튼에서 재사용할 수 있도록 documentIdx를 함께 리턴
                return {
                    ok: true,
                    documentIdx: finalDocIdx,
                    message: '문서가 저장되었습니다.',
                };
            } catch (error) {
                console.error('문서 저장 실패:', error);
                const msg =
                    error?.response?.data?.message ||
                    error?.message ||
                    '저장 중 오류가 발생했습니다.';
                setSaveError(msg);
                return { ok: false, error: msg };
            } finally {
                setSaving(false);
            }
        },
        [
            projectIdx,
            documentIdx,
            fileName,
            content,
            isDirty,
            saving,
            setSaving,
            markSaved,
            setSaveError,
            setMeta,
        ],
    );

    return {
        saveDocument,
        saving,
        isDirty,
        saveError,
    };
}
