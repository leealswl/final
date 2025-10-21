import React from 'react'

const Homepage = () => {

  const editpage =()=>{
    window.location.href='/edit'
  }
  return (
    <div>Homepage - 배치만 
      <button onClick={editpage}>에딧페이지 </button>
      {/* npm i @mui/material @emotion/react @emotion/styled @mui/icons-material @mui/x-tree-view */}
    </div>
  )
}

export default Homepage