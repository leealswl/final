import React, { useEffect, useMemo, useState } from "react";
import { Box, CircularProgress, TextField } from "@mui/material";
import { useFileStore } from "../../../../store/useFileStore";
import api from "../../../../utils/api";


// 파일 최상단 근처에 추가
const toAbs = (p) => (p?.startsWith('http') ? p : `http://127.0.0.1:8081${p}`);
/* 공용 UI */
function Center({ children }) {
  return <Box sx={{ height: "100%", display: "grid", placeItems: "center" }}>{children}</Box>;
}
function Pad({ children }) {
  return <Box sx={{ p: 2, color: "text.secondary" }}>{children}</Box>;
}

/* 파일 타입 판별 */
function pickKind(file) {
  if (!file) return "empty";
  if (file.type === "folder") return "folder";
  const name = (file.name || "").toLowerCase();
  const mime = (file.mime || "").toLowerCase();
  //console.log("name: ", name);
  if (
    name.endsWith(".doc") || name.endsWith(".docx") || name.endsWith(".odt") || name.endsWith(".rtf") ||
    name.endsWith(".txt") || name.endsWith(".md") ||
    name.endsWith(".hwp") || name.endsWith(".hwpx") ||
    name.endsWith(".xls") || name.endsWith(".xlsx") ||
    name.endsWith(".ppt") || name.endsWith(".pptx")
  ) return "office";
  if (name.endsWith(".md") || name.endsWith(".txt") || mime.startsWith("text/") || mime.includes("markdown")) return "text";
  if (name.endsWith(".pdf") || mime.includes("pdf")) return "pdf";
  return "unknown";
}

/* OnlyOffice api.js 로더 */
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
        destroy();

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
            onAppReady()    { console.log("[OO] onAppReady"); },
            onDocumentReady(){ console.log("[OO] onDocumentReady"); },
            onError(e)      { console.error("[OO] onError:", e); },
          },
        };

        editorRef.current = new window.DocsAPI.DocEditor(el.id, cfg);
        lastKeyRef.current = currentKey;
      } catch (e) {
        console.error("[DocxHost] init error:", e);
      }
    })();

    return () => { cancelled = true; };
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
}

// function DocxView({ file }) {
//   const hostRef = React.useRef(null);
//   const editorRef = React.useRef(null);
//   const constructedRef = React.useRef(false);
//   const [status, setStatus] = useState("idle"); // idle | loading | error
//   const [debug, setDebug] = useState("");
//   const ready = useOnlyOfficeReady();

//   useEffect(() => {
//     if (!file || !ready) return;

//     let cancelled = false;

//     const waitForSize = (el, tries = 40) =>
//       new Promise((resolve, reject) => {
//         const tick = () => {
//           if (cancelled) return;
//           if (!el) return reject(new Error("host element null"));
//           const r = el.getBoundingClientRect();
//           const cs = getComputedStyle(el);
//           if (r.width >= 10 && r.height >= 10 && cs.display !== "none" && cs.visibility !== "hidden")
//             return resolve(true);
//           if (tries-- <= 0) return reject(new Error(`host size zero: ${r.width}x${r.height}`));
//           setTimeout(tick, 50);
//         };
//         tick();
//       });

//     const initEditor = async () => {
//       try {
//         setStatus("loading");

//         // hostRef.current가 존재할 때까지 기다림
//         const el = hostRef.current;
//         if (!el) throw new Error("hostRef.current is null");
//         await waitForSize(el);

//         const hostId = `onlyoffice-${(file.id || file.path || 'noid')}`;
//         if (!el.id) el.id = hostId;

//         // 백엔드 config 요청
//         const absoluteUrl = `http://127.0.0.1:8081${file.path}`;
//         setDebug("config 요청…");
//         const { data } = await api.post("/onlyoffice/config", {
//           url: absoluteUrl,
//           title: file.name,
//         });
//         const { config, token } = data;

//         if (!window.DocsAPI?.DocEditor) throw new Error("DocsAPI 미준비");
//         if (constructedRef.current) {
//           setDebug((d) => d + " | already constructed(skip)");
//           setStatus("idle");
//           return;
//         }

//         const cfg = {
//           ...config,
//           token,
//           width: "100%",
//           height: "100%",
//           events: {
//             onAppReady() { console.log("[OO] onAppReady"); },
//             onDocumentReady() { console.log("[OO] onDocumentReady"); },
//             onError(e) {
//               console.error("[OO] onError:", e, e?.data ? JSON.stringify(e.data) : "");
//             },
//           },
//         };

