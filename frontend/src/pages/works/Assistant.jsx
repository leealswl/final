import React, { useState } from "react";
import { Box, Button, TextField } from "@mui/material";

export default function Assistant() {
  const [input, setInput] = useState("");

  const handleAI = async () => {
    const text = `${input}`.trim();
    const editor = window.tiptapEditor;

    if (!editor) {
      console.warn("[Assistant] Tiptap editor not ready.");
      return;
    }

    if (!text) {
      console.warn("[Assistant] 추가할 내용이 없습니다.");
      return;
    }

    editor.chain().focus().insertContent(`${text}\n`).run();
    setInput("");
  };


  return (
    <Box sx={{ p: 2, display: "grid", gap: 1 }}>
      <TextField
        label="온리오피스에 전달할 내용"
        value={input}
        onChange={(e) => setInput(e.target.value)}
        multiline
        minRows={4}
      />
      <Button
        variant="contained"
        onClick={handleAI}
        disabled={!window.tiptapEditor}
      >
        문서에 넣기
      </Button>
    </Box>
  );
}
