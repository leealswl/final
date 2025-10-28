import BookmarkIcon from "@mui/icons-material/Bookmark";
import GroupIcon from "@mui/icons-material/Group";
import LabelIcon from "@mui/icons-material/Label";
import LinkIcon from "@mui/icons-material/Link";
import { Box, Stack, Typography } from "@mui/material";
import React from "react";
import cat from "../img/cat.png";
import banner04 from "../img/banner04.png";

const features = [
  {
    icon: BookmarkIcon,
    iconColor: "#cc0000",
    title: "코어(Core) 중심의 최적화",
    description:
      "PALADOC AI의 핵심 엔진은 기획의 본질을 즉시 파악하고, 단 한 번의 입력으로 최적화된 결과물을 생성하여 시간 낭비를 최소화합니다.",
  },
  {
    icon: LinkIcon,
    iconColor: "#0075ff",
    title: "플로우(Flow)를 잇는 지속적인 컨텍스트",
    description:
      "RFP 분석부터 최종 문서 작성까지, 모든 단계에서 이전 대화 및 문서의 히스토리를 완벽하게 유지하여 끊김 없는 작업 흐름과 일관성을 보장합니다.",
  },
  {
    icon: GroupIcon,
    iconColor: "#4caf50",
    title: "전문 에이전트 시스템",
    description:
      "Analysis, Grading, Coaching 등 전문화된 3-Way 에이전트들이 분업하여 작업을 수행합니다. 각 파트의 최적화된 결과를 실시간으로 제공합니다.",
  },
  {
    icon: LabelIcon,
    iconColor: "#ff9800",
    title: "원클릭 통합 및 삽입",
    description:
      "복잡한 마크업이나 복사/붙여넣기 없이, AI 결과를 문서 편집기의 지정된 위치에 **원클릭**으로 삽입하거나 대체하여 작업 시간을 획기적으로 단축합니다.",
  },
];

const Banner04 = () => {
  return (
    <Box
      sx={{
        position: "relative",
        width: "100%",
        minHeight: "1080px",
        backgroundColor: "white",
        overflow: "hidden",
      }}
    >
      <Box
        component="img"
        src={banner04}
        alt="Background"
        sx={{
          position: "absolute",
          top: 0,
          left: 0,
          width: "100%",
          height: "100%",
          objectFit: "cover",
        }}
      />

      <Box
        sx={{
          position: "relative",
          maxWidth: "1200px",
          margin: "0 auto",
          padding: "114px 40px",
        }}
      >
        <Stack
          component="header"
          spacing={3.25}
          alignItems="center"
          sx={{ mb: 9.25 }}
        >
          <Typography
            variant="h2"
            sx={{
              color: "#1a1a1a",
              fontSize: "48px",
              fontWeight: 700,
              textAlign: "center",
              lineHeight: 1.3,
            }}
          >
            Why choose our AI-Powered Platform?
          </Typography>

          <Typography
            sx={{
              color: "#444444",
              fontSize: "20.8px",
              fontWeight: 400,
              textAlign: "center",
              lineHeight: "33.3px",
              maxWidth: "796px",
            }}
          >
            우리는 AI 기능이 사람의 능력을 가리지 않고 증폭시켜야 한다고
            믿습니다. 모든 디자인
            <br />
            결정은 이러한 목표를 반영합니다.
          </Typography>
        </Stack>

        <Box sx={{ display: "flex", gap: 8, alignItems: "center" }}>
          <Stack spacing={4.75} sx={{ flex: "0 0 auto", maxWidth: "540px" }}>
            {features.map((feature, index) => (
              <Stack
                key={index}
                direction="row"
                spacing={2.5}
                alignItems="flex-start"
              >
                <Box
                  sx={{
                    display: "flex",
                    alignItems: "center",
                    justifyContent: "center",
                    minWidth: "24px",
                    height: "24px",
                    mt: 0.5,
                  }}
                >
                  <feature.icon
                    sx={{ fontSize: 24, color: feature.iconColor }}
                  />
                </Box>

                <Stack spacing={1.5}>
                  <Typography
                    sx={{
                      color: "#1a1a1a",
                      fontSize: "20px",
                      fontWeight: 700,
                      lineHeight: 1.25,
                    }}
                  >
                    {feature.title}
                  </Typography>

                  <Typography
                    sx={{
                      color: "#555555",
                      fontSize: "16px",
                      fontWeight: 400,
                      lineHeight: "26px",
                    }}
                  >
                    {feature.description}
                  </Typography>
                </Stack>
              </Stack>
            ))}
          </Stack>

          <Box
            sx={{
              flex: 1,
              display: "flex",
              justifyContent: "center",
              alignItems: "center",
            }}
          >
            <Box
              component="img"
              src={cat}
              alt="Platform illustration"
              sx={{
                width: "100%",
                maxWidth: "500px",
                height: "auto",
              }}
            />
          </Box>
        </Box>
      </Box>
    </Box>
  );
};

export default Banner04;
