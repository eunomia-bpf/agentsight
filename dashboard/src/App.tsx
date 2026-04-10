import React from 'react';
import { HashRouter, Routes, Route } from 'react-router-dom';
import { NavBar } from './components/NavBar';
import { AgentHealthSidebar } from './components/AgentHealthSidebar';
import { ConversationList } from './pages/ConversationList';
import { AtifViewerPage } from './pages/AtifViewerPage';

const App: React.FC = () => {
  return (
    <HashRouter>
      <div className="min-h-screen bg-gray-50 flex flex-col">
        <NavBar />
        <div className="flex flex-1 overflow-hidden">
          <main className="flex-1 overflow-auto">
            <Routes>
              <Route path="/" element={<ConversationList />} />
              <Route path="/atif" element={<AtifViewerPage />} />
            </Routes>
          </main>
          <AgentHealthSidebar />
        </div>
      </div>
    </HashRouter>
  );
};

export default App;
