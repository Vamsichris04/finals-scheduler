// Mock API service for demonstration purposes
// In a real application, this would make actual API calls to a backend server
import axios from 'axios';

// Mock data
const mockUsers = [
  { id: '1', name: 'John Doe', email: 'john.doe@msoe.edu', role: 'user' },
  { id: '2', name: 'Jane Smith', email: 'jane.smith@msoe.edu', role: 'user' },
  { id: '3', name: 'Admin User', email: 'admin@msoe.edu', role: 'admin' },
  { id: '4', name: 'User 4', email: 'user4@msoe.edu', role: 'user' },
  { id: '5', name: 'User 5', email: 'user5@msoe.edu', role: 'user' },
  { id: '6', name: 'User 6', email: 'user6@msoe.edu', role: 'user' },
  { id: '7', name: 'User 7', email: 'user7@msoe.edu', role: 'user' },
  { id: '8', name: 'User 8', email: 'user8@msoe.edu', role: 'user' },
  { id: '9', name: 'User 9', email: 'user9@msoe.edu', role: 'user' },
  { id: '10', name: 'User 10', email: 'user10@msoe.edu', role: 'user' }
];

const mockBusyTimes = {
  '1': {
    'Monday-9:00 am': 'Class: CS101',
    'Monday-10:00 am': 'Class: CS101',
    'Wednesday-9:00 am': 'Class: CS101',
    'Wednesday-10:00 am': 'Class: CS101',
    'Friday-9:00 am': 'Class: CS101',
    'Friday-10:00 am': 'Class: CS101',
    'Tuesday-1:00 pm': 'Meeting with advisor',
    'Thursday-3:00 pm': 'Study group'
  },
  '2': {
    'Monday-1:00 pm': 'Class: ENG201',
    'Monday-2:00 pm': 'Class: ENG201',
    'Wednesday-1:00 pm': 'Class: ENG201',
    'Wednesday-2:00 pm': 'Class: ENG201',
    'Friday-1:00 pm': 'Class: ENG201',
    'Friday-2:00 pm': 'Class: ENG201',
    'Tuesday-10:00 am': 'Work shift',
    'Tuesday-11:00 am': 'Work shift',
    'Thursday-10:00 am': 'Work shift',
    'Thursday-11:00 am': 'Work shift'
  }
};

// Simulate API delay
const delay = (ms) => new Promise(resolve => setTimeout(resolve, ms));

// API functions
export const checkUserRole = async (email) => {
  await delay(800);
  const user = mockUsers.find(u => u.email.toLowerCase() === email.toLowerCase());
  if (!user) {
    throw new Error('User not found');
  }
  return user.role;
};

export const fetchUsers = async () => {
  const response = await fetch('http://localhost:5000/api/users');
  if (!response.ok) throw new Error('Failed to fetch users');
  return response.json();
};

export const fetchUserBusyTimes = async (userId) => {
  await delay(800);
  return mockBusyTimes[userId] || {};
};

export const saveBusyTimes = async (userId, busyTimes) => {
  await delay(800);
  mockBusyTimes[userId] = { ...busyTimes };
  return true;
};

export const addUser = async (userData) => {
  await delay(800);
  const newUser = {
    id: String(mockUsers.length + 1),
    name: userData.name,
    email: userData.email,
    role: 'user'
  };
  mockUsers.push(newUser);
  return newUser;
};

export const deleteUser = async (userId) => {
  await delay(800);
  const index = mockUsers.findIndex(u => u.id === userId);
  if (index !== -1) {
    mockUsers.splice(index, 1);
    delete mockBusyTimes[userId];
    return true;
  }
  throw new Error('User not found');
};

export const updateUser = async (userId, userData) => {
  try {
    const response = await api.put(`/users/${userId}`, userData);
    return response.data;
  } catch (error) {
    throw error.response?.data || { message: 'Failed to update user' };
  }
};

const API_URL = process.env.REACT_APP_API_URL || 'http://localhost:5000/api';

// Create axios instance with default config
const api = axios.create({
  baseURL: API_URL,
  headers: {
    'Content-Type': 'application/json'
  }
});

// Add token to requests if it exists
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

export const login = async (email) => {
  try {
    const response = await api.post('/users/validate', { email });
    if (response.data.success) {
      localStorage.setItem('user', JSON.stringify(response.data.user));
    }
    return response.data;
  } catch (error) {
    throw error.response?.data || { message: 'An error occurred during login' };
  }
};

export const logout = () => {
  localStorage.removeItem('token');
  localStorage.removeItem('user');
};

export const getCurrentUser = () => {
  const userStr = localStorage.getItem('user');
  if (userStr) return JSON.parse(userStr);
  return null;
};

export const submitAvailability = async (userId, availability) => {
  try {
    const response = await api.post('/availability', { userId, availability });
    return response.data;
  } catch (error) {
    throw error.response?.data || { message: 'Failed to submit availability' };
  }
};

export const getUsers = async () => {
  try {
    const response = await api.get('/users');
    return response.data;
  } catch (error) {
    throw error.response?.data || { message: 'Failed to fetch users' };
  }
};
