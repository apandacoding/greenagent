import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import ChatContainer from './components/ChatContainer';
import WhiteAgentChat from './pages/WhiteAgentChat';
import GreenAgentChat from './pages/GreenAgentChat';
import Navigation from './components/Navigation';
import ErrorBoundary from './components/ErrorBoundary';

function App() {
  return (
    <ErrorBoundary>
      <Router>
        <div className="flex flex-col h-full bg-background">
          <Navigation />
          <div className="flex-1 overflow-hidden">
            <Routes>
              <Route path="/" element={<GreenAgentChat />} />
              <Route path="/green-agent" element={<GreenAgentChat />} />
              <Route path="/white-agent" element={<WhiteAgentChat />} />
              <Route path="/legacy" element={<ChatContainer />} />
            </Routes>
          </div>
        </div>
      </Router>
    </ErrorBoundary>
  );
}

export default App;
