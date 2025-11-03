import React, { useEffect, useMemo, useState, useRef, useCallback } from "react";
import { Box } from "@mui/material";
import { useFileStore } from "../../../../store/useFileStore";
import api from "../../../../utils/api";

// 필드 선택해서 해당 필드 값 변경

// 공용 UI
function Pad({ children }) {
  return <Box sx={{ p: 2, color: "text.secondary" }}>{children}</Box>;
}

// 파일 종류 판별
function pickKind(file) {
  if (!file) return "empty";
  if (file.type === "folder") return "folder";
  const name = (file.name || "").toLowerCase();
  if (name.endsWith(".doc") || name.endsWith(".docx") || name.endsWith(".odt") || name.endsWith(".rtf") ||
      name.endsWith(".txt") || name.endsWith(".md") || name.endsWith(".hwp") || name.endsWith(".hwpx") ||
      name.endsWith(".xls") || name.endsWith(".xlsx") || name.endsWith(".ppt") || name.endsWith(".pptx"))
    return "office";
  if (name.endsWith(".md") || name.endsWith(".txt")) return "text";
  if (name.endsWith(".pdf")) return "pdf";
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

// DocxHost
function DocxHost({ active, file, onConnectorReady }) {
  const hostRef = useRef(null);
  const editorRef = useRef(null);
  const lastKeyRef = useRef(null);
  const ready = useOnlyOfficeReady();

  const destroy = useCallback(() => {
    try { editorRef.current?.destroyEditor?.(); } catch {}
    editorRef.current = null;
  }, []);

  useEffect(() => {
    if (!ready || !active || !file?.path) return;
    const currentKey = file?.id || file?.path;
    if (lastKeyRef.current === currentKey && editorRef.current) return;

    let cancelled = false;
    (async () => {
      try {
        destroy();
        const el = hostRef.current;
        if (!el) throw new Error("host element missing");
        if (!el.id) el.id = `oo-${Math.random().toString(36).slice(2)}`;

        console.log(file.path)
        const { data } = await api.post("/onlyoffice/config", {
          url: `http://127.0.0.1:8081${file.path}`,
          title: file.name,
        });
        if (cancelled) return;

        const { config, token } = data || {};
        if (!window.DocsAPI?.DocEditor) throw new Error("DocsAPI not ready");

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
                
                // Connector 안정성 체크
                if (typeof connector.executeMethod !== 'function') {
                    console.error("[OO] Connector.executeMethod 누락! Assistant가 작동하지 않을 수 있습니다.");
                    // 이 경우에도 connector를 전달하여 Assistant에서 오류를 확인하도록 함
                }

                // 필드 로딩 보장 (Assistant에서 다시 로드하지만, 초기 확인용)
                setTimeout(() => {
                  connector.executeMethod("GetAllContentControls", null, (fields) => {
                    console.log("[OO] ContentControls (Init):", fields);
                  });
                }, 500); 

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
        height: "100%", 
        background: "#f0f9ff",
      }}
    />
  );
}

// 메인 Editor33
export default function Editor33({ setConnector }) {
  const { selectedFile } = useFileStore();
  const file = useMemo(() => selectedFile || null, [selectedFile]);
  const kind = pickKind(file);
  const isOffice = kind === "office";

  if (!file) return <Pad>왼쪽에서 파일을 선택하세요.</Pad>;
  if (file.type === "folder") return <Pad>폴더가 아니라 파일을 선택해 주세요.</Pad>;

  return (
    <Box sx={{ width: "100%", height: "100%", minHeight: 0 }}>
      <DocxHost active={isOffice} file={file} onConnectorReady={setConnector} />
    </Box>
  );
}