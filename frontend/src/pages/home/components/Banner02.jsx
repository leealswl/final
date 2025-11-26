import { Box, Stack, Typography } from '@mui/material';
import React from 'react';

export const Banner02 = () => {
    return (
        <Box
            sx={{
                width: '100%',
                minHeight: '800px',
                bgcolor: '#f0f2f5',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                py: 8,
                px: 4,
            }}
        >
            <Stack
                direction="row"
                spacing={12}
                sx={{
                    // maxWidth: '1200px',
                    width: '100%',
                    alignItems: 'center',
                }}
            >
                <Stack
                    spacing={5}
                    data-aos="flip-right"
                    data-aos-once="false"
                    sx={{
                        flex: '0 0 52%',
                        bgcolor: '#e2e8f0',
                        borderRadius: '10px',
                        boxShadow: '0px 10px 30px rgba(0, 0, 0, 0.1)',
                        aspectRatio: '16/10',
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'center',
                        overflow: 'hidden',
                    }}
                >
                    <Box
                        sx={{
                            width: '97.65%',
                            height: '96%',
                            bgcolor: '#dcdcdc',
                            borderRadius: '10px',
                            display: 'flex',
                            alignItems: 'center',
                            justifyContent: 'center',
                        }}
                    >
                        <Typography
                            sx={{
                                color: '#999999',
                                fontSize: '16px',
                                textAlign: 'center',
                                whiteSpace: 'nowrap',
                            }}
                        >
                            두 번째 기능 시연 영상/데모
                        </Typography>
                    </Box>
                </Stack>

                <Stack
                    data-aos="zoom-in"
                    data-aos-duration="1500"
                    data-aos-delay="400"
                    data-aos-once="false"
                    spacing={3}
                    sx={{
                        flex: '0 0 40%',
                        alignItems: 'center',
                        textAlign: 'center',
                    }}
                >
                    <Typography
                        variant="h3"
                        sx={{
                            color: '#1a1a1a',
                            fontWeight: 700,
                            fontSize: '44px',
                            lineHeight: 1.2,
                        }}
                    >
                        최적의 기획 잠재력
                    </Typography>

                    <Typography
                        sx={{
                            color: '#555555',
                            fontSize: '17.6px',
                            lineHeight: '28.2px',
                            fontFamily: 'Inter, Helvetica, sans-serif',
                        }}
                    >
                        PALADOC AI는 단 한 번의 입력만으로 기획의 잠재력을
                        <br />
                        극대화하는 결과를 즉시 도출합니다.
                    </Typography>

                    <Typography
                        sx={{
                            color: '#555555',
                            fontSize: '17.6px',
                            lineHeight: '28.2px',
                            fontFamily: 'Inter, Helvetica, sans-serif',
                        }}
                    >
                        복잡한 기획의 본질을 즉각적으로 파악하고, 최적화된 결과물을
                        <br />
                        생성하여 작업 효율을 비약적으로 높여줍니다.
                    </Typography>
                </Stack>
            </Stack>
        </Box>
    );
};

export default Banner02;
