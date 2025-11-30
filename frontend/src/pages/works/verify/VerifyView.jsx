import React, { useEffect, useMemo, useState } from "react";
import {
  Box,
  Card,
  CardContent,
  Chip,
  Typography,
  Stack,
  Divider,
  Accordion,
  AccordionSummary,
  AccordionDetails,
  List,
  ListItem,
  ListItemText,
  Button,
  CircularProgress,
} from "@mui/material";

import ExpandMoreIcon from "@mui/icons-material/ExpandMore";
import {
  PieChart,
  Pie,
  Cell,
  Tooltip,
  Legend,
  ResponsiveContainer,
} from "recharts";

import { draftApi } from "../../../utils/draftApi";
import { tiptapDocToPlainText } from "../../../utils/tiptapText";
import { verifyLawSection } from "../../../utils/fastapi";
import { compareDraft } from "../../../utils/compareDraft";

import { useFileStore } from "../../../store/useFileStore";
import { useProjectStore } from "../../../store/useProjectStore";


// =============================
// FOCUSES 정의
// =============================
const FOCUSES = [
  {
    key: "purpose",
    label: "사업 목적/필요성/국가 R&D 기본 원칙",
    focus:
      "국가연구개발사업의 기본 원칙과 정책 방향을 기준으로, 사업의 목적과 필요성이 타당한지 검토하세요.",
  },
  {
    key: "budget",
    label: "연구개발비·예산",
    focus:
      "연구개발비 및 예산(직접비·간접비·자부담 등) 편성이 관련 법령과 지침에 부합하는지, 항목별 배분과 산정 근거가 타당한지 검토하세요.",
  },
  {
    key: "structure",
    label: "수행체계·책임·참여제한",
    focus:
      "수행기관·주관기관·참여기관의 역할과 책임이 명확한지, 참여제한·격리의무 등 관련 규정을 충족하는지 검토하세요.",
  },
  {
    key: "outcome",
    label: "성과지표·평가·성과관리",
    focus:
      "성과지표, 평가 방식, 성과관리·사후관리 체계가 관련 지침에 맞게 구체적으로 설계되어 있는지 검토하세요.",
  },
];


