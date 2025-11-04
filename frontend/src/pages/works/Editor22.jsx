// Editor22.jsx
import React, { useEffect, useMemo, useState } from "react";
import { Box, CircularProgress, TextField, FormControl, InputLabel, Select, MenuItem } from "@mui/material";
import { useFileStore } from "../../../../store/useFileStore";
import api from "../../../../utils/api";
import Assistant from "./Assistant";

const toAbs = (p) => (p?.startsWith('http') ? p : `http://127.0.0.1:8081${p}`);

// 공용 UI
function Center({ children }) {
  return <Box sx={{ height: "100%", display: "grid", placeItems: "center" }}>{children}</Box>;
}
function Pad({ children }) {
  return <Box sx={{ p: 2, color: "text.secondary" }}>{children}</Box>;
}

// 파일 종류 판별
function pickKind(file) {
  if (!file) return "empty";
  if (file.type === "folder") return "folder";
  const name = (file.name || "").toLowerCase();
  const mime = (file.mime || "").toLowerCase();
  if (name.endsWith(".doc") || name.endsWith(".docx") || name.endsWith(".odt") || name.endsWith(".rtf") ||
      name.endsWith(".txt") || name.endsWith(".md") || name.endsWith(".hwp") || name.endsWith(".hwpx") ||
      name.endsWith(".xls") || name.endsWith(".xlsx") || name.endsWith(".ppt") || name.endsWith(".pptx"))
    return "office";
  if (name.endsWith(".md") || name.endsWith(".txt") || mime.startsWith("text/") || mime.includes("markdown"))
    return "text";
  if (name.endsWith(".pdf") || mime.includes("pdf"))
    return "pdf";
  return "unknown";
}

// OnlyOffice API 준비 훅
function useOnlyOfficeReady() {
  const [ready, setReady] = useState(!!window.DocsAPI);
  useEffect(() => {
    if (window.DocsAPI) { setReady(true); return; }
    const src = import.meta.env.VITE_ONLYOFFICE_SRC;
    if (!src) { console.error("VITE_ONLYOFFICE_SRC 미설정"); return; }
    const exists = Array.from(document.scripts).some(s => s.src === src);
    if (exists) {
      const t = setInterval(() => { if (window.DocsAPI) { setReady(true); clearInterval(t); } }, 100);
      return () => clearInterval(t);
    }
    const s = document.createElement("script");
    s.src = src; s.async = true;
    s.onload = () => setReady(true);
    s.onerror = () => console.error("OnlyOffice API 로드 실패:", src);
    document.body.appendChild(s);
  }, []);
  return ready || !!window.DocsAPI;
}

const fileKey = (f) => String(f?.id || f?.path || "");

