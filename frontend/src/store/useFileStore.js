import { create } from 'zustand'
import { persist } from 'zustand/middleware'

const ROOTS = [
  { id: 'root-01', type: 'folder', name: '01. 제안서',  children: [] },
  { id: 'root-02', type: 'folder', name: '02. 첨부서류', children: [] },
  { id: 'root-03', type: 'folder', name: '03. 추가자료', children: [] },
];
export const toFolderNum = (rootId) =>
  rootId === 'root-01' ? 1 : rootId === 'root-02' ? 2 : 3;

const findNode = (nodes, id) => {
  for (const n of nodes) {
    if (n.id === id) return n;
    if (n.children?.length) {
      const k = findNode(n.children, id);
      if (k) return k;
    }
  }
  return null;
};
const insertNode = (nodes, parentId, node) => {
  if (!parentId) return [...nodes, node];
  return nodes.map((n) => {
    if (n.id === parentId && n.type === 'folder') {
      return { ...n, children: [...(n.children || []), node] };
    }
    if (n.children?.length) return { ...n, children: insertNode(n.children, parentId, node) };
    return n;
  });
};
const mapNode = (nodes, id, fn) =>
  nodes.map((n) => {
    const cur = n.id === id ? fn(n) : n;
    if (cur.children?.length) return { ...cur, children: mapNode(cur.children, id, fn) };
    return cur;
  });

export const useFileStore = create(
  persist(
  (set, get) => ({
  tree: structuredClone(ROOTS),
  selectedNodeId: null,
  selectedFile: null,
  currentProjectId: null,
  currentUserId: null,
  setCurrentContext: ({ projectId, userId }) =>
  set({ currentProjectId: projectId, currentUserId: userId }),

  addUploadedFileNodes: (rootId, nodes) =>
    set((s) => {
      let next = s.tree;
      for (const node of nodes) {
        next = insertNode(next, rootId, { ...node, children: undefined });
      }
      return { tree: next };
    }),

  selectNode: (id) => {
    const n = findNode(get().tree, id);
    set({ selectedNodeId: id, selectedFile: n?.type === 'file' ? n : null });
  },

  resetTree: () => set({ tree: structuredClone(ROOTS), selectedNodeId: null, selectedFile: null }),
  renameNode: (id, name) =>
    set((s) => ({ tree: mapNode(s.tree, id, (n) => ({ ...n, name })) })),
  
})));
