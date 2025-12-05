import React from "react";
import {
  Box, Card, CardContent, Typography, Stack, Chip, LinearProgress
} from "@mui/material";

import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
  LabelList,
} from "recharts";

export default function NoticeCriteriaSelfCheck({ data }) {
  if (!data) return null;

  // ⚡ data.data 안에 실제 결과가 있는 구조를 자동 인식
  const root = data.data ? data.data : data;

  const {
    block_name,
    total_score,
    total_max_score,
    percent,
    items = [],
  } = root;

  if (!Array.isArray(items) || items.length === 0) {
    console.warn("⚠️ NoticeCriteriaSelfCheck: items 없음 → root:", root);
    return null;
  }

  // 최대 점수 계산
  const maxScore = Math.max(...items.map(i => Number(i.max_score))) || 1;

  // 차트 데이터 구성
  const chartData = items.map(item => ({
    name: item.name,
    score: Number(item.score),
    label: `${item.score} / ${item.max_score}점`,
  }));

  return (
    <Box sx={{ mt: 3, display: "flex", flexDirection: "column", gap: 3 }}>

      {/* 상단 요약 카드 */}
      <Card>
        <CardContent>
          <Stack direction={{ xs: "column", md: "row" }} spacing={4}>
            {/* 왼쪽 설명 */}
            <Box sx={{ flex: 1 }}>
              <Typography variant="h6" sx={{ fontWeight: 700 }}>
                {block_name || "공고문 평가기준 자가진단"}
              </Typography>

              <Typography sx={{ mt: 1, color: "text.secondary" }}>
                평가기준을 기반으로 초안의 충족도를 분석한 결과입니다.
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
                  · 초안 충족률: <b>{percent}%</b>
                  <br />
                  · 총점 {total_score} / {total_max_score}
                </Typography>
              </Box>
            </Box>

            {/* 오른쪽 요약 숫자 */}
            <Box sx={{ width: 260, textAlign: "center" }}>
              <Typography variant="h3" sx={{ fontWeight: 800 }}>
                {percent}%
              </Typography>
              <Typography sx={{ color: "text.secondary" }}>
                평가기준 달성도
              </Typography>

              <LinearProgress
                variant="determinate"
                value={percent}
                sx={{ mt: 2, height: 10, borderRadius: 999 }}
              />

              <Chip
                sx={{ mt: 1.5 }}
                label={`총점 ${total_score} / ${total_max_score}`}
              />
            </Box>
          </Stack>
        </CardContent>
      </Card>

      {/* 가로 바 차트 */}
      <Card>
        <CardContent>
          <Typography variant="h6" sx={{ fontWeight: 700, mb: 2 }}>
            평가기준별 진단 점수
          </Typography>

          <Box sx={{ width: "100%", height: 320 }}>
            <ResponsiveContainer width="100%" height="100%">
              <BarChart
                data={chartData}
                layout="vertical"
                margin={{ left: 20, right: 25 }}
              >
                <XAxis type="number" domain={[0, maxScore]} />
                <YAxis type="category" dataKey="name" width={160} />

                <Tooltip formatter={(_, __, d) => d.payload.label} />

                <Bar dataKey="score" fill="#4CAF50" radius={[6, 6, 6, 6]}>
                  <LabelList
                    dataKey="label"
                    position="right"
                    style={{ fontSize: 13, fontWeight: 600 }}
                  />
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          </Box>
        </CardContent>
      </Card>

    </Box>
  );
}
