import './App.css';
import Homepage from './pages/home/Homepage';
import { Route, Routes } from 'react-router-dom';
import Login from './pages/login/Login';
import Layout from './pages/works/Layout';
import AnalyzeView from './pages/works/views/AnalyzeView';
import AnalyzeDashboard from './pages/works/views/AnalyzeDashboard';
import CreateView from './pages/works/views/CreateView';
import GenerateView from './pages/works/views/GenerateView';
import EditView from './pages/works/views/EditView';
import VerifyView from './pages/works/views/VerifyView';
import Dashboard from './pages/works/Dashboard';
import { useEffect } from 'react';
import { useFileStore } from './store/useFileStore';
// import { Dashboard } from '@mui/icons-material';

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

            <Route path="/main" element={<Dashboard />} />
            <Route path="/works" element={<Layout />}>
                <Route path="analyze" element={<AnalyzeView />} />
                {/* 2025-11-09 수연 추가: 분석 대시보드 라우트 */}
                <Route path="analyze/dashboard" element={<AnalyzeDashboard />} />
                <Route path="create" element={<CreateView />} />
                {/* 2025-11-09 suyeon: 제안서 초안 생성 페이지 라우트 추가 */}
                <Route path="generate" element={<GenerateView />} />
                <Route path="edit" element={<EditView />} />
                <Route path="edit/:docId" element={<EditView />} />
                <Route path="verify" element={<VerifyView />} />
            </Route>
        </Routes>
    );
}

export default App;
