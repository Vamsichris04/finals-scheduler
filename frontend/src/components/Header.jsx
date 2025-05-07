import React from 'react';
import { useNavigate } from 'react-router-dom';
import './Header.css';
import msoeLogo from '../assets/MSOE.png';

function Header({ onLogout }) {
  const navigate = useNavigate();

  const handleLogoClick = () => {
    // Call the onLogout function if provided
    if (onLogout) {
      onLogout();
    }
    // Navigate to login page
    navigate('/');
  };

  return (
    <header className="header">
      <div className="header-container">
        <div className="logo-container" onClick={handleLogoClick} style={{ cursor: 'pointer' }}>
          <img 
            src={msoeLogo} 
            alt="MSOE University Logo" 
            className="msoe-logo" 
          />
        </div>
        <div className="title-container">
          <h1 className="title">MSOE IT Scheduler</h1>
        </div>
      </div>
    </header>
  );
}

export default Header;
