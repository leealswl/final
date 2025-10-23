import { Grid, Box, Stack } from '@mui/material'
import React from 'react'
import img from './실사1.gif'

const Banner = () => {
  return (
    <Grid ml={15} mr={15} mt={4}>
      <Stack direction="row" display={'flex'} justifyContent={'space-between'}>
        {/* <Grid sx={{width: '30%'}}>123</Grid> */}
        <Grid sx={{width: '100%'}}>
          <Box 
            component="img"
            src={img}
            alt="logo"
            sx={{
              width: "100%",
              height: "100%",
              objectFit: "cover",
              // borderRadius: 2,
              boxShadow: 3,
              display: "block",
            }}>
          </Box>
        </Grid>
      </Stack>
      
    </Grid>
  )
}

export default Banner