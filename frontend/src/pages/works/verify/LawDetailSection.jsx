import React from "react";
import {
  Card, CardContent, Typography, Accordion,
  AccordionSummary, AccordionDetails, Chip,
  Stack, Box, List, ListItem, ListItemText
} from "@mui/material";
import ExpandMoreIcon from "@mui/icons-material/ExpandMore";

export default function LawDetailSection({ results }) {
  if (!results || Object.keys(results).length === 0) return null;

  const JUDGMENT_LABELS = {
    NO_ISSUE: "법령 위반 징후 없음",
    POTENTIAL_VIOLATION: "법령 위반 가능성 있음",
    POSSIBLE_ISSUE: "법령 리스크 가능성 있음",
    UNCLEAR: "판단 불가",
  };

  return (
    <Card sx={{ mt: 4 }}>
      <CardContent>
        <Typography variant="h6" sx={{ fontWeight: 700, mb: 1 }}>
          법령 검증 상세 결과
        </Typography>
        <Typography sx={{ color: "text.secondary", mb: 2, fontSize: 14 }}>
          각 관점별 적합/보완/부적합 판단 이유 및 법령 위반 가능성을 확인할 수 있습니다.
        </Typography>

        {Object.entries(results).map(([key, r], idx) => (
          <Accordion key={idx} sx={{ boxShadow: "none" }}>
            <AccordionSummary expandIcon={<ExpandMoreIcon />}>
              <Stack direction="row" spacing={1} alignItems="center">
                <Typography sx={{ fontWeight: 600 }}>{r.label}</Typography>

                {r.status && (
                  <Chip
                    size="small"
                    label={r.status}
                    color={
                      r.status === "적합"
                        ? "success"
                        : r.status === "보완"
                        ? "warning"
                        : "error"
                    }
                  />
                )}

                {r.risk_level && (
                  <Chip size="small" variant="outlined" label={r.risk_level} />
                )}

                {r.violation_judgment && (
                  <Chip
                    size="small"
                    variant="outlined"
                    label={
                      JUDGMENT_LABELS[r.violation_judgment] ||
                      r.violation_judgment
                    }
                  />
                )}
              </Stack>
            </AccordionSummary>

            <AccordionDetails>
              {/* 요약 */}
              {r.violation_summary && (
                <Box
                  sx={{
                    mb: 2,
                    p: 1.5,
                    borderRadius: 1,
                    bgcolor: "rgba(244, 67, 54, 0.03)",
                    border: "1px solid rgba(244, 67, 54, 0.3)",
                  }}
                >
                  <Typography sx={{ fontWeight: 600, mb: 0.5 }}>
                    법령 위반 가능성 요약
                  </Typography>
                  <Typography variant="body2" sx={{ whiteSpace: "pre-line" }}>
                    {r.violation_summary}
                  </Typography>
                </Box>
              )}

              {/* 부족한 요소 */}
              {r.missing?.length > 0 && (
                <Box sx={{ mb: 2 }}>
                  <Typography sx={{ fontWeight: 600, mb: 0.5 }}>
                    부족한 요소
                  </Typography>
                  <List dense>
                    {r.missing.map((m, i) => (
                      <ListItem key={i}>
                        <ListItemText primary={m} />
                      </ListItem>
                    ))}
                  </List>
                </Box>
              )}

              {/* 보완 제안 */}
              {r.suggestion && (
                <Box sx={{ mb: 2 }}>
                  <Typography sx={{ fontWeight: 600, mb: 0.5 }}>
                    보완 제안
                  </Typography>
                  <Typography sx={{ whiteSpace: "pre-line" }}>
                    {r.suggestion}
                  </Typography>
                </Box>
              )}

              {/* 위반 가능 조항 */}
              {r.violations?.length > 0 && (
                <Box sx={{ mb: 2 }}>
                  <Typography sx={{ fontWeight: 600, mb: 0.5 }}>
                    법령 위반 가능성이 있는 조항
                  </Typography>
                  <List dense>
                    {r.violations.map((v, i) => (
                      <ListItem key={i} alignItems="flex-start">
                        <ListItemText
                          primary={`${v.law_name} ${v.article_title}`}
                          secondary={
                            <Box sx={{ mt: 0.5 }}>
                              <Typography
                                variant="body2"
                                sx={{ whiteSpace: "pre-line" }}
                              >
                                {v.reason}
                              </Typography>

                              {v.recommendation && (
                                <Typography
                                  variant="body2"
                                  sx={{ mt: 1, whiteSpace: "pre-line" }}
                                >
                                  <b>보완 제안:</b> {v.recommendation}
                                </Typography>
                              )}
                            </Box>
                          }
                          secondaryTypographyProps={{ component: "div" }}
                        />
                      </ListItem>
                    ))}
                  </List>
                </Box>
              )}

              {/* 참고 법령 */}
              {r.related_laws?.length > 0 && (
                <Box>
                  <Typography sx={{ fontWeight: 600, mb: 0.5 }}>
                    참고할 법령
                  </Typography>
                  <Stack direction="row" spacing={1} flexWrap="wrap">
                    {r.related_laws.map((law, i) => (
                      <Chip
                        key={i}
                        size="small"
                        variant="outlined"
                        label={`${law.law_name} ${law.article_title}`}
                      />
                    ))}
                  </Stack>
                </Box>
              )}
            </AccordionDetails>
          </Accordion>
        ))}
      </CardContent>
    </Card>
  );
}
