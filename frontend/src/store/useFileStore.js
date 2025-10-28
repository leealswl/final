import { create } from 'zustand'
import { persist,createJSONStorage } from 'zustand/middleware'
import { isRootId } from '../utils/folder';

const ROOTS = [
  { id: 'root-01', type: 'folder', name: '공고문',  children: [] },
  { id: 'root-02', type: 'folder', name: '파일', children: [] },
];
//특정아이디 노드 찾기
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

//특정폴더 하위파일 새 노드 추가
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
// 특정노드 이름 변경
const mapNode = (nodes, id, fn) =>
  nodes.map((n) => {
    const cur = n.id === id ? fn(n) : n;
    if (cur.children?.length) return { ...cur, children: mapNode(cur.children, id, fn) };
    return cur;
  });

function removeNode(nodes, targetId) {
  let removed = null;
  const next = [];

  for (const n of nodes) {
    if (n.id === targetId) {
      removed = n;
      continue;
    }
    if (n.children?.length) {
      const { next: childNext, removed: childRemoved } = removeNode(n.children, targetId);
      if (childRemoved && !removed) removed = childRemoved;
      next.push({ ...n, children: childNext });
    } else {
      next.push(n);
    }
  }
  return { next, removed };
}

export const useFileStore = create(
  persist( //로컬스토리지에 저장
  (set, get) => ({
  tree: structuredClone(ROOTS), //현재 루트 2개
  selectedNodeId: null, //현재 선택된 노드 id
  selectedFile: null, //선택된 노드가 파일일 때, 그 파일 객체
  currentProjectId: null, //업로드/경로 생성에 쓰는 컨텍스트
  currentUserId: null,
  setCurrentContext: ({ projectId, userId }) => //컨텍스트 저장(페이지 진입 시 한 번). 업로드 훅 / 경로 생성에서 사용
  set({ currentProjectId: projectId, currentUserId: userId }),

  deleteNode: (id) =>
  set((state) => {
    if (!id) return {};
    if (isRootId(id)) {
      console.warn('루트 폴더는 삭제할 수 없습니다.'); //root-01/02 루트 폴더는 삭제 금지.
      return {};
    }

    const { next, removed } = removeNode(state.tree, id);
    if (!removed) return {}; // 못 찾은 경우

    // 선택 중인 항목이 삭제되었으면 선택 초기화
    const clearSelection =
      state.selectedNodeId === id ||
      (state.selectedFile && state.selectedFile.id === id);

    return {
      tree: next,
      ...(clearSelection ? { selectedNodeId: null, selectedFile: null } : {}),
    };
  }),

  addUploadedFileNodes: (rootId, nodes) => 
    // addUploadedFileNodes 업로드 완료 후 트리에 파일 노드들 추가.
    //모든 노드는 insertNode를 통해 rootId 폴더의 children에 들어감.  
  set((state) => {
      let next = state.tree;
      for (const node of nodes) {
        next = insertNode(next, rootId, { ...node, children: undefined });
      }
      return { tree: next };
    }),
    // selectNode 사이드바 클릭 시 호출, findNode로 노드를 찾아, 파일이면 selectedFile 세팅
  selectNode: (id) => {
    const n = findNode(get().tree, id);
    set({ selectedNodeId: id, selectedFile: n?.type === 'file' ? n : null });
  },

  deleteSelected: () => {
        const id = get().selectedNodeId || get().selectedFile?.id;
        if (id) get().deleteNode(id);
      },

  resetTree: () => set({ tree: structuredClone(ROOTS), selectedNodeId: null, selectedFile: null }),
  renameNode: (id, name) =>
    set((state) => ({ tree: mapNode(state.tree, id, (n) => ({ ...n, name })) })),
  }),
  {
      name: 'file-store',
      storage: createJSONStorage(()=> localStorage),
    }
));

// 사이드바 파일 트리를 전역으로 관리