// Docx 편집기 호스트
function DocxHost({ active, file, onConnectorReady }) {
  const hostRef = React.useRef(null);
  const editorRef = React.useRef(null);
  const lastKeyRef = React.useRef(null);
  const ready = useOnlyOfficeReady();

  const destroy = React.useCallback(() => {
    try { editorRef.current?.destroyEditor?.(); } catch {}
    editorRef.current = null;
  }, []);

  useEffect(() => {
    if (!ready || !active || !file?.path) return;

    const currentKey = fileKey(file);
    if (lastKeyRef.current === currentKey && editorRef.current) return;

    let cancelled = false;
    (async () => {
      try {
        destroy();
        const el = hostRef.current;
        if (!el) throw new Error("host element missing");
        if (!el.id) el.id = `oo-${Math.random().toString(36).slice(2)}`;

        const absoluteUrl = `http://127.0.0.1:8081${file.path}`;
        const { data } = await api.post("/onlyoffice/config", {
          url: absoluteUrl,
          title: file.name,
        });
        if (cancelled) return;

        const { config, token } = data || {};
        if (!window.DocsAPI?.DocEditor) throw new Error("DocsAPI not ready");

        // DocEditor 생성
        editorRef.current = new window.DocsAPI.DocEditor(el.id, {
          ...config,
          token,
          width: "100%",
          height: "100%",
          events: {
            onAppReady() { console.log("[OO] onAppReady"); },
            onDocumentReady() {
              console.log("[OO] onDocumentReady");

              if (editorRef.current?.createConnector) {
                const connector = editorRef.current.createConnector();
                console.log("[OO] Connector ready:", connector);

                // 문서 로드 완료 후 ContentControl 가져오기
                connector.executeMethod("GetAllContentControls", null, (fields) => {
                  console.log("[OO] ContentControls:", fields);
                  connector.fields = fields;

                });



                if (onConnectorReady) onConnectorReady(connector);
              }
            },
            onError(e) { console.error("[OO] onError:", e); }
          }
        });
        lastKeyRef.current = currentKey;

      } catch (e) {
        console.error("[DocxHost] init error:", e);
      }
    })();

    return () => { cancelled = true; };
  }, [ready, active, file?.id, file?.path, destroy, onConnectorReady]);

  useEffect(() => destroy, [destroy]);

  return (
    <div
      ref={hostRef}
      style={{
        display: active ? "block" : "none",
        width: "100%",
        height: "100vh",
        background: "#f0f9ff",
      }}
    />
  );
}

// 폼 필드 선택/값 변경 UI
function FormFiller({ connector }) {
  const [fields, setFields] = useState([]);
  const [selectedId, setSelectedId] = useState("");
  const [value, setValue] = useState("");

  useEffect(() => {
    if (!connector) return;
    connector.executeMethod("GetAllContentControls", null, (result) => {
      setFields(result || []);
      if (result && result.length > 0) setSelectedId(result[0].Id);
    });
  }, [connector]);

  const handleChangeField = (e) => {
    setSelectedId(e.target.value);
    const field = fields.find(f => f.Id === e.target.value);
    setValue(field?.Text || "");
  };

  const handleChangeValue = (e) => {
    setValue(e.target.value);
    if (selectedId) {
      connector.executeMethod("SetFormValue", [selectedId, e.target.value]);
    }
  };

  if (!connector) return null;
  if (fields.length === 0) return <Pad>문서 필드를 로딩 중…</Pad>;

  return (
    <Box sx={{ p: 2, display: "flex", gap: 2, alignItems: "center" }}>
      <FormControl>
        <InputLabel>필드 선택</InputLabel>
        <Select value={selectedId} onChange={handleChangeField} sx={{ minWidth: 200 }}>
          {fields.map(f => (
            <MenuItem key={f.Id} value={f.Id}>{f.Title || f.Tag || f.Id}</MenuItem>
          ))}
        </Select>
      </FormControl>
      <TextField
        label="값 입력"
        value={value}
        onChange={handleChangeValue}
      />
    </Box>
  );
}

// 메인 Editor 컴포넌트
export default function Editor22() {
  const { selectedFile } = useFileStore();
  const file = useMemo(() => selectedFile || null, [selectedFile]);
  const kind = pickKind(file);
  const isOffice = kind === 'office';

  const [connector, setConnector] = useState(null);

  if (!file) return <Pad>왼쪽에서 파일을 선택하세요.</Pad>;
  if (file.type === "folder") return <Pad>폴더가 아니라 파일을 선택해 주세요.</Pad>;

  return (
    <Box sx={{ width: "100%", height: "100%", minHeight: 0 }}>
      <DocxHost active={isOffice} file={file} onConnectorReady={setConnector} />
      {connector && <FormFiller connector={connector} />}
      {connector && <Assistant connector={connector} />}   {/* 여기에 추가 */}

      {!isOffice && kind === "text" && <TextView file={file} />}
      {!isOffice && kind === "pdf" && (
        <Box sx={{ width: "100%", height: "100vh" }}>
          <PdfView file={file} />
        </Box>
      )}
    </Box>
  );
}

// TextView, PdfView는 기존 코드 그대로 사용
