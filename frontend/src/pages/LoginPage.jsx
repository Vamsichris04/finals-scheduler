import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import Header from '../components/Header';
import { logout } from '../services/api';
import './LoginPage.css';

async function validateUserEmail(email) {
  const response = await fetch('/api/users/validate', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ email }),
  });
  if (!response.ok) throw new Error('Invalid email or user not found');
  return response.json();
}

function LoginPage({ onLogin }) {
  const [email, setEmail] = useState('');
  const [error, setError] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const navigate = useNavigate();

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    setIsLoading(true);

    try {
      // Special case for admin
      if (email.toLowerCase() === 'sudersanamv@msoe.edu') {
        onLogin(email, 'admin');
        navigate('/admin');
        return;
      }

      // Regular user login
      const response = await validateUserEmail(email);
      if (response.user.role === 'admin') {
        navigate('/admin');
      } else {
        navigate('/user');
      }
      onLogin(email, response.user.role);
    } catch (err) {
      setError(err.message || 'Invalid email or user not found');
    } finally {
      setIsLoading(false);
    }
  };

  const handleLogoClick = () => {
    logout();
    setEmail('');
    setError('');
    navigate('/');
  };

  return (
    <div className="login-page">
      <Header />
      <div className="top-right-shape"></div>
      <div className="bottom-left-shape"></div>
      <div className="login-content-flex">
        <div className="login-info-box">
          <h1 className="title">MSOE IT Scheduler</h1>
          <p className="welcome-text">This tool helps streamline shift scheduling for the student manager. Whether you're entering your availability or generating the schedules, this platform will save you time.!!</p>
          <p className="welcome-subtext">At a low cost of take Vamsi out for a meal</p>
        </div>
        <div className="login-container">
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
                placeholder="MSOE Email Address" 
                className="email-input"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                required
                pattern="[a-z0-9._%+-]+@msoe\.edu$"
                title="Please enter a valid MSOE email address"
              />
            </div>
            <button 
              type="submit" 
              className="login-button"
              disabled={isLoading}
            >
              {isLoading ? 'Logging in...' : 'Login'}
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
    </div>
  );
}

export default LoginPage;
