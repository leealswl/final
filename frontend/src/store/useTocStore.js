import { create } from 'zustand';

/**
 * 2025-11-17: 목차(TOC) 상태 관리 Store
 * - 목차 데이터 관리
 * - 에디터 인스턴스 관리 (목차 클릭 시 스크롤을 위해)
 * - 활성 섹션 추적
 */
export const useTocStore = create((set, get) => ({
    // 목차 섹션 데이터
    sections: [],
    setSections: (sections) => set({ sections }),

    // 활성 섹션 (현재 편집 중인 섹션)
    activeSection: null,
    setActiveSection: (sectionNumber) => set({ activeSection: sectionNumber }),

    // TipTap 에디터 인스턴스 저장
    editorInstance: null,
    setEditorInstance: (editor) => set({ editorInstance: editor }),

    // 섹션으로 스크롤하기
    scrollToSection: (sectionNumber, sectionTitle) => {
        const { editorInstance } = get();
        if (!editorInstance) {
            console.warn('에디터 인스턴스가 없습니다.');
            return;
        }

        // 에디터에서 해당 섹션의 heading 찾기
        const doc = editorInstance.state.doc;
        let targetPos = null;
        let foundNode = null;

        doc.descendants((node, pos) => {
            if (targetPos !== null) return false; // 이미 찾았으면 중단

            if (node.type.name === 'heading') {
                const text = node.textContent.trim();
                
                // 섹션 번호와 제목을 포함한 텍스트 매칭
                // 예: "1. 연구개발과제의 필요성" 또는 "연구개발과제의 필요성"
                const fullTitle = `${sectionNumber}. ${sectionTitle}`;
                const titleOnly = sectionTitle;
                
                if (text === fullTitle || text === titleOnly || text.includes(sectionTitle)) {
                    targetPos = pos;
                    foundNode = node;
                    return false;
                }
            }
        });

        if (targetPos !== null) {
            console.log('✅ 섹션 찾음:', sectionNumber, sectionTitle, 'at position', targetPos);
            
            // 해당 위치로 스크롤 및 포커스
            editorInstance
                .chain()
                .focus()
                .setTextSelection({ from: targetPos, to: targetPos })
                .scrollIntoView()
                .run();
            
            set({ activeSection: sectionNumber });
        } else {
            console.warn('⚠️ 섹션을 찾을 수 없음:', sectionNumber, sectionTitle);
            
            // 섹션이 없으면 생성할 수 있는 옵션 제공 (향후 구현)
            // 또는 챗봇에게 해당 섹션 생성 요청
        }
    },

    // 목차 메타데이터
    tocMetadata: {},
    setTocMetadata: (metadata) => set({ tocMetadata: metadata }),
}));










