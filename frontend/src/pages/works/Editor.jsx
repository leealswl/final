import React, { useEffect, useMemo, useState } from "react";
import { Box, CircularProgress, Typography } from "@mui/material";
import { useFileStore } from "../../store/useFileStore";
import { useDocumentStore } from "../../store/useDocumentStore";
import TiptapEditor from "../../components/TiptapEditor";

const toAbs = (p) => (p?.startsWith("http") ? p : `http://localhost:8081${p}`);

function Center({ children }) {
  return <Box sx={{ height: "100%", display: "grid", placeItems: "center" }}>{children}</Box>;
}

function Pad({ children }) {
  return <Box sx={{ p: 2, color: "text.secondary" }}>{children}</Box>;
}

function pickKind(file) {
  if (!file) return "empty";
  if (file.type === "folder") return "folder";
  const name = (file.name || "").toLowerCase();
  const mime = (file.mime || "").toLowerCase();
  if (
    name.endsWith(".doc") || name.endsWith(".docx") ||
    name.endsWith(".odt") || name.endsWith(".rtf") ||
    name.endsWith(".hwp") || name.endsWith(".hwpx") ||
    name.endsWith(".xls") || name.endsWith(".xlsx") ||
    name.endsWith(".ppt") || name.endsWith(".pptx")
  ) return "office";
  if (name.endsWith(".md") || name.endsWith(".txt") || mime.startsWith("text/") || mime.includes("markdown")) return "text";
  if (name.endsWith(".pdf") || mime.includes("pdf")) return "pdf";
  if (name.endsWith(".json")) return "json";
  return "unknown";
}

function escapeHtml(text) {
  return text
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#039;");
}

<<<<<<< HEAD
/* 파일 식별 키 (같은 파일 재선택 시 중복 생성 방지) */
const fileKey = (f) => String(f?.id || f?.path || "");

