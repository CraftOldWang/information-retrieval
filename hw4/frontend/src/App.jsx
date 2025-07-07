import React from 'react';
import { Routes, Route } from 'react-router-dom';
import './App.css';

// 导入页面组件
import HomePage from './pages/HomePage';
import SearchResultsPage from './pages/SearchResultsPage';
import DocumentSearchPage from './pages/DocumentSearchPage';
import LoginPage from './pages/LoginPage';
import RegisterPage from './pages/RegisterPage';
import ProfilePage from './pages/ProfilePage';
import SnapshotPage from './pages/SnapshotPage';

// 导入上下文提供者
import { AuthProvider } from './contexts/AuthContext';

function App() {
  return (
    <AuthProvider>
      <div className="App">
        <Routes>
          <Route path="/" element={<HomePage />} />
          <Route path="/search" element={<SearchResultsPage />} />
          <Route path="/documents" element={<DocumentSearchPage />} />
          <Route path="/login" element={<LoginPage />} />
          <Route path="/register" element={<RegisterPage />} />
          <Route path="/profile" element={<ProfilePage />} />
          <Route path="/snapshot/:urlId" element={<SnapshotPage />} />
        </Routes>
      </div>
    </AuthProvider>
  );
}

export default App;