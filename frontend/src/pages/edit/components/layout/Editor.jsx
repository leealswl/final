// src/pages/edit/components/layout/Editor.jsx
import React, { useEffect, useMemo, useRef, useState } from "react";
import { Box, CircularProgress, Typography, TextField } from "@mui/material";
import { useFileStore } from "../../../../store/useFileStore";
import api from "../../../../utils/api";


// mime/확장자로 타입 판별
function pickKind(file) {
  if (!file) return "empty";
  if (file.type === "folder") return "folder";
  const name = (file.name || "").toLowerCase();
  const mime = file.mime || "";
  if (name.endsWith(".docx") || mime.includes("officedocument.wordprocessingml.document")) return "docx";
  if (name.endsWith(".md") || name.endsWith(".txt") || mime.startsWith("text/") || mime.includes("markdown")) return "text";
  if (name.endsWith(".pdf") || mime.includes("pdf")) return "pdf";
  return "unknown";
}

// OnlyOffice api.js 로드
function useOnlyOfficeReady() {
  const [ready, setReady] = useState(!!window.DocsAPI);
  useEffect(() => {
    if (window.DocsAPI) return;
    const s = document.createElement("script");
    s.src = import.meta.env.VITE_ONLYOFFICE_SRC;
    s.async = true;
    s.onload = () => setReady(true);
    s.onerror = () => console.error("OnlyOffice API 로드 실패");
    document.body.appendChild(s);
  }, []);
  return ready || !!window.DocsAPI;
}

// ---------- 서브뷰(같은 파일 내부) ----------

// DOCX OnlyOffice 뷰
function DocxView({ fileId }) {
  const containerRef = useRef(null);
  const ready = useOnlyOfficeReady();
  const [status, setStatus] = useState("idle"); // idle | loading | error
  useEffect(() => {
    let editor;
    async function mount() {
      try {
        setStatus("loading");
        const { data } = await api.get(`/onlyoffice/config/${fileId}`);
        const { config, token } = data;
        editor = new window.DocsAPI.DocEditor(containerRef.current, { ...config, token });
        setStatus("idle");
      } catch (e) {
        console.error(e);
        setStatus("error");
      }
    }
    if (ready && fileId && containerRef.current) mount();
    return () => {
      try { editor?.destroyEditor?.(); } catch {}
    };
  }, [ready, fileId]);

  if (!ready) return <Center>OnlyOffice 로딩 중…</Center>;
  if (status === "loading") return <Center><CircularProgress size={28} /></Center>;
  if (status === "error")
    return <Pad>에디터 설정을 불러오지 못했습니다. (JWT/파일 URL 확인)</Pad>;

  return <Box ref={containerRef} sx={{ width: "100%", height: "100%" }} />;
}

// 텍스트 뷰 (md/txt) – 자동 저장
function TextView({ fileId }) {
  const [value, setValue] = useState("");
  const [saving, setSaving] = useState("idle"); // idle | saving | saved

  // 로드
  useEffect(() => {
    let ignore = false;
    (async () => {
      try {
        const res = await api.get(`/files/${fileId}/content`, { responseType: "text" });
        if (!ignore) setValue(typeof res.data === "string" ? res.data : "");
      } catch (e) { console.error(e); }
    })();
    return () => { ignore = true; };
  }, [fileId]);

  // 디바운스 저장
  useEffect(() => {
    const t = setTimeout(async () => {
      try {
        setSaving("saving");
        await api.put(`/files/${fileId}/content`, value ?? "", {
          headers: { "Content-Type": "text/plain;charset=utf-8" },
        });
        setSaving("saved");
        setTimeout(() => setSaving("idle"), 700);
      } catch (e) { console.error(e); setSaving("idle"); }
    }, 700);
    return () => clearTimeout(t);
  }, [fileId, value]);

  return (
    <Box sx={{ height: "100%", display: "flex", flexDirection: "column" }}>
      <Box sx={{ p: 1, borderBottom: "1px solid #eee", fontSize: 12, color: "#666" }}>
        {saving === "saving" ? "저장 중…" : saving === "saved" ? "저장 완료" : " "}
      </Box>
      <TextField
        value={value}
        onChange={(e) => setValue(e.target.value)}
        fullWidth
        multiline
        sx={{ flex: 1, "& .MuiInputBase-root": { height: "100%" } }}
        minRows={8}
      />
    </Box>
  );
}

// PDF 뷰
function PdfView({ url }) {
  if (!url) return <Pad>PDF 주소가 없습니다.</Pad>;
  return (
    <Box sx={{ width: "100%", height: "100%" }}>
      <iframe title="pdf" src={url} style={{ border: "none", width: "100%", height: "100%" }} />
    </Box>
  );
}

// 공용 UI
function Center({ children }) {
  return <Box sx={{ height: "100%", display: "grid", placeItems: "center" }}>{children}</Box>;
}
function Pad({ children }) {
  return <Box sx={{ p: 2, color: "text.secondary" }}>{children}</Box>;
}

// ---------- 메인 Editor ----------
export default function Editor() {
  const { selectedFile } = useFileStore();

  // 선택된 파일의 메타(특히 public_url 없는 경우 보강)
  const [meta, setMeta] = useState(null);
  const file = useMemo(() => selectedFile || null, [selectedFile]);

  useEffect(() => {
    setMeta(null);
    if (!file || file.type === "folder") return;
    // public_url 없으면 메타 조회
    if (!file.public_url) {
      (async () => {
        try {
          const { data } = await api.get(`/files/${file.id}`);
          setMeta({ ...file, ...data });
        } catch (e) { setMeta(file); }
      })();
    } else {
      setMeta(file);
    }
  }, [file]);

  const kind = pickKind(meta || file);

  if (!file) return <Pad>왼쪽에서 파일을 선택하세요.</Pad>;
  if (file.type === "folder") return <Pad>폴더를 선택했습니다. 파일을 선택해 주세요.</Pad>;

  // 타입별 렌더링
  if (kind === "docx") return <DocxView fileId={file.id} />;
  if (kind === "text") return <TextView fileId={file.id} />;
  if (kind === "pdf")  return <PdfView url={(meta || file)?.public_url} />;

  return (
    <Pad>
      미지원 형식입니다. (권장: DOCX / MD / TXT / PDF)
      <Box sx={{ mt: 1, fontSize: 12 }}>
        선택된 파일: <b>{file.name}</b> ({file.mime || "unknown"})
      </Box>
    </Pad>
  );
}
