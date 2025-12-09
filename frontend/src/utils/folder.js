const ROOT_TO_NUM = { 'root-01': 1, 'root-02': 2 };

export function toFolderNum(rootId) {
    const node = ROOT_TO_NUM[rootId];
    if (!node) 
        throw new Error(`Invalid rootId: ${rootId}`); 
    return node;
}

export function isRootId(id) {
    return Object.prototype.hasOwnProperty.call(ROOT_TO_NUM, id);
}

// rootId에 (root-01)를 넣으면 디비 도큐먼트테이블 folder 1,2 로 바꿔줌
// DB가 NUMBER 컬럼으로 폴더를 저장할 때, 프론트 rootId를 folderNum을 쓰기 위함.