// =======================================================
// 🚀 공고문 비교 대시보드
// =======================================================
function AnnouncementCompareDashboard({ result }) {
  if (!result) return null;

  const missingSections = result?.missing_sections || [];
  const missingFeatures = result?.feature_mismatch || [];

  const mapped = result?.mapped_sections || [];

  const sectionDetails = result?.section_analysis?.details || [];
  const featureDetails = result?.feature_analysis?.details || [];

  const includedCount = mapped.length;
  const missingCount = missingSections.length + missingFeatures.length;

  const chartData = [
    { name: "Included", value: includedCount },
    { name: "Missing", value: missingCount },
  ];

  const COLORS = ["#4caf50", "#f44336"];

  return (
    <Box sx={{ mt: 4 }}>
      <Card>
        <CardContent>
          <Stack direction={{ xs: "column", md: "row" }} spacing={3}>
            <Box sx={{ flex: 1 }}>
              <Typography variant="h6" sx={{ fontWeight: 700 }}>
                공고문 요구사항 충족 요약
              </Typography>

              <Typography sx={{ mt: 2 }}>
                총 <b>{includedCount}</b>개의 항목은 충족되었으며{" "}
                <b>{missingCount}</b>개의 항목이 부족합니다.
              </Typography>

              {missingSections.length > 0 && (
                <Box sx={{ mt: 2 }}>
                  <Typography sx={{ fontWeight: 600 }}>
                    누락된 필수 섹션
                  </Typography>
                  <List dense>
                    {missingSections.map((s, i) => (
                      <ListItem key={i}>
                        <ListItemText primary={s} />
                      </ListItem>
                    ))}
                  </List>
                </Box>
              )}

              {missingFeatures.length > 0 && (
                <Box sx={{ mt: 2 }}>
                  <Typography sx={{ fontWeight: 600 }}>
                    불일치 Feature
                  </Typography>
                  <List dense>
                    {missingFeatures.map((f, i) => (
                      <ListItem key={i}>
                        <ListItemText primary={f} />
                      </ListItem>
                    ))}
                  </List>
                </Box>
              )}
            </Box>

            <Box sx={{ width: 260, height: 230 }}>
              <ResponsiveContainer>
                <PieChart>
                  <Pie
                    data={chartData}
                    dataKey="value"
                    innerRadius={60}
                    outerRadius={80}
                    paddingAngle={4}
                  >
                    {chartData.map((entry, idx) => (
                      <Cell key={idx} fill={COLORS[idx]} />
                    ))}
                  </Pie>
                  <Tooltip />
                  <Legend />
                </PieChart>
              </ResponsiveContainer>
            </Box>
          </Stack>
        </CardContent>
      </Card>

      {/* 상세 - 섹션 */}
      <Card sx={{ mt: 3 }}>
        <CardContent>
          <Typography variant="h6" sx={{ fontWeight: 700 }}>
            섹션 상세 분석
          </Typography>

          {sectionDetails.map((item, i) => (
            <Accordion key={i} sx={{ boxShadow: "none" }}>
              <AccordionSummary expandIcon={<ExpandMoreIcon />}>
                <Stack direction="row" spacing={1}>
                  <Typography sx={{ fontWeight: 600 }}>{item.section}</Typography>
                </Stack>
              </AccordionSummary>

              <AccordionDetails>
                <Typography sx={{ mt: 1 }}>
                  <b>이유:</b> {item.reason}
                </Typography>
                <Typography sx={{ mt: 1 }}>
                  <b>보완 제안:</b> {item.suggestion}
                </Typography>
              </AccordionDetails>
            </Accordion>
          ))}
        </CardContent>
      </Card>

      {/* 상세 - Feature */}
      <Card sx={{ mt: 3 }}>
        <CardContent>
          <Typography variant="h6" sx={{ fontWeight: 700 }}>
            Feature 상세 분석
          </Typography>

          {featureDetails.map((item, i) => (
            <Accordion key={i} sx={{ boxShadow: "none" }}>
              <AccordionSummary expandIcon={<ExpandMoreIcon />}>
                <Stack direction="row" spacing={1}>
                  <Typography sx={{ fontWeight: 600 }}>{item.feature}</Typography>
                </Stack>
              </AccordionSummary>

              <AccordionDetails>
                <Typography sx={{ mt: 1 }}>
                  <b>이유:</b> {item.reason}
                </Typography>
                <Typography sx={{ mt: 1 }}>
                  <b>보완 제안:</b> {item.suggestion}
                </Typography>
              </AccordionDetails>
            </Accordion>
          ))}
        </CardContent>
      </Card>
    </Box>
  );
}


