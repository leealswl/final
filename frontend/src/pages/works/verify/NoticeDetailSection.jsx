import React from "react";
import {
  Card, CardContent, Typography,
  Accordion, AccordionSummary, AccordionDetails,
  Divider, Box
} from "@mui/material";
import ExpandMoreIcon from "@mui/icons-material/ExpandMore";

import {
  FEATURE_EXCLUDE_KEYWORDS,
  normalizeFeatureLabel,
  buildNormalizedMissingFeatureList,
} from "../../../utils/verifyUtils";

export default function NoticeDetailSection({ compareResult }) {
  if (!compareResult) return null;

  const missingSections = compareResult?.missing_sections || [];
  const rawMissingFeatures = compareResult?.feature_mismatch || [];
  const missingFeatures = buildNormalizedMissingFeatureList(rawMissingFeatures);

  const sectionDetails = compareResult?.section_analysis?.details || [];
  const rawFeatureDetails = compareResult?.feature_analysis?.details || [];

  const mergedFeatureMap = {};

  rawFeatureDetails.forEach((item) => {
    const rawLabel =
      typeof item?.feature === "string"
        ? item.feature
        : String(item?.feature ?? "");

    if (FEATURE_EXCLUDE_KEYWORDS.some((kw) => rawLabel.includes(kw))) return;

    const label = normalizeFeatureLabel(rawLabel);

    if (!mergedFeatureMap[label]) {
      mergedFeatureMap[label] = { ...item, feature: label };
    }
  });

  const featureDetails = Object.values(mergedFeatureMap);

  return (
    <Card sx={{ mt: 3 }}>
      <CardContent>
        <Typography variant="h6" sx={{ fontWeight: 700, mb: 1 }}>
          공고문 요구사항 vs 초안 상세
        </Typography>

        <Typography sx={{ color: "text.secondary", mb: 2, fontSize: 14 }}>
          공고문에서 요구한 항목이 초안에 어떻게 반영되었는지,  
          <b>누락된 섹션</b>과 <b>세부 조건 불일치</b>를 확인할 수 있습니다.
        </Typography>

        {/* 섹션 상세 */}
        {sectionDetails.length > 0 && (
          <>
            <Typography sx={{ fontWeight: 600, mt: 1, mb: 1 }}>
              섹션별 상세 분석
            </Typography>

            {sectionDetails.map((item, i) => (
              <Accordion key={i} sx={{ boxShadow: "none" }}>
                <AccordionSummary expandIcon={<ExpandMoreIcon />}>
                  <Typography sx={{ fontWeight: 600 }}>
                    {item.section}
                  </Typography>
                </AccordionSummary>
                <AccordionDetails>
                  <Typography sx={{ mt: 0.5 }}>
                    <b>이유:</b> {item.reason}
                  </Typography>
                  <Typography sx={{ mt: 0.5 }}>
                    <b>보완 제안:</b> {item.suggestion}
                  </Typography>
                </AccordionDetails>
              </Accordion>
            ))}
          </>
        )}

        {/* Feature 상세 */}
        {featureDetails.length > 0 && (
          <>
            <Divider sx={{ my: 2 }} />

            <Typography sx={{ fontWeight: 600, mb: 1 }}>
              세부 조건별 분석
            </Typography>

            {featureDetails.map((item, i) => (
              <Accordion key={i} sx={{ boxShadow: "none" }}>
                <AccordionSummary expandIcon={<ExpandMoreIcon />}>
                  <Typography sx={{ fontWeight: 600 }}>
                    {item.feature}
                  </Typography>
                </AccordionSummary>
                <AccordionDetails>
                  <Typography sx={{ mt: 0.5 }}>
                    <b>이유:</b> {item.reason}
                  </Typography>
                  <Typography sx={{ mt: 0.5 }}>
                    <b>보완 제안:</b> {item.suggestion}
                  </Typography>
                </AccordionDetails>
              </Accordion>
            ))}
          </>
        )}

        {/* 분석 결과가 아무것도 없을 때 */}
        {missingSections.length === 0 &&
          featureDetails.length === 0 &&
          sectionDetails.length === 0 && (
            <Box sx={{ mt: 1 }}>
              <Typography sx={{ color: "text.secondary" }}>
                공고문 기준으로 분석할 항목이 없습니다.
              </Typography>
            </Box>
          )}
      </CardContent>
    </Card>
  );
}
