/**
 * Tiptap doc JSON에서 순수 텍스트만 추출
 * - paragraph / text 노드만 타겟
 * - ```plaintext / ``` 코드펜스 제거
 * - zero-width space(​) 제거
 */
export function tiptapDocToPlainText(doc) {
    if (!doc || doc.type !== 'doc' || !Array.isArray(doc.content)) {
        return '';
    }

    const lines = [];

    const walk = (nodes) => {
        if (!nodes) return;
        for (const node of nodes) {
            if (!node) continue;

            if (node.type === 'text' && typeof node.text === 'string') {
                const t = node.text;
                // zero-width space 제거
                if (t.replace(/\u200B/g, '').trim().length === 0) {
                    continue;
                }
                lines.push(t);
            }

            if (Array.isArray(node.content)) {
                walk(node.content);
            }
        }
    };

    walk(doc.content);

    // 줄 합치기
    let full = lines.join('\n');

    // 코드펜스 제거: ```plaintext, ``` 같은 것들
    full = full.replace(/```plaintext/g, '');
    full = full.replace(/```/g, '');

    // zero-width space 전체 제거 + 양쪽 공백 trim
    full = full.replace(/\u200B/g, '').trim();

    return full;
}
