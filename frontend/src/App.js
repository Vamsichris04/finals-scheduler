import React, { useState, useEffect } from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { getCurrentUser, logout as apiLogout } from './services/api';
import LoginPage from './pages/LoginPage';
import UserPage from './pages/UserPage';
import AdminPage from './pages/AdminPage';
import TooBadPage from './pages/TooBadPage';
import './App.css';

function App() {
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [userRole, setUserRole] = useState('');
  const [userEmail, setUserEmail] = useState('');
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    // Check if user is already logged in
    const user = getCurrentUser();
    if (user) {
      setIsAuthenticated(true);
      setUserRole(user.role);
      setUserEmail(user.email);
    }
    setIsLoading(false);
  }, []);

  const handleLogin = (email, role) => {
    setIsAuthenticated(true);
    setUserRole(role);
    setUserEmail(email);
  };

  const handleLogout = () => {
    apiLogout();
    setIsAuthenticated(false);
    setUserRole('');
    setUserEmail('');
  };

  if (isLoading) {
    return <div>Loading...</div>;
  }

  return (
    <Router>
      <div className="App">
        <Routes>
          <Route 
            path="/" 
            element={
              isAuthenticated ? 
                (userRole === 'admin' ? <Navigate to="/admin" /> : <Navigate to="/user" />) : 
                <LoginPage onLogin={handleLogin} />
            } 
          />
          <Route 
            path="/user" 
            element={
              isAuthenticated && userRole === 'user' ? 
                <UserPage userEmail={userEmail} onLogout={handleLogout} /> : 
                <Navigate to="/" />
            } 
          />
          <Route 
            path="/admin" 
            element={
              isAuthenticated && userRole === 'admin' ? 
                <AdminPage onLogout={handleLogout} /> : 
                <Navigate to="/" />
            } 
          />
          <Route path="/too-bad" element={<TooBadPage />} />
        </Routes>
      </div>
    </Router>
  );
}

export default App;
