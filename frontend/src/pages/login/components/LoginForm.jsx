import { Box, Button, FormControl, FormLabel, Grid, Input, Stack, TextField, Typography } from '@mui/material'
import React from 'react'
import LoginIcon from '@mui/icons-material/Login';
import logo from '../../home/components/앨리스.png'

const LoginForm = () => {
    const home = () => {
    window.location.href="/"
  }

  const login = () => {

  }

    return (
        <Grid display={'flex'} justifyContent={'center'} alignItems={'center'} sx={{height: '100vh'}}>
            <Box
                display={'flex'}
                flexDirection={'column'}
                justifyContent={'center'}
                alignItems={'center'}
                border={1}
                component="form"
                sx={{ '& .MuiTextField-root': { }, width: '400px', height: '600px'}}
                noValidate
                autoComplete="off">
                    <Box
                    onClick={home}
                    component="img"
                              src={logo}
                              alt="logo"
                              sx={{
                                width: 30,
                                height: "auto",
                                borderRadius: 2,
                                boxShadow: 3,
                                cursor: 'pointer',
                              }}>

                    </Box>
                    <Typography fontSize={30}>Welcome</Typography>
                    <TextField
                        required
                        id="outlined-email-input"
                        label="email"
                        margin='normal'
                        sx={{width:'60%'}}
                    />
                    <TextField
                        required
                        id="outlined-password-input"
                        label="Password"
                        type="password"
                        margin='normal'
                        autoComplete="current-password"
                        sx={{width:'60%'}}
                    />
                    <Stack spacing={2} sx={{width:'100%'}} mt={3} display={'flex'} alignItems={'center'}>
                        <Button variant='outlined' onClick={login} sx={{width:'60%', height: '40%', color: 'black', borderColor: 'black', '&:hover':{borderColor:'black', backgroundColor:'#f5f5f5'}}}><LoginIcon sx={{marginRight:'10px'}}/>Login</Button>
                        <Typography>1234</Typography>
                        <Grid display={'flex'} justifyContent={'center'}>
                            <Typography onClick={home} sx={{cursor:'pointer', marginRight:'5px'}}>아이디</Typography>/<Typography onClick={home} sx={{cursor:'pointer', marginLeft:'5px'}}>비밀번호 찾기</Typography>
                        </Grid>
                    </Stack>
            </Box>
        </Grid>
    )
  }

export default LoginForm