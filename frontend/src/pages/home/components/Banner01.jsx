import { Grid, Box, Stack, Typography, Button } from '@mui/material';
import React from 'react';
import banner01 from '../img/banner01.png';
import Section from '../img/Section.png';

const Banner01 = () => {
    const main = () => {
        window.location.href = '/main';
    };
    return (
        <Grid mx={30} mt={4}>
            <Stack display={'flex'} justifyContent={'center'} alignItems={'center'}>
                <Grid sx={{ width: '100%', height: '55vh' }}>
                    <Box
                        sx={{
                            width: '100%',
                            height: '100%',
                            backgroundImage: `url(${banner01})`,
                            backgroundSize: 'cover', // 이미지 크기 조정 (cover, contain 등)
                            backgroundPosition: 'center', // 가운데 정렬
                            backgroundRepeat: 'no-repeat', // 반복 방지
                            // boxShadow: 3,
                            // borderRadius: 2,
                            display: 'flex',
                            justifyContent: 'center',
                            alignItems: 'center',
                            flexDirection: 'column',
                        }}
                    >
                        <Typography fontSize={60} textAlign={'center'} my={2} fontFamily={'Isamanru-Bold'}>
                            A next-gen
                            <br />
                            AI editor for all your
                            <br />
                            documents
                        </Typography>
                        <Typography textAlign={'center'} fontFamily={'Pretendard5'}>
                            Out-of-the-box, Markdown-Friendly
                            <br />
                            Full framework support (React, Vue Angular, Svelte)
                        </Typography>
                        <Button
                            onClick={main}
                            variant="contained"
                            size="large"
                            sx={{
                                my: '20px',
                                backgroundColor: 'black',
                                color: 'white',
                                fontWeight: 'bold',
                                '&:hover': {
                                    backgroundColor: '#333',
                                },
                            }}
                        >
                            Quick Start
                        </Button>
                    </Box>
                </Grid>
                <Box
                    sx={{
                        width: '100%',
                        height: '55vh',
                        backgroundImage: `url(${Section})`,
                        backgroundSize: 'cover', // 이미지 크기 조정 (cover, contain 등)
                        backgroundPosition: 'center', // 가운데 정렬
                        backgroundRepeat: 'no-repeat', // 반복 방지
                        // boxShadow: 3,
                        // borderRadius: 2,
                        display: 'flex',
                        justifyContent: 'center',
                        alignItems: 'center',
                        flexDirection: 'column',
                    }}
                />
            </Stack>
        </Grid>
    );
};

export default Banner01;
