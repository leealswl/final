import React from "react";
import { Box, Typography } from "@mui/material";
import { useFileStore } from "../../../../store/useFileStore";

export default function Assistant() {
  const { selectedFile } = useFileStore();
  return (
    <Box sx={{ height: "100%", p: 2 }}>
      <Typography variant="subtitle2" gutterBottom>AI Assistant</Typography>
      <Typography variant="body2" color="text.secondary">
        {selectedFile ? `현재 문서 기준으로 분석 준비: ${selectedFile.name}` : "문서를 선택하면 분석을 시작할 수 있어요."}
      </Typography>
    </Box>
  );
}
