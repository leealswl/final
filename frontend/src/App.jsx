import './App.css'
import Editpage from './pages/edit/Editpage'
import Homepage from './pages/home/Homepage'
import {Route, Routes} from 'react-router-dom'
import Login from './pages/login/Login';

function App() {

  return (
      <Routes>
        <Route path="/" element={<Homepage />} />
        <Route path="/edit" element={<Editpage />} />
        <Route path="/login" element={<Login />} />
    </Routes>
  );
}

export default App
