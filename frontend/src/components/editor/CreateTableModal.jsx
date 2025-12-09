import React, { useState } from "react";
import {
  Box,
  Button,
  Dialog,
  DialogActions,
  DialogContent,
  DialogTitle,
  FormControl,
  FormControlLabel,
  InputLabel,
  MenuItem,
  Select,
  Switch,
  Typography,
} from "@mui/material";

const ROW_OPTIONS = [3, 4, 5, 6, 7, 8];
const COL_OPTIONS = [2, 3, 4, 5, 6];

export default function CreateTableModal({ open, onClose, onCreate }) {
  const [rows, setRows] = useState(5);
  const [cols, setCols] = useState(4);
  const [hasHeader, setHasHeader] = useState(true);

  const handleCreate = () => {
    if (rows <= 0 || cols <= 0) return;
    onCreate?.({ rows, cols, withHeaderRow: hasHeader });
    onClose?.();
  };

  const handleCancel = () => {
    onClose?.();
  };

  return (
    <Dialog open={open} onClose={handleCancel} maxWidth="xs" fullWidth>
      <DialogTitle>표 만들기</DialogTitle>
      <DialogContent>
        <Box sx={{ display: "grid", gap: 2, pt: 1 }}>
          <Typography variant="body2" color="text.secondary">
            원하는 행·열 개수를 입력한 뒤 "만들기"를 눌러 주세요.
          </Typography>

          <Box sx={{ display: "flex", gap: 2 }}>
            <FormControl fullWidth size="small">
              <InputLabel id="rows-label">행 개수</InputLabel>
              <Select
                labelId="rows-label"
                label="행 개수"
                value={rows}
                onChange={(event) => setRows(Number(event.target.value))}
              >
                {ROW_OPTIONS.map((option) => (
                  <MenuItem key={option} value={option}>
                    {option}
                  </MenuItem>
                ))}
              </Select>
            </FormControl>

            <FormControl fullWidth size="small">
              <InputLabel id="cols-label">열 개수</InputLabel>
              <Select
                labelId="cols-label"
                label="열 개수"
                value={cols}
                onChange={(event) => setCols(Number(event.target.value))}
              >
                {COL_OPTIONS.map((option) => (
                  <MenuItem key={option} value={option}>
                    {option}
                  </MenuItem>
                ))}
              </Select>
            </FormControl>
          </Box>

          <FormControlLabel
            control={<Switch checked={hasHeader} onChange={(event) => setHasHeader(event.target.checked)} />}
            label="첫 행을 머리글로 사용"
          />
        </Box>
      </DialogContent>
      <DialogActions>
        <Button onClick={handleCancel}>취소</Button>
        <Button onClick={handleCreate} variant="contained">
          만들기
        </Button>
      </DialogActions>
    </Dialog>
  );
}
