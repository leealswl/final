import React from 'react';
import { Button, Grid, Stack, Box, Typography, CircularProgress } from '@mui/material';
import logo from '../img/nav_logo.png';
import { useAuthStore } from '../../../store/useAuthStore';
import LogoutButton from '../../../components/LogoutButton';

const Navbar = () => {
    const user = useAuthStore((s) => s.user);
    console.log(user);

    const edit = () => {
        window.location.href = '/works';
    };

    const login = () => {
        window.location.href = '/login';
    };

    return (
        <Grid container pt={3} mx={30}>
            <Grid size={1} display="flex" justifyContent="center" alignItems="center">
                <Box
                    component="img"
                    src={logo}
                    alt="logo"
                    sx={{
                        mr: '10px',
                        width: 30,
                        height: 'auto',
                        // borderRadius: 2,
                        // boxShadow: 3,
                    }}
                />
                <Typography fontSize={24} fontWeight={'bold'}>
                    Paladoc
                </Typography>
            </Grid>
            <Grid size={9} display="flex" justifyContent="center" alignItems="center">
                <Stack direction="row" spacing={3}>
                    <Button size="large" color="warning" sx={{ color: 'black', '&:hover': { backgroundColor: '#f5f5f5' } }}>
                        카탈로그
                    </Button>
                    <Button size="large" color="success" sx={{ color: 'black', '&:hover': { backgroundColor: '#f5f5f5' } }}>
                        요금제
                    </Button>
                    <Button size="large" color="primary" sx={{ color: 'black', '&:hover': { backgroundColor: '#f5f5f5' } }}>
                        AI
                    </Button>
                    <Button size="large" color="error" sx={{ color: 'black', '&:hover': { backgroundColor: '#f5f5f5' } }}>
                        고객지원
                    </Button>
                    <Button size="large" color="secondary" sx={{ color: 'black', '&:hover': { backgroundColor: '#f5f5f5' } }} onClick={edit}>
                        <strong>시작하기</strong>
                    </Button>
                </Stack>
            </Grid>
            <Grid size={2} display="flex" justifyContent="center" alignItems="center">
                <Stack direction="row" spacing={2}>
                    {user ? (
                        <>
                            <Typography>{user.userName}님</Typography>
                            <LogoutButton after="/"></LogoutButton>
                        </>
                    ) : (
                        <>
                            <Button
                                variant="outlined"
                                onClick={login}
                                sx={{
                                    color: 'black',
                                    borderColor: 'black',
                                    // fontWeight: 'bold',
                                    '&:hover': {
                                        borderColor: 'black',
                                        backgroundColor: '#f5f5f5',
                                    },
                                }}
                            >
                                LOG IN
                            </Button>

                            <Button
                                variant="contained"
                                sx={{
                                    backgroundColor: 'black',
                                    color: 'white',
                                    // fontWeight: 'bold',
                                    '&:hover': {
                                        backgroundColor: '#333',
                                    },
                                }}
                            >
                                SIGN UP
                            </Button>
                        </>
                    )}
                </Stack>
            </Grid>
        </Grid>
    );
};

export default Navbar;
