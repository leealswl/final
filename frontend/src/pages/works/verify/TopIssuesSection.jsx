import React, { useMemo } from "react";
import {
  Card, CardContent, Typography, Chip, Stack,
  List, ListItem, ListItemText, Box
} from "@mui/material";
import WarningAmberIcon from "@mui/icons-material/WarningAmber";

import {
  buildNormalizedMissingFeatureList,
} from "../../../utils/verifyUtils";

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

    // 1) 법령 missing, violations
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
              severity: v.severity || "MEDIUM",
            });
          });
        }
      });
    }

    // 2) 공고문 누락/조건 부족
    if (hasCompare) {
      const missingSections = compareResult?.missing_sections || [];
      const rawMissingFeatures = compareResult?.feature_mismatch || [];
      const normalizedMissingFeatures =
        buildNormalizedMissingFeatureList(rawMissingFeatures);

      missingSections.forEach((s) => {
        list.push({
          type: "NOTICE_SECTION",
          focusLabel: "공고문 섹션",
          text: `${s} 섹션이 초안에서 빠져 있습니다.`,
          severity: "MEDIUM",
        });
      });

      normalizedMissingFeatures.forEach((f) => {
        list.push({
          type: "NOTICE_FEATURE",
          focusLabel: "공고문 세부 조건",
          text: `${f} 관련 공고문 조건이 초안 내용과 다르거나 부족합니다.`,
          severity: "MEDIUM",
        });
      });
    }

    const SEVERITY_ORDER = { HIGH: 3, MEDIUM: 2, LOW: 1 };
    list.sort(
      (a, b) =>
        (SEVERITY_ORDER[b.severity] || 0) - (SEVERITY_ORDER[a.severity] || 0)
    );

    return list.slice(0, 3);
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
            지금 바로 보완하면 좋은 Top 3
          </Typography>
          <Chip
            icon={<WarningAmberIcon />}
            label={`${items.length}개 핵심 보완 포인트`}
            size="small"
            color="warning"
          />
        </Stack>

        <Typography sx={{ color: "text.secondary", mb: 2, fontSize: 14 }}>
          아래 항목부터 수정하면 심사 리스크를 빠르게 줄일 수 있습니다.
        </Typography>

        <List dense>
          {items.map((item, idx) => (
            <ListItem key={idx} alignItems="flex-start">
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
                  <Box sx={{ mt: 0.5 }}>
                    <Typography variant="body2">
                      {idx + 1}. {item.text}
                    </Typography>
                    {item.law && (
                      <Typography
                        variant="caption"
                        sx={{ color: "text.secondary" }}
                      >
                        관련 법령: {item.law} {item.article}
                      </Typography>
                    )}
                  </Box>
                }
                secondaryTypographyProps={{ component: "div" }}
              />
            </ListItem>
          ))}
        </List>
      </CardContent>
    </Card>
  );
}
