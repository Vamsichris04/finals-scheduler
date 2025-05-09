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
    <>
      <header className="header">
        <div className="logo-container" onClick={handleLogoClick}>
          <img src={msoeLogo} alt="MSOE Logo" className="logo" />
        </div>
      </header>
      <div className="text-bubble">
        <h1>MSOE IT Scheduler</h1>
      </div>
    </>
  );
}

export default Header;
