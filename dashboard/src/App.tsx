import React from 'react';
import { HashRouter, Routes, Route } from 'react-router-dom';
import { ConversationList } from './pages/ConversationList';
import { TraceEventsPage } from './pages/TraceEventsPage';
import { TraceDetailPage } from './pages/TraceDetailPage';

const App: React.FC = () => {
  return (
    <HashRouter>
      <Routes>
        <Route path="/" element={<ConversationList />} />
        <Route path="/trace-events" element={<TraceEventsPage />} />
        <Route path="/trace/:traceId" element={<TraceDetailPage />} />
      </Routes>
    </HashRouter>
  );
};

export default App;
