import 'aos/dist/aos.css';
import './App.css';
import Homepage from './pages/home/Homepage';
import { Route, Routes } from 'react-router-dom';
import Login from './pages/login/Login';
import Layout from './pages/works/Layout';
import AnalyzeView from './pages/works/analyze/AnalyzeView';
import AnalyzeDashboard from './pages/works/analyze/AnalyzeDashboard';
import CreateView from './pages/works/create/CreateView';
import GenerateView from './pages/works/create/GenerateView';
import EditView from './pages/works/edit/EditView';
import VerifyView from './pages/works/verify/VerifyView';
import Dashboard from './pages/main/Dashboard';
import { useEffect } from 'react';
import AOS from 'aos';

function App() {
    useEffect(() => {
        AOS.init({
            duration: 1000,
            once: true,
            easing: 'ease-out',
        });
    }, []);

    return (
        <Routes>
            <Route path="/" element={<Homepage />} />
            <Route path="/login" element={<Login />} />

            <Route path="/main" element={<Dashboard />} />

            <Route path="/works" element={<Layout />}>
                <Route path="analyze" element={<AnalyzeView />} />
                <Route path="analyze/dashboard" element={<AnalyzeDashboard />} />
                <Route path="create" element={<CreateView />} />
                <Route path="generate" element={<GenerateView />} />
                <Route path="edit" element={<EditView />} />
                <Route path="edit/:docId" element={<EditView />} />
                <Route path="verify" element={<VerifyView />} />
            </Route>
        </Routes>
    );
}

export default App;