/** DocxHost: OO 편집기 호스트를 항상 같은 div에 유지(언마운트X, display 토글만) */
function DocxHost({ active, file }) {
  const hostRef = React.useRef(null);
  const editorRef = React.useRef(null);
  const lastKeyRef = React.useRef(null);
  const ready = useOnlyOfficeReady();

  const destroy = React.useCallback(() => {
    try { editorRef.current?.destroyEditor?.(); } catch {}
    editorRef.current = null;
  }, []);

  useEffect(() => {
    if (!ready) return;
    if (!active) return;             // 비활성 상태에선 생성하지 않음(숨김만)
    if (!file?.path) return;

    const currentKey = fileKey(file);
    if (lastKeyRef.current === currentKey && editorRef.current) return; // 같은 파일이면 스킵

    let cancelled = false;
    (async () => {
      try {
        // 이전 에디터 정리
        try { editorRef.current?.destroyEditor?.(); } catch {}
        editorRef.current = null;
        //destroy();

        const el = hostRef.current;
        if (!el) throw new Error("host element missing");
        if (!el.id) el.id = `oo-${Math.random().toString(36).slice(2)}`;

        // 백엔드에서 OO config 요청
        const absoluteUrl = `http://127.0.0.1:8081${file.path}`;
        const { data } = await api.post("/onlyoffice/config", {
          url: absoluteUrl,
          title: file.name,
        });
        if (cancelled) return;

        const { config, token } = data || {};
        if (!window.DocsAPI?.DocEditor) throw new Error("DocsAPI not ready");

        const cfg = {
          ...config,
          token,
          width: "100%",
          height: "100%",
          events: {
            onAppReady(){ 
              console.log("[OO] onAppReady"); },
            onDocumentReady(){
              console.log("[OO] onDocumentReady");
              if (typeof window.onDocReady === "function") {
                window.onDocReady();
              }
              // ✅ 문서가 준비된 '이 타이밍'에 커넥터를 만든다
              // 주의: createConnector는 ONLYOFFICE Developer Edition의 유료 기능입니다
              // 무료 버전이나 HWP 파일에서는 작동하지 않을 수 있습니다
              try {
                // mac용 확인
                if (ed && typeof ed.createConnector === 'function') {
                  const conn = ed.createConnector();
                  window.editorBridge = {
                    editor: ed,
                    conn,
                    insert(text) {
                      try {
                        console.log("[editorBridge.insert] called with:", text);
                        this.conn.executeMethod("PasteText", [text]);
                        this.conn.executeMethod("PasteText", ["\n"]);
                        console.log("[OO] insert via connector OK");
                      } catch (e) {
                        console.error("[OO] insert error:", e);
                      }
                    },
                  };
                  console.log("[OO] editorBridge ready");
                } else {
                  // createConnector를 사용할 수 없는 경우 기본 에디터만 제공
                  console.info("[OO] createConnector not available (requires Developer Edition or not supported for this file type)");
                  window.editorBridge = {
                    editor: ed,
                    conn: null,
                    // eslint-disable-next-line no-unused-vars
                    insert(text) {
                      console.warn("[OO] Text insertion not available without connector");
                    }
                  };
                }
              } catch (e) {
                // 에러가 발생해도 에디터는 정상 작동
                console.warn("[OO] connector create failed (this is normal for free edition or HWP files):", e.message);
                window.editorBridge = {
                  editor: ed,
                  conn: null,
                  // eslint-disable-next-line no-unused-vars
                  insert(text) {
                    console.warn("[OO] Text insertion not available without connector");
                  }
                };
              }
            },
            onError(e){
              console.error("[OO] onError:", e);
              console.error("[OO] errorCode:", e?.errorCode);
              console.error("[OO] errorDescription:", e?.errorDescription);
              console.error("[OO] full error object:", JSON.stringify(e, null, 2));
            },
          },
        };
        console.log("[OO] cfg.document.fileType =", cfg?.document?.fileType);     // 'docx' 기대
        console.log("[OO] cfg.documentType =", cfg?.documentType);                // 'word' 기대
        console.log("[OO] cfg.editorConfig.mode =", cfg?.editorConfig?.mode);     // 'edit' 기대
        console.log("[OO] cfg.document.permissions.edit =", cfg?.document?.permissions?.edit); // true 기대
        
        //new edit 
        const ed = new window.DocsAPI.DocEditor(el.id, cfg);
        editorRef.current = ed;  
        lastKeyRef.current = currentKey;
        } catch (e) {
          console.error("[DocxHost] init error:", e);
        }
      })();
    // ✅ 클린업은 여기 (useEffect의 반환값)
    return () => { 
      cancelled = true;
      try { editorRef.current?.destroyEditor?.(); } catch {}
      editorRef.current = null;
      delete window.editorBridge; 
      };
  }, [ready, active, file?.id, file?.path, destroy]);

  // Editor 전체가 언마운트될 때만 완전 파괴
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
=======
function textToHtml(text = "") {
  const lines = escapeHtml(text).split(/\n/g);
  if (!lines.length) return "<p></p>";
  return lines.map((line) => (line.trim() ? `<p>${line}</p>` : "<p><br /></p>")).join("");
>>>>>>> dev
}

function PdfView({ file }) {
  if (!file?.path) return <Pad>PDF 경로가 없습니다.</Pad>;
  const url = toAbs(file.path);
  return (
    <Box sx={{ width: "100%", height: "100%" }}>
      <iframe title="pdf" src={url} style={{ border: "none", width: "100%", height: "100%" }} />
    </Box>
  );
}

export default function Editor() {
  const { selectedFile } = useFileStore();
  const file = useMemo(() => selectedFile || null, [selectedFile]);
  const kind = pickKind(file);

  const { documentId, setDocumentId, content: docContent } = useDocumentStore();

  const [initialContent, setInitialContent] = useState("<p></p>");
  const [loading, setLoading] = useState(false);
  const [loadError, setLoadError] = useState(null);

  useEffect(() => {
    if (!file || file.type === "folder") {
      setInitialContent("<p></p>");
      setLoading(false);
      setLoadError(null);
      return;
    }

    setDocumentId(file.id);

    if (file.meta?.isDraft) {
      setInitialContent(docContent || "<p></p>");
      setLoading(false);
      setLoadError(null);
      return;
    }

    if (kind === "pdf" || kind === "unknown") {
      setInitialContent("<p></p>");
      setLoading(false);
      setLoadError(null);
      return;
    }

    if (!file.path || kind === "office") {
      setInitialContent("<p></p>");
      setLoading(false);
      setLoadError(null);
      return;
    }

    if (kind === "json") {
  setLoading(true);
  setLoadError(null);
  let cancelled = false;

  fetch(toAbs(file.path))
    .then(async (res) => {
      if (!res.ok) throw new Error(res.statusText || "JSON 파일을 불러오지 못했습니다.");
      const jsonData = await res.json(); // JSON 파싱
      if (!cancelled) setInitialContent(jsonData);
    })
    .catch((error) => {
      console.warn("[Editor] JSON 로드 실패", error);
      if (!cancelled) {
        setInitialContent({ type: "doc", content: [] });
        setLoadError("JSON 파일 로드를 실패했습니다. 빈 문서로 시작합니다.");
      }
    })
    .finally(() => {
      if (!cancelled) setLoading(false);
    });

  return () => { cancelled = true; };
}


    let cancelled = false;
    setLoading(true);
    setLoadError(null);

    fetch(toAbs(file.path))
      .then(async (res) => {
        if (!res.ok) throw new Error(res.statusText || "파일을 불러오지 못했습니다.");
        const txt = await res.text();
        if (!cancelled) setInitialContent(textToHtml(txt));
      })
      .catch((error) => {
        console.warn("[Editor] 콘텐츠 로드 실패", error);
        if (!cancelled) {
          setInitialContent("<p></p>");
          setLoadError("파일 내용을 불러오지 못했습니다. 빈 문서로 시작합니다.");
        }
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });

    return () => {
      cancelled = true;
    };
  }, [file, kind, docContent, setDocumentId]);

  if (!file) return <Pad>왼쪽에서 파일을 선택하세요.</Pad>;
  if (file.type === "folder") return <Pad>폴더가 아니라 파일을 선택해 주세요.</Pad>;

  if (kind === "pdf") return <PdfView file={file} />;

  if (kind === "unknown")
    return (
      <Pad>
        미지원 형식입니다. (권장: DOCX / MD / TXT / PDF)
        <Box sx={{ mt: 1, fontSize: 12 }}>
          선택된 파일: <b>{file.name}</b> ({file.mime || "unknown"})
        </Box>
        {file.path && (
          <Box sx={{ mt: 1 }}>
            <a href={toAbs(file.path)} target="_blank" rel="noreferrer">
              원본 열기
            </a>
          </Box>
        )}
      </Pad>
    );

  return (
    <Box sx={{ width: "100%", height: "100%", display: "flex", flexDirection: "column" }}>
      {loading && <Center><CircularProgress size={24} /></Center>}
      {!loading && loadError && (
        <Box sx={{ px: 2, py: 1, bgcolor: "#fff4e5", color: "#8a6d3b", borderBottom: "1px solid #f0deb4" }}>
          {loadError}
        </Box>
      )}
      <Box sx={{ flex: 1, minHeight: 0 }}>
        <TiptapEditor
          initialContent={initialContent}
          contentKey={file.id}
          onContentChange={(html) => setInitialContent(html)}
          readOnly={false}
        />
      </Box>
      <Box sx={{ px: 2, py: 1, borderTop: "1px solid #e5e7eb", bgcolor: "#fafafa" }}>
        <Typography variant="caption" color="text.secondary">
          Heading 레벨, 목록, 표 삽입과 AI 다듬기가 지원됩니다. 변경 사항 저장 로직은 추후 연동이 필요합니다.
        </Typography>
      </Box>
    </Box>
  );
}
