import React, { useEffect } from 'react'
import { useFileStore } from '../../../store/useFileStore'
import Editor from '../Editor'
import { useParams } from 'react-router'

export default function EditView() {
  const { docId } = useParams();             // /works/edit/:docId
  const getById = useFileStore(s => s.getById);
  const setSelectedFile = useFileStore(s => s.setSelectedFile);

  // URL의 docId → 전역 선택(단방향 동기화)
  useEffect(() => {
    if (!docId) return;
    const f = getById(docId);
    if (f) setSelectedFile(f);
  }, [docId, getById, setSelectedFile]);

  return <Editor />;
}