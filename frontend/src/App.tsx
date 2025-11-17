import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import ChatContainer from './components/ChatContainer';
import WhiteAgentChat from './pages/WhiteAgentChat';
import Navigation from './components/Navigation';

function App() {
  return (
    <Router>
      <div className="flex flex-col h-full bg-background">
        <Navigation />
        <div className="flex-1 overflow-hidden">
          <Routes>
            <Route path="/" element={<ChatContainer />} />
            <Route path="/white-agent" element={<WhiteAgentChat />} />
          </Routes>
        </div>
      </div>
    </Router>
  );
}

export default App;
