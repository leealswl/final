import React, { useRef } from "react";
import {
  Box, Stack, Typography, Button,
  Card, CardContent
} from "@mui/material";

import ArrowBackIcon from "@mui/icons-material/ArrowBack";
import ErrorOutlineIcon from "@mui/icons-material/ErrorOutline";
import PictureAsPdfIcon from "@mui/icons-material/PictureAsPdf";
import html2canvas from "html2canvas";
import jsPDF from "jspdf";

import { useNavigate } from "react-router-dom";

import SummaryHeader from "./SummaryHeader";
import { useVerifyStore } from "../../../store/useVerifyStore";
import TopIssuesSection from "./TopIssuesSection";
import LawDetailSection from "./LawDetailSection";
import NoticeDetailSection from "./NoticeDetailSection";
import NoticeCriteriaSelfCheck from "./NoticeCriteriaSelfCheck";

import VerifySummaryCard from "./VerifySummaryCard";
import OverallAssessment from "./OverallAssessment";


export default function VerifyReport2() {
  const navigate = useNavigate();
  const { results, compareResult, noticeEvalResult } = useVerifyStore();
  const reportRef = useRef(null);

  const hasLaw = results && Object.keys(results).length > 0;
  const hasCompare = !!compareResult;
  const isEmpty = !hasLaw && !hasCompare;
  const handleDownloadPdf = async () => {
    const target = reportRef.current;
    if (!target) return;

    const canvas = await html2canvas(target, {
      scale: 2,
      useCORS: true,
      scrollY: -window.scrollY,
    });

    const imgData = canvas.toDataURL("image/png");
    const pdf = new jsPDF("p", "mm", "a4");
    const pdfWidth = pdf.internal.pageSize.getWidth();
    const pdfHeight = pdf.internal.pageSize.getHeight();
    const imgProps = { width: canvas.width, height: canvas.height };
    const imgPdfHeight = (imgProps.height * pdfWidth) / imgProps.width;

    let heightLeft = imgPdfHeight;
    let position = 0;

    pdf.addImage(imgData, "PNG", 0, position, pdfWidth, imgPdfHeight);
    heightLeft -= pdfHeight;

    while (heightLeft > 0) {
      position = heightLeft - imgPdfHeight;
      pdf.addPage();
      pdf.addImage(imgData, "PNG", 0, position, pdfWidth, imgPdfHeight);
      heightLeft -= pdfHeight;
    }

    pdf.save("verify-report.pdf");
  };

  return (
    <Box sx={{ p: 3 }} ref={reportRef}>
      {/* 헤더 */}
      <Stack direction="row" alignItems="center" justifyContent="space-between">
        <Stack spacing={0.5}>
          <Typography variant="h5" sx={{ fontWeight: 700 }}>
            종합 리포트
          </Typography>
          <Typography sx={{ color: "text.secondary", fontSize: 14 }}>
            현재 프로젝트에 대해 수행한 <b>법령 검증</b> 및 <b>공고문·초안 비교</b> 결과입니다.
          </Typography>
        </Stack>

        <Stack direction="row" spacing={1}>
          <Button
            variant="outlined"
            startIcon={<ArrowBackIcon />}
            onClick={() => navigate("/works/verify")}
          >
            검증 화면으로 돌아가기
          </Button>
          <Button
            variant="contained"
            startIcon={<PictureAsPdfIcon />}
            onClick={handleDownloadPdf}
          >
            PDF 다운로드
          </Button>
        </Stack>
      </Stack>

      {/* 데이터 없음 */}
      {isEmpty ? (
        <Card sx={{ mt: 3 }}>
          <CardContent>
            <Stack direction="row" spacing={1} alignItems="center" sx={{ mb: 1 }}>
              <ErrorOutlineIcon color="warning" />
              <Typography sx={{ fontWeight: 600 }}>
                아직 생성된 리포트가 없습니다.
              </Typography>
            </Stack>

            <Typography sx={{ color: "text.secondary", mb: 2 }}>
              먼저 검증 화면에서 <b>법령 검증</b> 또는 <b>초안 검증</b>을 실행해주세요.
            </Typography>

            <Button
              variant="contained"
              onClick={() => navigate("/works/verify")}
              startIcon={<ArrowBackIcon />}
            >
              검증 실행하러 가기
            </Button>
          </CardContent>
        </Card>
      ) : (
        <>
          {/* 상단 요약 */}
          <SummaryHeader
            results={results}
            compareResult={compareResult}
            noticeEval={noticeEvalResult}
          />

          {/* TOP 3 */}
          <TopIssuesSection results={results} compareResult={compareResult} />

          {/* 평가기준 자가진단 */}
          {/* {noticeEvalResult && (
            <NoticeCriteriaSelfCheck data={noticeEvalResult} />
          )} */}
          <VerifySummaryCard
            results={results}
            compareResult={compareResult}
            noticeEval={noticeEvalResult}
          />

          {/* 상세 분석 */}
          {/* {hasLaw && <LawDetailSection results={results} />}
          {hasCompare && <NoticeDetailSection compareResult={compareResult} />} */}
          <OverallAssessment
            results={results}
            compareResult={compareResult}
          />
        </>
      )}
    </Box>
  );
}
