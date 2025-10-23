import React from 'react'
import {Button,  Grid, Stack, Box} from "@mui/material";
import logo from './앨리스.png'

const Navbar = () => {

  const edit =() => {
    window.location.href="/edit"
  }
  return (
    <Grid container pt={3} pb={3} borderBottom={1} borderColor={'black'} ml={15} mr={15}>

      <Grid size={1} display="flex" justifyContent="center" alignItems="center">
        <Box
          component="img"
          src={logo}
          alt="logo"
          sx={{
            width: 30,
            height: "auto",
            borderRadius: 2,
            boxShadow: 3,
          }}
    />
      </Grid>
      <Grid size={9} display="flex" justifyContent="center" alignItems="center">
        <Stack direction="row" spacing={3}>
          <Button size='large' color='warning'>카탈로그</Button>
          <Button size='large' color='success'>요금제</Button>
          <Button size='large' color='primary'>AI</Button>
          <Button size='large' color='error'>고객지원</Button>
          <Button size='large' color='secondary' onClick={edit}><strong>시작하기</strong></Button>
        </Stack>
      </Grid>
      <Grid size={2} display="flex" justifyContent="center" alignItems="center">
        <Stack direction="row" spacing={2}>
          <Button variant="outlined">LOG IN</Button>
          <Button variant="contained">SIGN UP</Button>
        </Stack>
      </Grid>
    </Grid>
  )
}

export default Navbar