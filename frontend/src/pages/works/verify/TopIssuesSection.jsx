import React, { useMemo } from "react";
import {
  Card,
  CardContent,
  Typography,
  Chip,
  Stack,
  List,
  ListItem,
  ListItemText,
  Box,
} from "@mui/material";
import WarningAmberIcon from "@mui/icons-material/WarningAmber";

import { buildNormalizedMissingFeatureList } from "../../../utils/verifyUtils";

const SEVERITY_COLORS = { LOW: "#4caf50", MEDIUM: "#ffb300", HIGH: "#f44336" };
const SEVERITY_LABELS = {
  LOW: "위험도 낮음",
  MEDIUM: "위험도 보통",
  HIGH: "위험도 높음",
};

export default function TopIssuesSection({ results, compareResult }) {
  const hasLaw = results && Object.keys(results).length > 0;
  const hasCompare = !!compareResult;

  const items = useMemo(() => {
    const list = [];

    // --------------------------
    // 1) 법령 missing, violations
    // --------------------------
    if (hasLaw) {
      Object.entries(results).forEach(([_, r]) => {
        if (!r) return;

        if (Array.isArray(r.missing)) {
          r.missing.forEach((m) => {
            list.push({
              type: "LAW_MISSING",
              focusLabel: r.label,
              text: m,
              severity: r.risk_level || "MEDIUM",
              source: r.label, // 어떤 검증 관점인지
              impact: "관련 법령 요건 미준수로 부적합 판단 가능",
            });
          });
        }

        if (Array.isArray(r.violations)) {
          r.violations.forEach((v) => {
            list.push({
              type: "LAW_VIOLATION",
              focusLabel: r.label,
              text: v.reason || v.recommendation || "",
              law: v.law_name,
              article: v.article_title,
              severity: v.severity || "HIGH",
              source: `${v.law_name} · ${v.article_title}`, // 법령 출처 표시
              impact: "법령 위반 가능성이 있어 심사에서 중대한 감점 요소",
            });
          });
        }
      });
    }

    // --------------------------
    // 2) 공고문 누락/조건 부족
    // --------------------------
    if (hasCompare) {
      const missingSections = compareResult?.missing_sections || [];
      const rawMissingFeatures = compareResult?.feature_mismatch || [];
      const normalizedMissingFeatures =
        buildNormalizedMissingFeatureList(rawMissingFeatures);

      missingSections.forEach((s) => {
        list.push({
          type: "NOTICE_SECTION",
          focusLabel: "공고문 섹션",
          text: `${s} 섹션이 초안에서 누락되었습니다.`,
          severity: "MEDIUM",
          source: s, // 어떤 섹션이 문제인지
          impact: "공고문 요구사항 충족률 하락으로 감점 가능성",
        });
      });

      rawMissingFeatures.forEach((f) => {
        list.push({
          type: "NOTICE_FEATURE",
          focusLabel: "공고문 세부 조건",
          text: `${f.feature_name} 관련 공고문 조건이 초안에 반영되지 않았습니다.`,
          severity: "MEDIUM",
          source: f.source_section || f.feature_name, // 어떤 목차/세부 조건인지
          impact: "평가 기준과의 불일치로 내용 보완 필요",
        });
      });
    }

    // 정렬: HIGH → MEDIUM → LOW
    const SEVERITY_ORDER = { HIGH: 3, MEDIUM: 2, LOW: 1 };
    list.sort(
      (a, b) =>
        (SEVERITY_ORDER[b.severity] || 0) - (SEVERITY_ORDER[a.severity] || 0)
    );

    return list.slice(0, 3); // Top 3만
  }, [results, compareResult]);


  if (items.length === 0) return null;

  return (
    <Card sx={{ mt: 3 }}>
      <CardContent>

        <Stack
          direction="row"
          alignItems="center"
          justifyContent="space-between"
          sx={{ mb: 1 }}
        >
          <Typography variant="h6" sx={{ fontWeight: 700 }}>
            평가 리스크를 줄이기 위한 보완 포인트 Top 3
          </Typography>

          <Chip
            icon={<WarningAmberIcon />}
            label={`${items.length}개 핵심 보완 포인트`}
            size="small"
            color="warning"
          />
        </Stack>

        <Typography sx={{ color: "text.secondary", mb: 2, fontSize: 14 }}>
          아래 항목은 심사위원이 가장 먼저 확인하는 핵심 요소로, 
          지금 보완하면 평가 점수가 즉시 개선될 수 있습니다.
        </Typography>

        <List dense>
          {items.map((item, idx) => {
            const bgColor = SEVERITY_COLORS[item.severity] + "22";

            return (
              <ListItem
                key={idx}
                sx={{
                  border: "1px solid #e0e0e0",
                  borderRadius: 2,
                  mb: 1.5,
                  p: 2,
                  background: bgColor,
                }}
                alignItems="flex-start"
              >
                <ListItemText
                  primary={
                    <Stack direction="row" spacing={1} alignItems="center">
                      <Chip size="small" variant="outlined" label={item.focusLabel} />
                      <Chip
                        size="small"
                        label={SEVERITY_LABELS[item.severity]}
                        sx={{
                          borderColor: SEVERITY_COLORS[item.severity],
                          color: SEVERITY_COLORS[item.severity],
                        }}
                        variant="outlined"
                      />
                    </Stack>
                  }
                  secondary={
                    <Box sx={{ mt: 1 }}>
                      <Typography variant="body2" sx={{ fontWeight: 600 }}>
                        {idx + 1}. {item.text}
                      </Typography>

                      {/* 출처 추가 */}
                      <Typography
                        variant="caption"
                        sx={{ color: "text.secondary", display: "block", mt: 0.5 }}
                      >
                        · 출처: {item.source}
                      </Typography>

                      <Typography
                        variant="caption"
                        sx={{ color: "error.main", display: "block", mt: 0.5 }}
                      >
                        · 영향: {item.impact}
                      </Typography>

                      {item.law && (
                        <Typography variant="caption" sx={{ color: "text.secondary" }}>
                          관련 법령: {item.law} {item.article}
                        </Typography>
                      )}
                    </Box>
                  }
                  secondaryTypographyProps={{ component: "div" }}
                />
              </ListItem>
            );
          })}
        </List>
      </CardContent>
    </Card>
  );
}
