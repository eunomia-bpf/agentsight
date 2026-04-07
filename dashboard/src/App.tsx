import React from 'react';
import { HashRouter, Routes, Route } from 'react-router-dom';
import { NavBar } from './components/NavBar';
import { ConversationList } from './pages/ConversationList';
import { TraceEventsPage } from './pages/TraceEventsPage';
import { TraceDetailPage } from './pages/TraceDetailPage';
import { AtifViewerPage } from './pages/AtifViewerPage';

const App: React.FC = () => {
  return (
    <HashRouter>
      <div className="min-h-screen bg-gray-50">
        <NavBar />
        <Routes>
          <Route path="/" element={<ConversationList />} />
          <Route path="/trace-events" element={<TraceEventsPage />} />
          <Route path="/trace/:traceId" element={<TraceDetailPage />} />
          <Route path="/atif" element={<AtifViewerPage />} />
        </Routes>
      </div>
    </HashRouter>
  );
};

export default App;