//         editorRef.current = new window.DocsAPI.DocEditor(el.id, cfg);
//         constructedRef.current = true;
//         setStatus("idle");
//       } catch (e) {
//         console.error("[DocxView] init error:", e);
//         setDebug(`init error: ${e?.message || e}`);
//         setStatus("error");
//       }
//     };

//     // DOM이 렌더링될 때까지 다음 tick에서 실행
//     const id = setTimeout(() => initEditor(), 0);

//     return () => {
//       cancelled = true;
//       try { editorRef.current?.destroyEditor?.(); } catch {}
//         editorRef.current = null;
//       constructedRef.current = false;
//       clearTimeout(id);
//     };
//   }, [ready, file?.id, file?.path]);

//   if (status === "loading") {
//     return (
//       <Center>
//         <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
//           <CircularProgress size={20} /> <span>OnlyOffice 로딩 중…</span>
//         </div>
//       </Center>
//     );
//   }
//   if (status === "error") {
//     return <Pad>OnlyOffice 초기화 실패: {debug}</Pad>;
//   }

//   return <Box ref={hostRef} style={{ width: '100%', height: '600px' }} />;
// }


/* 텍스트 뷰 (md/txt) — file.path에서 직접 읽기 (읽기 전용) */
function TextView({ file }) {
  const [value, setValue] = useState("");
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let ignore = false;
    (async () => {
      try {
        setLoading(true);
        const res = await fetch(toAbs(file.path));
        const txt = await res.text();
        if (!ignore) setValue(txt);
      } catch (e) {
        console.error(e);
        if (!ignore) setValue("(불러오기 실패)");
      } finally {
        if (!ignore) setLoading(false);
      }
    })();
    return () => { ignore = true; };
  }, [file?.path]);

  if (loading) return <Center><CircularProgress size={20} /></Center>;
  return (
    <TextField
      value={value}
      onChange={() => {}}
      fullWidth
      multiline
      minRows={12}
      sx={{ "& .MuiInputBase-root": { fontFamily: "monospace" } }}
      helperText="읽기 전용 미리보기 (서버 저장 API 없어서 수정은 비활성)"
    />
  );
}

/* PDF 뷰 — file.path 직접 사용 */
function PdfView({ file }) {
  if (!file?.path) return <Pad>PDF 경로가 없습니다.</Pad>;
    const url = toAbs(file.path);
  return (
    <Box sx={{ width: "100%", height: "100%" }}>
      <iframe title="pdf" src={url} style={{ border: "none", width: "100%", height: "100%" }} />
    </Box>
  );
}


/* 메인 Editor */
export default function Editor() {
  const { selectedFile } = useFileStore();
  const file = useMemo(() => selectedFile || null, [selectedFile]);
  const kind = pickKind(file);
  const isOffice = kind === 'office';


  console.log("file: ", file)

  if (!file) return <Pad>왼쪽에서 파일을 선택하세요.</Pad>;
  if (file.type === "folder") return <Pad>폴더가 아니라 파일을 선택해 주세요.</Pad>;

  return (
    <Box sx={{ width: "100%",height:"100%", minHeight: 0}}>
      {/* ✅ 항상 DOM에 남아 있게 */}
      <DocxHost active={isOffice} file={file} />

      {/* office가 아닐 때만 다른 뷰들 조건부 렌더 */}
      {!isOffice && kind === "text" && <TextView file={file} />}
      {!isOffice && kind === "pdf" && (
        <Box sx={{ width: "100%", height: "100vh" }}>
          <PdfView active={isOffice} file={file} />
        </Box>
      )}

      {!isOffice && !["text", "pdf"].includes(kind) && (
        <Pad>
          미지원 형식입니다. (권장: DOCX / MD / TXT / PDF)
          <Box sx={{ mt: 1, fontSize: 12 }}>
            선택된 파일: <b>{file.name}</b> ({file.mime || "unknown"})
          </Box>
          {file.path && (
            <Box sx={{ mt: 1 }}>
              <a href={toAbs(file.path)} target="_blank" rel="noreferrer">원본 열기</a>
            </Box>
          )}
        </Pad>
      )}
    </Box>
  );
}
