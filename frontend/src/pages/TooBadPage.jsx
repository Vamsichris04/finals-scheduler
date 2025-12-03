import React from 'react';
import { useNavigate } from 'react-router-dom';
import Header from '../components/Header';
import './TooBadPage.css';

function TooBadPage() {
  const navigate = useNavigate();

  const handleLogoClick = () => {
    navigate('/');
  };

  return (
    <div className="too-bad-page">
      <Header onLogoClick={handleLogoClick} />
      <div className="too-bad-content">
        <h1>Too bad...</h1>
      </div>
    </div>
  );
}

export default TooBadPage; 