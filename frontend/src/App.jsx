import './App.css'
import Editpage from './pages/edit/Editpage'
import Homepage from './pages/home/Homepage'
import {Route, Routes} from 'react-router-dom'
import Login from './pages/login/Login';
import { useEffect } from 'react';
import { useFileStore } from './store/useFileStore';


function App() {
  const setCtx = useFileStore(s => s.setCurrentContext);

  useEffect(() => {
    // TODO: 실제 로그인/선택값으로 설정
    setCtx({ projectId: 1, userId: 'userId' });
  }, [setCtx]);

  return (
      <Routes>
        <Route path="/" element={<Homepage />} />
        <Route path="/edit" element={<Editpage />} />
        <Route path="/edit/:id" element={<Editpage />} />
        <Route path="/login" element={<Login />} />
    </Routes>
  );
}

export default App
