import React, { useEffect } from "react";
import { useParams, useNavigate, useLocation } from "react-router-dom";
import Layout from "./components/layout/Layout";
import { useFileStore } from "../../store/useFileStore";

const Editpage = () => {
  const { id } = useParams();
  const navigate = useNavigate();
  const location = useLocation();

  const selectNode     = useFileStore((s) => s.selectNode);
  const selectedNodeId = useFileStore((s) => s.selectedNodeId);

  // 1) 맨 처음 진입하거나 URL이 바뀌었을 때: URL의 id를 스토어 선택으로 반영
  useEffect(() => {
    if (id) selectNode(id);
  }, [id, selectNode]);

  // 2) 사이드바에서 선택이 바뀌면 URL도 동기화 (/edit/:id)
  useEffect(() => {
    if (!selectedNodeId) return;
    const want = `/edit/${selectedNodeId}`;
    if (location.pathname !== want) {
      navigate(want, { replace: false });
    }
  }, [selectedNodeId, location.pathname, navigate]);

  return <Layout />;
};

export default Editpage;
