import { Box, Stack, Typography, Grid } from '@mui/material'
import React from 'react'
import banner03img01 from '../img/banner03_img01.png'
import banner03img02 from '../img/banner03_img02.png'
import banner03img03 from '../img/banner03_img03.png'
import banner03img05 from '../img/banner03_img04.png'
import banner03img04 from '../img/banner03_img05.png'
import banner03img06 from '../img/banner03_img06.png'
import { grey } from '@mui/material/colors'

const Banner03 = () => {
    return(
        <Grid mx={30} mt={10}>
            <Stack mb={5} alignItems={'center'}>
                <Typography fontSize={50} fontFamily={'SeoulAlrim-Heavy'}>Why Choose Our AI Service?</Typography>
                <Typography textAlign={'center'} fontFamily={'SeoulAlrim-Medium'}>단순한 도구를 넘어, 기획 및 문서 작성 과정 전체를 혁신합니다.<br />최적의 결과물을 단 한 번의 클릭으로.</Typography>
            </Stack>
            <Grid display={'flex'} justifyContent={'center'}>
                <Stack width={400} height={400} border={1} borderColor={'gray'} borderRadius={2} mr={3} boxShadow={3}>
                    <Grid height={100} m={3}>
                        <Typography fontSize={24} fontWeight={'bold'}>자동 요건 진단</Typography>
                        <Typography color='gray'>**핵심 추출과 분석** RFP/RMP 문서만 입력하면, AI가 핵심 요구사항, 필수 요건, 개발 범위를 즉시 추출하고 진단합니다.</Typography>
                    </Grid>
                    <Grid height={300} mx={3} mb={3} boxShadow={3}>
                        <Box
                            component={'img'}
                            src={banner03img01}
                            alt="img01"
                            sx={{
                                width: '100%',
                                height:'100%',
                            }}
                            >
                        </Box>
                    </Grid>
                </Stack>
                <Stack width={400} height={400} border={1} borderColor={'gray'} borderRadius={2} mr={3} boxShadow={3}>
                    <Grid height={100} m={3}>
                        <Typography fontSize={24} fontWeight={'bold'}>원클릭 통합 기능</Typography>
                        <Typography color='gray'>**편집기와의 완벽한 연동** AI 출력 내용을 원클릭으로 편집기의 지정된 위치에 삽입하거나 대체하여, 문서 작성 시간을 획기적으로 단축합니다.</Typography>
                    </Grid>
                    <Grid height={250} mx={3} mb={3} boxShadow={3}>
                        <Box
                            component={'img'}
                            src={banner03img02}
                            alt="img02"
                            sx={{
                                width: '100%',
                                height:'100%',
                                // objectFit:'cover'

                            }}
                            >
                                
                        </Box>
                    </Grid>
                </Stack>
                <Stack width={400} height={400} border={1} borderColor={'gray'} borderRadius={2} boxShadow={5}>
                    <Grid height={100} m={3}>
                        <Typography fontSize={24} fontWeight={'bold'}>기획 잠재력 극대화</Typography>
                        <Typography color='gray'>**'퀘스터'와 '로드맵'의 통합** AI 번역, AI 요약, AI 코드 블록 등 다양한 기능을 지원하며, 한 번의 입력으로 최적의 기획 초안을 생성합니다.</Typography>
                    </Grid>
                    <Grid height={228} mx={3} display={'flex'} justifyContent={'center'} backgroundColor={'#f0f0f0ff'} borderRadius={2} boxShadow={3}>
                        <Box
                            component={'img'}
                            src={banner03img03}
                            alt="img03"
                            sx={{
                                height: '100%',
                                objectFit: 'contain'
                            }}
                            >
                        </Box>
                    </Grid>
                </Stack>

            </Grid>
            <Grid display={'flex'} justifyContent={'center'}>
                <Grid my={8} border={1} borderColor={grey} borderRadius={2} p={3} width={1248} boxShadow={3}>
                    <Grid>
                        <Typography fontSize={24} fontWeight={'bold'}>3-Way 에이전트 시스템</Typography>
                        <Typography color='gray'>**전문 분야별 분업화** Analysis, Grading, Coaching 에이전트가 3단계로 나누어 지원하여, 오류 없는 완벽한 결과물과 실시간 피드백을 보장합니다.</Typography>
                    </Grid>
                    <Grid>
                        <Grid sx={{backgroundColor:'#f0f0f0ff'}} height={'auto'} borderRadius={2} mt={3} display={'flex'} p={3} justifyContent={'space-between'}>
                            <Box
                                component={'img'}
                                src={banner03img04}
                                sx={{height:'250px',}}
                                />
                            <Box
                                component={'img'}
                                src={banner03img05}
                                sx={{height:'250px'}}
                            />
                            <Box
                                component={'img'}
                                src={banner03img06}
                                sx={{height:'250px'}}
                                />
                        </Grid>
                    </Grid>
                </Grid>
            </Grid>

        </Grid>
    )
}

export default Banner03