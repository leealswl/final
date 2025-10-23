import React, { useEffect, useMemo, useRef, useState } from "react";
import { Box, CircularProgress, TextField } from "@mui/material";
import { useFileStore } from "../../../../store/useFileStore";
import api from "../../../../utils/api";


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
  if (name.endsWith(".docx") || mime.includes("officedocument.wordprocessingml.document")) return "docx";
  if (name.endsWith(".md") || name.endsWith(".txt") || mime.startsWith("text/") || mime.includes("markdown")) return "text";
  if (name.endsWith(".pdf") || mime.includes("pdf")) return "pdf";
  return "unknown";
}

/* OnlyOffice api.js 로드 */
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

/* DOCX 뷰 (OnlyOffice) — DOM element로 attach + 컨테이너 크기 보장 */
function DocxView({ fileId }) {
  const hostRef = React.useRef(null);
  const editorRef = React.useRef(null);
  const constructedRef = React.useRef(false);
  const [status, setStatus] = React.useState("idle"); // idle | loading | error
  const [debug, setDebug] = React.useState("");

  // api.js 로드 + DocsAPI 준비 대기
  React.useEffect(() => {
    let cancelled = false;

    const loadApi = () =>
      new Promise((resolve, reject) => {
        if (window.DocsAPI?.DocEditor) return resolve(true);
        const src = import.meta.env.VITE_ONLYOFFICE_SRC;
        if (!src) return reject(new Error("VITE_ONLYOFFICE_SRC 미설정"));
        const s = document.createElement("script");
        s.src = src; s.async = true;
        s.onload = resolve;
        s.onerror = () => reject(new Error("OnlyOffice API 로드 실패: " + src));
        document.body.appendChild(s);
      });

    const waitForDocsApi = (tries = 40) =>
      new Promise((resolve, reject) => {
        const tick = () => {
          if (cancelled) return;
          if (window.DocsAPI?.DocEditor) return resolve(true);
          if (tries-- <= 0) return reject(new Error("DocsAPI 준비 실패"));
          setTimeout(tick, 50);
        };
        tick();
      });

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
        setDebug("api.js 로드…");
        await loadApi();
        await waitForDocsApi();

        const el = hostRef.current;
        // 컨테이너에 id 보장
        if (el && !el.id) el.id = `onlyoffice-${fileId}`;
        await waitForSize(el);

        setDebug("config 요청…");
        const { data } = await api.get(`/onlyoffice/config/${fileId}`);
        const { config, token } = data;

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

        // ★ 안전모드: id 문자열로 attach (타이밍 문제 우회)
        editorRef.current = new window.DocsAPI.DocEditor(el.id, cfg);
        constructedRef.current = true;
        setDebug((d) => d + " | constructed");
      } catch (e) {
        console.error("[DocxView] init error:", e);
        setDebug(`init error: ${e?.message || e}`);
        setStatus("error");
      }
    })();

    return () => {
      cancelled = true;
      try { editorRef.current?.destroyEditor?.(); } catch {}
      constructedRef.current = false;
    };
  }, [fileId]);

  return (
    <Box sx={{ display: "flex", flexDirection: "column", height: "100%" }}>
      {/* <Box sx={{ p: 1, fontSize: 12, borderBottom: "1px solid #eee", color: status === "error" ? "error.main" : "#4b5563" }}>
        {status === "loading" ? "로딩 중…" :
          status === "error"   ? `에디터 초기화 실패 — ${debug}` :
                                `상태 OK${debug ? " — " + debug : ""}`}
      </Box> */}
      <Box
        ref={hostRef}
        id="onlyoffice-host"
        sx={{ flex: 1, minHeight: 780, position: "relative" }}
      />
    </Box>
  );
}



/* 텍스트 뷰 (md/txt) */
function TextView({ fileId }) {
  const [value, setValue] = useState("");
  const [saving, setSaving] = useState("idle"); // idle | saving | saved

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
        minRows={8}
        sx={{ flex: 1, "& .MuiInputBase-root": { height: "100%" } }}
      />
    </Box>
  );
}

/* PDF 뷰 */
function PdfView({ url }) {
  if (!url) return <Pad>PDF 주소가 없습니다.</Pad>;
  return (
    <Box sx={{ width: "100%", height: "100%" }}>
      <iframe title="pdf" src={url} style={{ border: "none", width: "100%", height: "100%" }} />
    </Box>
  );
}

/* 메인 Editor */
export default function Editor() {
  const { selectedFile } = useFileStore();
  const [meta, setMeta] = useState(null);
  const file = useMemo(() => selectedFile || null, [selectedFile]);

  useEffect(() => {
    setMeta(null);
    if (!file || file.type === "folder") return;

    const isDocx =
      (file.name || "").toLowerCase().endsWith(".docx") ||
      (file.mime || "").toLowerCase().includes("officedocument.wordprocessingml.document");

    if (isDocx) { setMeta(file); return; }

    (async () => {
      try {
        const { data } = await api.get(`/files/${file.id}`);
        setMeta({ ...file, ...data });
      } catch { setMeta(file); }
    })();
  }, [file]);

  const kind = pickKind(meta || file);
  console.log("[Editor] selected:", file?.id, file?.name, "kind:", kind);

  if (!file) return <Pad>왼쪽에서 파일을 선택하세요.</Pad>;
  if (file.type === "folder") return <Pad>폴더를 선택했습니다. 파일을 선택해 주세요.</Pad>;

  return (
    <Box sx={{ width: "100%", minHeight: "85vh" }}>
      {kind === "docx" && (
        // ★ 부모 박스에 확실한 높이 부여 (height: 80vh)
        <Box sx={{ width: "100%", height: "100vh", bgcolor: '#f0f9ff' }}>
          <DocxView fileId={file.id} />
        </Box>
      )}
      {kind === "text" && <TextView fileId={file.id} />}
      {kind === "pdf" && <PdfView url={(meta || file)?.public_url} />}
      {!(kind === "docx" || kind === "text" || kind === "pdf") && (
        <Pad>
          미지원 형식입니다. (권장: DOCX / MD / TXT / PDF)
          <Box sx={{ mt: 1, fontSize: 12 }}>
            선택된 파일: <b>{file.name}</b> ({file.mime || "unknown"})
          </Box>
        </Pad>
      )}
    </Box>
  );
}
