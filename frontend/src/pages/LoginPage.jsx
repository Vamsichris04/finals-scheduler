import React, { useState } from 'react';
import { validateEmail } from '../utils/validation';
import { checkUserRole } from '../services/api';
import './LoginPage.css';

function LoginPage({ onLogin }) {
  const [email, setEmail] = useState('');
  const [error, setError] = useState('');
  const [isLoading, setIsLoading] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    
    // Validate email format
    if (!validateEmail(email)) {
      setError('Please enter a valid MSOE email address');
      return;
    }
    
    setIsLoading(true);
    
    try {
      // Check if user exists and get role
      const role = await checkUserRole(email);
      onLogin(email, role);
    } catch (err) {
      setError('Invalid email or user not found');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="login-page">
      <div className="top-right-shape"></div>
      <div className="bottom-left-shape"></div>
      
      <div className="login-container">
        <div className="header">
          <div className="logo-container">
            <img 
              src="/msoe-logo.png" 
              alt="MSOE University Logo" 
              className="msoe-logo" 
            />
          </div>
          <div className="title-container">
            <h1 className="title">MSOE IT Scheduler</h1>
            <p className="welcome-text">Some dialogue to welcome the users !!</p>
            <p className="welcome-subtext">Blah Blah Blah ...</p>
          </div>
        </div>
        
        <form className="login-form" onSubmit={handleSubmit}>
          <div className="user-icon">
            <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
              <path d="M12 2a5 5 0 0 1 5 5c0 2.76-2.24 5-5 5S7 9.76 7 7a5 5 0 0 1 5-5z"></path>
              <path d="M12 12c-5.52 0-10 4.48-10 10h20c0-5.52-4.48-10-10-10z"></path>
            </svg>
          </div>
          
          {error && <div className="error-message">{error}</div>}
          
          <div className="input-container">
            <input 
              type="email" 
              placeholder="MSOE EMAIL ADDRESS" 
              className="email-input"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              required
            />
          </div>
          
          <button 
            type="submit" 
            className="login-button"
            disabled={isLoading}
          >
            {isLoading ? 'LOGGING IN...' : 'LOGIN'}
          </button>
          
          <div className="forgot-username">
            <a href="#" className="forgot-link">Forgot Username?</a>
          </div>
          
          <div className="not-implemented">
            ...Too bad I dont have that implemented yet :(
          </div>
        </form>
      </div>
    </div>
  );
}

export default LoginPage;