// =======================================================
// 🚀 법령 검증 대시보드
// =======================================================
function LawVerifyDashboard({ results }) {

  const hasResults = results && Object.keys(results).length > 0;

  const {
    statusCounts,
    overallStatus,
    overallRisk,
    actionItems,
    sortedEntries,
  } = useMemo(() => {
    if (!hasResults) {
      return {
        statusCounts: {},
        overallStatus: null,
        overallRisk: null,
        actionItems: [],
        sortedEntries: [],
      };
    }

    const statusCounts = { 적합: 0, 보완: 0, 부적합: 0 };
    const actionItems = [];
    const entries = Object.entries(results);

    entries.forEach(([key, r]) => {
      if (!r) return;

      if (r.status && statusCounts[r.status] !== undefined) {
        statusCounts[r.status] += 1;
      }

      if (Array.isArray(r.missing)) {
        r.missing.forEach((m) => {
          actionItems.push({
            focusKey: key,
            focusLabel: r.label,
            text: m,
          });
        });
      }
    });

    const STATUS_ORDER = { 적합: 1, 보완: 2, 부적합: 3 };
    const RISK_ORDER = { LOW: 1, MEDIUM: 2, HIGH: 3 };

    const sortedEntries = entries.sort(([, a], [, b]) => {
      const aStatus = a?.status || "적합";
      const bStatus = b?.status || "적합";
      const aRisk = a?.risk_level || "LOW";
      const bRisk = b?.risk_level || "LOW";

      const statusDiff = STATUS_ORDER[bStatus] - STATUS_ORDER[aStatus];
      if (statusDiff !== 0) return statusDiff;

      return RISK_ORDER[bRisk] - RISK_ORDER[aRisk];
    });

    const overallStatus = sortedEntries[0]?.[1]?.status || null;
    const overallRisk = sortedEntries[0]?.[1]?.risk_level || null;

    return {
      statusCounts,
      overallStatus,
      overallRisk,
      actionItems,
      sortedEntries,
    };
  }, [results, hasResults]);


  const STATUS_COLORS = { 적합: "#4caf50", 보완: "#ffb300", 부적합: "#f44336" };
  const statusChartData = Object.entries(statusCounts)
    .filter(([, count]) => count > 0)
    .map(([name, value]) => ({ name, value }));


  return (
    <Box sx={{ display: "flex", flexDirection: "column", gap: 3, mt: 3 }}>
      <Card>
        <CardContent>
          <Stack direction={{ xs: "column", md: "row" }} spacing={3}>
            <Box sx={{ flex: 1 }}>
              <Typography variant="h6" sx={{ fontWeight: 700 }}>
                summary
              </Typography>

              <Stack spacing={1.2} sx={{ mt: 1.5 }}>
                {sortedEntries.map(([key, r]) => (
                  <Box key={key}>
                    <Typography sx={{ fontWeight: 600 }}>{r.label}</Typography>
                    {r.reason && (
                      <Typography
                        sx={{
                          ml: 1,
                          color: "text.secondary",
                          whiteSpace: "pre-line",
                        }}
                      >
                        {r.reason}
                      </Typography>
                    )}
                  </Box>
                ))}
              </Stack>
            </Box>

            <Box sx={{ width: 260, height: 230 }}>
              {statusChartData.length === 0 ? (
                <Typography
                  sx={{ mt: 7, textAlign: "center", color: "text.secondary" }}
                >
                  검증 결과 없음
                </Typography>
              ) : (
                <ResponsiveContainer>
                  <PieChart>
                    <Pie
                      data={statusChartData}
                      dataKey="value"
                      innerRadius={60}
                      outerRadius={80}
                      paddingAngle={3}
                    >
                      {statusChartData.map((entry, idx) => (
                        <Cell key={idx} fill={STATUS_COLORS[entry.name]} />
                      ))}
                    </Pie>
                    <Tooltip />
                    <Legend />
                  </PieChart>
                </ResponsiveContainer>
              )}

              {overallRisk && (
                <Chip
                  size="small"
                  variant="outlined"
                  label={`전체 리스크: ${overallRisk}`}
                  sx={{ mt: 1 }}
                />
              )}
            </Box>
          </Stack>
        </CardContent>
      </Card>

      {actionItems.length > 0 && (
        <Card>
          <CardContent>
            <Typography variant="h6" sx={{ fontWeight: 700 }}>
              보완이 필요한 핵심 항목
            </Typography>

            <List dense>
              {actionItems.map((item, idx) => (
                <ListItem key={idx}>
                  <ListItemText
                    primary={
                      <>
                        <Typography
                          variant="caption"
                          sx={{ fontWeight: 600, mr: 1 }}
                        >
                          [{item.focusLabel}]
                        </Typography>
                        {item.text}
                      </>
                    }
                  />
                </ListItem>
              ))}
            </List>
          </CardContent>
        </Card>
      )}

      <Card>
        <CardContent>
          <Typography variant="h6" sx={{ fontWeight: 700, mb: 1 }}>
            관점별 상세 분석
          </Typography>

          {sortedEntries.map(([key, r]) => (
            <Accordion key={key} sx={{ boxShadow: "none" }}>
              <AccordionSummary expandIcon={<ExpandMoreIcon />}>
                <Stack direction="row" spacing={1}>
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
                </Stack>
              </AccordionSummary>

              <AccordionDetails>
                {r.missing?.length > 0 && (
                  <Box sx={{ mb: 2 }}>
                    <Typography sx={{ fontWeight: 600 }}>부족한 요소</Typography>
                    <List dense>
                      {r.missing.map((m, i) => (
                        <ListItem key={i}>
                          <ListItemText primary={m} />
                        </ListItem>
                      ))}
                    </List>
                  </Box>
                )}

                {r.suggestion && (
                  <Box sx={{ mb: 2 }}>
                    <Typography sx={{ fontWeight: 600 }}>보완 제안</Typography>
                    <Typography sx={{ whiteSpace: "pre-line" }}>
                      {r.suggestion}
                    </Typography>
                  </Box>
                )}

                {r.related_laws?.length > 0 && (
                  <Box>
                    <Typography sx={{ fontWeight: 600 }}>관련 법령</Typography>
                    <Stack direction="row" gap={1} flexWrap="wrap">
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
    </Box>
  );
}




// =======================================================
// 🚀 VerifyView Main
// =======================================================
function VerifyView() {
  const [loading, setLoading] = useState(false);
  const [progress, setProgress] = useState(0);

  const [text, setText] = useState("");
  const [draftJson, setDraftJson] = useState(null);

  const [results, setResults] = useState({});
  const [compareResult, setCompareResult] = useState(null);

  const [activeTab, setActiveTab] = useState(null);

  const filePath = useFileStore((state) => state.filePath);
  const project = useProjectStore((state) => state.project);
  const projectIdx = project?.projectIdx;


  // 초안 로딩
  useEffect(() => {
    if (!filePath) return;

    (async () => {
      try {
        const docJson = await draftApi(filePath);
        setDraftJson(docJson);

        const plain = tiptapDocToPlainText(docJson);
        setText(plain);
      } catch (e) {
        console.error("초안 JSON 불러오기 실패:", e);
      }
    })();
  }, [filePath]);


  // 🔵 법령 검증 실행 + 로딩 + 진행률
  const handleVerifyAll = async () => {
    if (!text) return alert("초안이 없습니다.");

    setActiveTab("law");
    setLoading(true);
    setProgress(0);

    const total = FOCUSES.length;
    let count = 0;

    const settled = await Promise.allSettled(
      FOCUSES.map(async (f) => {
        const res = await verifyLawSection({ text, focus: f.focus });

        count++;
        setProgress(Math.round((count / total) * 100));

        return { key: f.key, label: f.label, data: res.data };
      })
    );

    const next = {};
    settled.forEach((res, idx) => {
      const f = FOCUSES[idx];

      next[f.key] =
        res.status === "fulfilled"
          ? { label: f.label, ...res.value.data }
          : {
              label: f.label,
              status: "error",
              risk_level: "UNKNOWN",
              reason: "검증 과정 중 오류 발생",
            };
    });

    setResults(next);
    setTimeout(() => setLoading(false), 300);
  };


  // 🔵 공고문 비교 실행 + 진행률
  const handleCompare = async () => {
    if (!draftJson) return alert("초안 JSON이 없습니다.");

    setActiveTab("compare");
    setLoading(true);
    setProgress(10);

    try {
      setProgress(40);

      const result = await compareDraft(projectIdx, draftJson);

      setProgress(100);
      setCompareResult(result);
    } catch (e) {
      console.error("초안 비교 오류:", e);
    } finally {
      setTimeout(() => setLoading(false), 300);
    }
  };


  return (
    <Box sx={{ p: 3 }}>

      {/* 🔥 중앙 로딩 오버레이 */}
      {loading && (
        <Box
          sx={{
            position: "fixed",
            top: 0,
            left: 0,
            width: "100vw",
            height: "100vh",
            bgcolor: "rgba(255,255,255,0.7)",
            display: "flex",
            flexDirection: "column",
            alignItems: "center",
            justifyContent: "center",
            zIndex: 2000,
          }}
        >
          <CircularProgress size={60} />
          <Typography sx={{ mt: 2, fontSize: 18, fontWeight: 600 }}>
            분석 중... {progress}%
          </Typography>
        </Box>
      )}

      {/* Header */}
      <Stack direction="row" alignItems="center" justifyContent="space-between">
        <Box>
          <Typography variant="h5" sx={{ fontWeight: 700 }}>
            검증
          </Typography>
          <Typography sx={{ color: "text.secondary" }}>
            기획서 초안을 기반으로 법령 준수 및 공고문 요구사항 충족 여부를 자동 점검합니다.
          </Typography>
        </Box>

        <Stack direction="row" spacing={2}>
          <Button
            variant="contained"
            onClick={handleVerifyAll}
          >
            법령 검증
          </Button>

          <Button
            variant="outlined"
            onClick={handleCompare}
          >
            초안 검증
          </Button>
        </Stack>
      </Stack>

      {!text && (
        <Typography sx={{ mt: 2, color: "text.secondary" }}>
          초안을 불러오는 중입니다…
        </Typography>
      )}

      {activeTab === "law" && Object.keys(results).length > 0 && (
        <LawVerifyDashboard results={results} />
      )}

      {activeTab === "compare" && compareResult && (
        <AnnouncementCompareDashboard result={compareResult} />
      )}
    </Box>
  );
}

export default VerifyView;
