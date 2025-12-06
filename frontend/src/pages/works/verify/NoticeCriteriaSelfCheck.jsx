import React from "react";
import { Box, Card, CardContent, Typography, Stack, Chip, LinearProgress } from "@mui/material";
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, LabelList, Cell } from "recharts";

const COLORS = ["#4CAF50", "#2196F3", "#FF9800", "#F44336", "#9C27B0", "#009688"];

export function NoticeCriteriaChart({ items = [], height = 320, yWidth = 160 }) {
  if (!Array.isArray(items) || items.length === 0) return null;

  const maxScore = Math.max(...items.map((i) => Number(i.max_score))) || 1;
  const chartData = items.map((item) => ({
    name: item.name,
    score: Number(item.score),
    label: `${item.score} / ${item.max_score}`,
  }));

  return (
    <Box sx={{ width: "100%", height }}>
      <ResponsiveContainer width="100%" height="100%">
        <BarChart data={chartData} layout="vertical" margin={{ left: 20, right: 25 }}>
          <XAxis type="number" domain={[0, maxScore]} />
          <YAxis type="category" dataKey="name" width={yWidth} />
          <Tooltip formatter={(_, __, d) => d.payload.label} />
          <Bar dataKey="score" radius={[6, 6, 6, 6]}>
            {chartData.map((entry, index) => (
              <Cell key={index} fill={COLORS[index % COLORS.length]} />
            ))}
            <LabelList dataKey="label" position="right" style={{ fontSize: 13, fontWeight: 600 }} />
          </Bar>
        </BarChart>
      </ResponsiveContainer>
    </Box>
  );
}

export default function NoticeCriteriaSelfCheck({ data }) {
  if (!data) return null;

  // 응답 객체에 data가 한 번 더 감싸져 있을 때도 처리
  const root = data.data ? data.data : data;
  const { block_name, total_score, total_max_score, percent, items = [] } = root;

  if (!Array.isArray(items) || items.length === 0) {
    console.warn("NoticeCriteriaSelfCheck: items 없음 → root:", root);
    return null;
  }

  const percentValue =
    typeof percent === "number"
      ? percent
      : total_max_score
      ? Math.round((Number(total_score) / Number(total_max_score || 1)) * 100)
      : 0;

  return (
    <Box sx={{ mt: 3, display: "flex", flexDirection: "column", gap: 3 }}>
      <Card>
        <CardContent>
          <Stack direction={{ xs: "column", md: "row" }} spacing={4}>
            <Box sx={{ flex: 1 }}>
              <Typography variant="h6" sx={{ fontWeight: 700 }}>
                {block_name || "공고문 평가기준 자가진단"}
              </Typography>

              <Typography sx={{ mt: 1, color: "text.secondary" }}>
                평가기준에 따라 초안을 분석한 결과입니다.
              </Typography>

              <Box
                sx={{
                  mt: 2,
                  p: 2,
                  borderRadius: 1,
                  bgcolor: "rgba(25,118,210,0.05)",
                }}
              >
                <Typography variant="body2" sx={{ whiteSpace: "pre-line" }}>
                  · 초안 충족률 <b>{percentValue}%</b>
                  <br />
                  · 총점 {total_score} / {total_max_score}
                </Typography>
              </Box>
            </Box>

            <Box sx={{ width: 260, textAlign: "center" }}>
              <Typography variant="h3" sx={{ fontWeight: 800 }}>
                {percentValue}%
              </Typography>
              <Typography sx={{ color: "text.secondary" }}>
                평가기준 달성도
              </Typography>

              <LinearProgress
                variant="determinate"
                value={percentValue}
                sx={{ mt: 2, height: 10, borderRadius: 999 }}
              />

              <Chip sx={{ mt: 1.5 }} label={`총점 ${total_score} / ${total_max_score}`} />
            </Box>
          </Stack>
        </CardContent>
      </Card>

      {/* <Card>
        <CardContent>
          <Typography variant="h6" sx={{ fontWeight: 700, mb: 2 }}>
            평가기준별 진단 점수
          </Typography>
          <NoticeCriteriaChart items={items} />
        </CardContent>
      </Card> */}
    </Box>
  );
}
