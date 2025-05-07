// Mock API service for demonstration purposes
// In a real application, this would make actual API calls to a backend server

// Mock data
const mockUsers = [
  { id: '1', name: 'John Doe', email: 'john.doe@msoe.edu', role: 'user' },
  { id: '2', name: 'Jane Smith', email: 'jane.smith@msoe.edu', role: 'user' },
  { id: '3', name: 'Admin User', email: 'admin@msoe.edu', role: 'admin' }
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
  await delay(800);
  return [...mockUsers];
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
