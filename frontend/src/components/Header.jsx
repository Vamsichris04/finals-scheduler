import React from 'react';
import './Header.css';
import msoeLogo from '../assets/MSOE.png';

function Header() {
  return (
    <header className="header">
      <div className="header-container">
        <div className="logo-container">
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
