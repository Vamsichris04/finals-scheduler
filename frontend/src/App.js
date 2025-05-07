import React, { useState } from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import LoginPage from './pages/LoginPage';
import UserPage from './pages/UserPage';
import AdminPage from './pages/AdminPage';
import './App.css';

function App() {
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [userRole, setUserRole] = useState('');
  const [userEmail, setUserEmail] = useState('');

  const handleLogin = (email, role) => {
    setIsAuthenticated(true);
    setUserRole(role);
    setUserEmail(email);
  };

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
              isAuthenticated ? 
                <UserPage userEmail={userEmail} /> : 
                <Navigate to="/" />
            } 
          />
          <Route 
            path="/admin" 
            element={
              isAuthenticated && userRole === 'admin' ? 
                <AdminPage /> : 
                <Navigate to="/" />
            } 
          />
        </Routes>
      </div>
    </Router>
  );
}

export default App;
