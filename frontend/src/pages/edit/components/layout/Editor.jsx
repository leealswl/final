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
  console.log("name: ", name);
  if (name.endsWith(".docx") || mime.includes("officedocument.wordprocessingml.document")) return "docx";
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

/* DOCX 뷰 (OnlyOffice) — file.path 사용 */
function DocxView({ file }) {
  const hostRef = React.useRef(null);
  const editorRef = React.useRef(null);
  const constructedRef = React.useRef(false);
  const [status, setStatus] = useState("idle"); // idle | loading | error
  const [debug, setDebug] = useState("");
  const ready = useOnlyOfficeReady();

  useEffect(() => {
    console.log("editor useeffect 실행");
    let cancelled = false;
    if (!file || !ready) return;

    const waitForSize = (el, tries = 40) =>
      new Promise((resolve, reject) => {
        const tick = () => {
          if (cancelled) return;
          if (!el) return reject(new Error("host element null"));
          const r = el.getBoundingClientRect();
          const cs = getComputedStyle(el);
          if (r.width >= 10 && r.height >= 10 && cs.display !== "none" && cs.visibility !== "hidden")
            return resolve(true);
          if (tries-- <= 0) return reject(new Error(`host size zero: ${r.width}x${r.height}`));
          setTimeout(tick, 50);
        };
        tick();
      });

    (async () => {
      try {
        setStatus("loading");
        const el = hostRef.current;
        console.log("el: ", el);
        if (el && !el.id) el.id = `onlyoffice-${file.id || Math.random().toString(36).slice(2)}`;
        await waitForSize(el);

        // 백엔드에 문서 절대 URL 전달해서 config 받기
        // 프론트는 5173, 백엔드는 8081에서 정적 파일 제공하므로 8081 기준으로 조립
        console.log("editor 실행")
        const absoluteUrl = `http://127.0.0.1:8081${file.path}`;
        console.log("absoluteUrl: ", absoluteUrl);
        console.log("filepath: ", file.path);
        setDebug("config 요청…");
        const { data } = await api.post("/onlyoffice/config", {
          url: absoluteUrl,
          title: file.name,
        });

        console.log("data: ", data)
        console.log("url: ", data.config.document.url)
        const { config, token } = data || {};

        console.log("config: ", config)

        console.log("window.DocsAPI: ", window.DocsAPI);
        if (!window.DocsAPI?.DocEditor) throw new Error("DocsAPI 미준비");
        if (constructedRef.current) {
          setDebug((d) => d + " | already constructed(skip)");
          setStatus("idle");
          return;
        }

        const cfg = {
          ...config,
          token,
          width: "100%",
          height: "100%",
          events: {
            onAppReady() { console.log("[OO] onAppReady"); },
            onDocumentReady() { console.log("[OO] onDocumentReady"); },
            onError(e) {
              try { console.error("[OO] onError:", e, e?.data ? JSON.stringify(e.data) : ""); }
              catch(_) { console.error("[OO] onError (raw):", e); }
            },
          },
        };

        console.log("el.id:", el.id);
        console.log("cfg:", cfg);

        editorRef.current = new window.DocsAPI.DocEditor(el.id, cfg);
        console.log("editorRef.current: ", editorRef.current)
        constructedRef.current = true;
        setStatus("idle");
        console.log("status: ", status);
      } catch (e) {
        console.error("[DocxView] init error:", e);
        setDebug(`init error: ${e?.message || e}`);
        setStatus("error");
      }
    })();

    return () => {
      cancelled = true;
      console.log()
      try { editorRef.current?.destroyEditor?.(); } catch {}
      constructedRef.current = false;
    };
  }, [file, ready]);

  console.log("hostRef: ", hostRef);
  console.log("hostRef.current: ", hostRef.current);

  if (status === "loading") {
    return (
      <Center>
        <Box sx={{ display: "flex", alignItems: "center", gap: 1 }}>
          <CircularProgress size={20} /> <span>OnlyOffice 로딩 중…</span>
        </Box>
      </Center>
    );
  }
  if (status === "error") {
    return <Pad>OnlyOffice 초기화 실패: {debug}</Pad>;
  }

  return <Box ref={hostRef} sx={{ width: "100%", height: "100%" }} />;
}

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

  console.log("file: ", file)

  if (!file) return <Pad>왼쪽에서 파일을 선택하세요.</Pad>;
  if (file.type === "folder") return <Pad>폴더가 아니라 파일을 선택해 주세요.</Pad>;

  return (
    <Box sx={{ width: "100%", minHeight: "85vh" }}>
      {kind === "docx" && (
        <Box sx={{ width: "100%", height: "100vh", bgcolor: '#f0f9ff' }}>
          <DocxView file={file} />
        </Box>
      )}
      {kind === "text" && <TextView file={file} />}
      {kind === "pdf" && (
        <Box sx={{ width: "100%", height: "100vh" }}>
          <PdfView file={file} />
        </Box>
      )}
      {!(kind === "docx" || kind === "text" || kind === "pdf") && (
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
