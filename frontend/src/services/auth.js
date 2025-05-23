import axios from 'axios';


const API_URL = process.env.REACT_APP_API_URL || 'http://localhost:3001/api';

export const validateUserEmail = async (email) => {
  try {
    const cleanedEmail = email.trim().toLowerCase();
    const response = await fetch('/api/users/validate', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ email: cleanedEmail }),
    });
    if (!response.ok) throw new Error('Invalid email or user not found');
    return response.json();
  } catch (error) {
    if (error.response) {
      throw new Error(error.response.data.message || 'User not found');
    }
    throw new Error('Network error occurred');
  }
};

export const login = async (email) => {
  try {
    const response = await axios.post(`${API_URL}/auth/login`, { email });
    if (response.data.token) {
      localStorage.setItem('user', JSON.stringify(response.data));
    }
    return response.data;
  } catch (error) {
    if (error.response) {
      throw new Error(error.response.data.message || 'Login failed');
    }
    throw new Error('Network error occurred');
  }
};

export const logout = () => {
  localStorage.removeItem('user');
};

export const getCurrentUser = () => {
  const userStr = localStorage.getItem('user');
  if (userStr) return JSON.parse(userStr);
  return null;
}; 