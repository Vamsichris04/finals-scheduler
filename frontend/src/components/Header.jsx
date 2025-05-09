import React from 'react';
import { useNavigate } from 'react-router-dom';
import msoeLogo from '../assets/MSOE.png';
import './Header.css';

function Header({ onLogout }) {
  const navigate = useNavigate();

  const handleLogoClick = () => {
    if (onLogout) {
      onLogout();
    }
    navigate('/login');
  };

  return (
    <header className="header">
      <div className="header-container">
        <div className="logo-container" onClick={handleLogoClick}>
          <img src={msoeLogo} alt="MSOE Logo" className="logo" />
        </div>
        <div className="header-title-center">
          <h1 className="header-title">MSOE IT Scheduler</h1>
        </div>
      </div>
    </header>
  );
}

export default Header;
