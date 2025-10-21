import React from 'react'
import Navbar from './components/Navbar'

const Homepage = () => {

  const editpage =()=>{
    window.location.href='/edit'
  }
  return (
<<<<<<< HEAD
    <div>Homepage - 배치만 
      <button onClick={editpage}>에딧페이지 </button>
      {/* npm i @mui/material @emotion/react @emotion/styled @mui/icons-material @mui/x-tree-view */}
=======
    <div>
        <Navbar />


>>>>>>> b0c6a8c (navbar 수정)
    </div>
  )
}

export default Homepage