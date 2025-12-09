import { Box, Button, FormControl, FormLabel, Grid, Input, Stack, TextField, Typography, IconButton, InputAdornment } from '@mui/material';
import { Visibility, VisibilityOff } from '@mui/icons-material';
import React, { useState } from 'react';
import LoginIcon from '@mui/icons-material/Login';
import logo from '../../home/img/nav_logo.png';
import { useNavigate } from 'react-router-dom';
import useSignIn from '../../../hooks/useSignIn';

const LoginForm = () => {
    const navigate = useNavigate();

    const home = () => {
        navigate('/');
    };

    const { mutate: signIn, isPending } = useSignIn({
        onSuccess: () => {
            alert('로그인 성공!');
            navigate('/');
        },
        onError: (error) => {
            // console.log('전체 error 객체:', error);
            // console.log('error.response:', error.response);
            // console.log('error.response.status:', error.response?.status);
            // console.log('error.response.data:', error.response?.data);
            // if (error.response?.status === 401) {
            //     alert('아이디 또는 비밀번호가 올바르지 않습니다.');
            // } else {
            //     alert('아이디 또는 비밀번호가 올바르지 않습니다.');
            //     // alert('서버 오류: ' + error.message);
            // }
            alert(error);
        },
    });

    const [values, setValues] = useState({ email: '', password: '', showPw: false });

    const onChange = (e) => {
        const { name, value } = e.target;
        setValues((v) => ({ ...v, [name]: value }));
    };
    const toggleShowPw = () => setValues((v) => ({ ...v, showPw: !v.showPw }));

    const canSubmit = values.email.trim() && values.password.trim();

    const handleSubmit = (e) => {
        e.preventDefault();
        if (!canSubmit || isPending) return;
        signIn({ userId: values.email, userPw: values.password });
    };

    const inputStyle = {
        bgcolor: '#f1f3f5',
        borderRadius: 1,
        '& .MuiFilledInput-underline:before, & .MuiFilledInput-underline:after': {
            borderBottom: 'none',
        },
        '&:hover': { bgcolor: '#eef0f2' },
        minHeight: 48,
    };

    return (
        <Box sx={{ position: 'fixed', inset: 0, bgcolor: '#f1f3f5', display: 'grid', placeItems: 'center', p: { xs: 2, sm: 4 }, overflow: 'hidden' }}>
            <Grid display={'flex'} justifyContent={'center'} alignItems={'center'} sx={{ height: '100vh' }}>
                <Box
                    display={'flex'}
                    flexDirection={'column'}
                    justifyContent={'center'}
                    alignItems={'center'}
                    border={1}
                    component="form"
                    bgcolor={'white'}
                    onSubmit={handleSubmit}
                    sx={{ '& .MuiTextField-root': {}, width: '400px', height: '600px', borderRadius: 2 }}
                    noValidate
                    autoComplete="off"
                >
                    <Stack
                        mb={3}
                        onClick={home}
                        display={'flex'}
                        spacing={2}
                        direction="row"
                        sx={{
                            cursor: 'pointer',
                            transition: 'transform 0.2s', // 부드러운 애니메이션
                            '&:hover': {
                                transform: 'scale(1.1)', // 호버 시 10% 확대
                            },
                        }}
                    >
                        <Box
                            component="img"
                            src={logo}
                            alt="logo"
                            sx={{
                                width: 40,
                                height: 'auto',
                            }}
                        ></Box>
                        <Typography fontFamily={'SeoulAlrim-Bold'} fontSize={30}>
                            PALADOC
                        </Typography>
                        <Box
                            component="img"
                            src={logo}
                            alt="logo"
                            sx={{
                                width: 40,
                                height: 'auto',
                            }}
                        ></Box>
                    </Stack>

                    <TextField required id="outlined-email-input" label="email" name="email" value={values.email} onChange={onChange} margin="normal" sx={{ width: '60%' }} />
                    <TextField
                        name="password"
                        required
                        id="outlined-password-input"
                        label="Password"
                        type={values.showPw ? 'text' : 'password'}
                        value={values.password}
                        onChange={onChange}
                        margin="normal"
                        autoComplete="current-password"
                        sx={{ width: '60%' }}
                        InputProps={{
                            sx: inputStyle,
                            endAdornment: (
                                <InputAdornment position="end">
                                    <IconButton aria-label="비밀번호 보기" onClick={toggleShowPw} edge="end">
                                        {values.showPw ? <VisibilityOff /> : <Visibility />}
                                    </IconButton>
                                </InputAdornment>
                            ),
                        }}
                    />
                    <Stack spacing={2} sx={{ width: '100%' }} mt={3} display={'flex'} alignItems={'center'}>
                        <Button
                            type="submit"
                            variant="outlined"
                            disabled={!canSubmit}
                            sx={{ width: '60%', height: '40%', color: 'black', borderColor: 'black', '&:hover': { borderColor: 'black', backgroundColor: '#f5f5f5' } }}
                        >
                            <LoginIcon sx={{ marginRight: '10px' }} />
                            Login
                        </Button>
                        {/* <Typography>1234</Typography> */}
                        <Grid display={'flex'} justifyContent={'center'}>
                            <Typography onClick={home} sx={{ cursor: 'pointer', marginRight: '5px' }}>
                                아이디
                            </Typography>
                            /
                            <Typography onClick={home} sx={{ cursor: 'pointer', marginLeft: '5px' }}>
                                비밀번호 찾기
                            </Typography>
                        </Grid>
                        <Grid>
                            <Typography onClick={home} sx={{ cursor: 'pointer', marginRight: '5px' }}>
                                아이디가 없으신가요? 회원가입
                            </Typography>
                        </Grid>
                    </Stack>
                </Box>
            </Grid>
        </Box>
    );
};

export default LoginForm;
