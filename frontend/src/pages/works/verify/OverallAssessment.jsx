import React from "react";
import { Card, CardContent, Typography } from "@mui/material";

export default function OverallAssessment({ results, compareResult, noticeEval }) {
  if (!results) return null;

  // --------------------------
  // 1) 법령 통계 계산
  // --------------------------
  const lawStats = (() => {
    let total = 0;
    let suitable = 0;
    let risk = { HIGH: 0, MEDIUM: 0, LOW: 0 };

    Object.values(results).forEach((r) => {
      if (!r) return;

      total++;
      if (r.status === "적합") suitable++;

      risk[r.risk_level] = (risk[r.risk_level] || 0) + 1;
    });

    return {
      lawScore: total > 0 ? Math.round((suitable / total) * 100) : null,
      risk,
    };
  })();

  // --------------------------
  // 2) 공고문 충족률
  // --------------------------
  const noticeScore = noticeEval?.percent ?? null;

  // --------------------------
  // 3) 초안에서 누락된 부분 계산
  // --------------------------
  const missingSections = compareResult?.missing_sections?.length || 0;
  const missingFeatures = compareResult?.feature_mismatch?.length || 0;

  // --------------------------
  // 4) 주요 문제 항목 1~2개 가져오기 (TopIssuesSection과 동일 근거)
  // --------------------------
  const topIssue = (() => {
    let list = [];

    Object.values(results).forEach((r) => {
      if (r?.missing?.length) list.push(r.missing[0]);
      if (r?.violations?.length) list.push(r.violations[0]?.reason);
    });

    if (compareResult) {
      compareResult.missing_sections?.forEach((s) => list.push(`${s} 섹션 누락`));
      compareResult.feature_mismatch?.forEach((f) =>
        list.push(`${f.feature_name} 충족 미흡`)
      );
    }

    return list.slice(0, 2);
  })();

  // --------------------------
  // 5) 한 줄 종합 평가 생성
  // --------------------------
  let headline = "";

  if (noticeScore >= 90 && lawStats.lawScore >= 90) {
    headline = "제안서는 매우 우수한 수준으로 완성되어 있으며 핵심 요건을 충실히 반영하고 있습니다.";
  } else if (noticeScore >= 75 && lawStats.lawScore >= 75) {
    headline = "전반적으로 양호한 제안서이나, 일부 항목을 보완하면 완성도가 크게 향상될 수 있습니다.";
  } else if (noticeScore >= 60 || lawStats.lawScore >= 60) {
    headline = "기본적인 구조는 갖추고 있으나 주요 항목에서 보완이 필요한 제안서입니다.";
  } else {
    headline = "핵심 평가 요소에서 여러 개선이 필요한 제안서로, 보완 작업이 반드시 필요합니다.";
  }

  // --------------------------
  // 6) 전체 총평 문장 생성
  // --------------------------
  const detailParagraph = (() => {
    let text = "";

    // 법령 요약
    text += `법령 준수 측면에서는 ${lawStats.lawScore}% 수준으로 `;
    if (lawStats.risk.HIGH > 0) {
      text += `고위험(HIGH) 항목이 ${lawStats.risk.HIGH}건 존재하여 유의가 필요합니다. `;
    } else {
      text += `대체로 양호한 편입니다. `;
    }

    // 공고문 요약
    if (noticeScore != null) {
      text += `공고문 충족률은 ${noticeScore}%로 `;
      if (noticeScore >= 85) text += "요구사항을 대부분 충족하고 있으며 ";
      else if (noticeScore >= 70) text += "기본요건은 충족했으나 일부 항목은 보완이 필요하고 ";
      else text += "핵심 요건 일부가 충실히 반영되지 못했습니다. ";
    }

    // 누락된 섹션
    if (missingSections > 0) {
      text += `${missingSections}개의 공고문 섹션이 초안에서 누락된 것으로 확인되었으며 `;
    }

    // 부족한 feature
    if (missingFeatures > 0) {
      text += `세부 조건 ${missingFeatures}개 항목에서 보완이 필요합니다. `;
    }

    // Top 1~2 문제 언급
    if (topIssue.length > 0) {
      text += `특히 “${topIssue.join(", ")}” 항목은 우선적으로 개선하는 것을 권장드립니다.`;
    }

    return text;
  })();

  return (
    <Card sx={{ mt: 4, borderLeft: "6px solid #6a1b9a" }}>
      <CardContent>
        <Typography variant="h6" sx={{ fontWeight: 700, mb: 1 }}>
          종합 총평
        </Typography>

        {/* 한 줄 요약 */}
        <Typography variant="subtitle1" sx={{ fontWeight: 600, mb: 1.5 }}>
          {headline}
        </Typography>

        {/* 상세 총평 문단 */}
        <Typography sx={{ color: "text.secondary" }}>
          {detailParagraph}
        </Typography>
      </CardContent>
    </Card>
  );
}
