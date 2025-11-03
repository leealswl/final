import React, { useState } from "react";
import { Box, Button,TextField  } from "@mui/material";

export default function Assistant() {
  const [input, setInput] = useState("");

  const handleAI = async () => {
    const text = `${input}`;
    console.log("[Assistant] clicked. editorBridge =", window.editorBridge);
    if (!window.editorBridge) {
      console.warn("[Assistant] editorBridge not ready (문서가 아직 안 떴거나 에러).");
      return;
    }
    try {
      window.editorBridge.insert(text);
      console.log("[Assistant] insert requested.");
    } catch (e) {
      console.error("[Assistant] insert error:", e);
    }
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
        disabled={!window.editorBridge?.insert}
      >
        문서에 넣기
      </Button>
    </Box>
  );
}
