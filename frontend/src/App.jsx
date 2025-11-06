import './App.css';
import Homepage from './pages/home/Homepage';
import { Route, Routes } from 'react-router-dom';
import Login from './pages/login/Login';
import Layout from './pages/works/Layout';
import AnalyzeView from './pages/works/views/AnalyzeView';
import CreateView from './pages/works/views/CreateView';
import EditView from './pages/works/views/EditView';
import VerifyView from './pages/works/views/VerifyView';
import { useEffect } from 'react';
import { useFileStore } from './store/useFileStore';
import AnalyzeSession from './pages/works/views/AnalyzeSession';

function App() {
    const setCtx = useFileStore((s) => s.setCurrentContext);

    useEffect(() => {
        // TODO: 실제 로그인/선택값으로 설정
        setCtx({ projectId: 1, userId: 'userId' });
        // 임시 하드코딩 분석에이전트 관련
        // setCtx({ projectId: 1, userId: '1' });
    }, [setCtx]);

    return (
        <Routes>
            <Route path="/" element={<Homepage />} />
            <Route path="/login" element={<Login />} />

            <Route path="/works" element={<Layout />}>
                <Route path="analyze" element={<AnalyzeView />} />
                <Route path="analyze/:analyzeId" element={<AnalyzeSession />} />
                <Route path="create" element={<CreateView />} />
                <Route path="edit" element={<EditView />} />
                <Route path="edit/:docId" element={<EditView />} />
                <Route path="verify" element={<VerifyView />} />
            </Route>
        </Routes>
    );
}

export default App;
