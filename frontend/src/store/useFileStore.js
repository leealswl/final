import { create } from "zustand";

// 샘플 트리 (id는 문자열 권장)
const initialTree = [
  { id: "root-01", type: "folder", name: "01. 제안서", children: [] },
  { id: "root-02", type: "folder", name: "02. 첨부서류", children: [] },
  { id: "root-03", type: "folder", name: "03. 추가자료", children: [] },
];

export const useFileStore = create((set, get) => ({
  tree: initialTree,
  selectedNodeId: null,
  selectedFile: null, // 파일을 선택한 경우 여기에 객체 저장

  // 노드 선택
  selectNode: (id) => {
    const n = findNode(get().tree, id);
    set({ selectedNodeId: id, selectedFile: n?.type === "file" ? n : null });
  },

  // ✅ 업로드(프론트 더미): 파일 객체들을 트리에 추가
  uploadFiles: async (files, parentId = null) => {
    if (!files?.length) return;
    const toNode = (f) => ({
      id: crypto.randomUUID(),
      type: "file",
      name: f.name,
      mime: f.type || guessMime(f.name),
      status: "unknown",
    });
    const newNodes = Array.from(files).map(toNode);
    set((s) => {
      let next = s.tree;
      for (const node of newNodes) next = insertNode(next, parentId, node);
      return { tree: next };
    });
    return newNodes;
  },

  renameNode: (id, name) =>
    set((s) => ({ tree: mapNode(s.tree, id, (n) => ({ ...n, name })) })),
}));

// ---- helpers ----
function guessMime(name) {
  const x = name.toLowerCase();
  if (x.endsWith(".md") || x.endsWith(".txt")) return "text/markdown";
  if (x.endsWith(".pdf")) return "application/pdf";
  if (x.endsWith(".docx")) return "application/vnd.openxmlformats-officedocument.wordprocessingml.document";
  if (x.endsWith(".hwp") || x.endsWith(".hwpx")) return "application/x-hwp";
  return "application/octet-stream";
}
function findNode(nodes, id) {
  for (const n of nodes) { if (n.id === id) return n; if (n.children){ const k=findNode(n.children,id); if(k) return k; } }
  return null;
}
function insertNode(nodes, parentId, node) {
  if (!parentId) return [...nodes, node];
  return nodes.map((n) => {
    if (n.id === parentId && n.type === "folder") return { ...n, children: [...(n.children || []), node] };
    if (n.children) return { ...n, children: insertNode(n.children, parentId, node) };
    return n;
  });
}
function mapNode(nodes, id, fn) {
  return nodes.map((n) => {
    const cur = n.id === id ? fn(n) : n;
    if (cur.children) return { ...cur, children: mapNode(cur.children, id, fn) };
    return cur;
  });
}