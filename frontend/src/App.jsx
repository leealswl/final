import './App.css'
import Editpage from './pages/edit/Editpage'
import Homepage from './pages/home/Homepage'
import {Route, Routes} from 'react-router-dom'

function App() {

  return (
      <Routes>
        <Route path="/" element={<Homepage />} />
        <Route path="/edit" element={<Editpage />} />
    </Routes>
  );
}

export default App
