import React, { useState, useEffect } from 'react';
import Header from '../components/Header';
import UserDropdown from '../components/UserDropdown';
import Calendar from '../components/Calendar';
import { fetchUsers, fetchUserBusyTimes, saveBusyTimes } from '../services/api';
import './UserPage.css';

function UserPage({ userEmail }) {
  const [users, setUsers] = useState([]);
  const [selectedUser, setSelectedUser] = useState('');
  const [busyTimes, setBusyTimes] = useState({});
  const [isLoading, setIsLoading] = useState(true);
  const [message, setMessage] = useState('');

  useEffect(() => {
    const loadUsers = async () => {
      try {
        const userData = await fetchUsers();
        setUsers(userData);
        setIsLoading(false);
      } catch (error) {
        console.error('Error loading users:', error);
        setMessage('Failed to load users. Please try again later.');
        setIsLoading(false);
      }
    };
    
    loadUsers();
  }, []);

  useEffect(() => {
    if (selectedUser) {
      const loadBusyTimes = async () => {
        setIsLoading(true);
        try {
          const times = await fetchUserBusyTimes(selectedUser);
          setBusyTimes(times);
        } catch (error) {
          console.error('Error loading busy times:', error);
          setMessage('Failed to load schedule. Please try again later.');
        } finally {
          setIsLoading(false);
        }
      };
      
      loadBusyTimes();
    }
  }, [selectedUser]);

  const handleSelectUser = (userId) => {
    setSelectedUser(userId);
  };

  const handleUpdateBusyTimes = async (updatedTimes) => {
    setIsLoading(true);
    try {
      await saveBusyTimes(selectedUser, updatedTimes);
      setBusyTimes(updatedTimes);
      setMessage('Schedule saved successfully!');
      
      // Clear message after 3 seconds
      setTimeout(() => {
        setMessage('');
      }, 3000);
    } catch (error) {
      console.error('Error saving busy times:', error);
      setMessage('Failed to save schedule. Please try again.');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="user-page">
      <Header />
      
      <div className="user-page-content">
        <div className="welcome-message"><h2>Welcome to the MSOE IT Scheduler</h2>
          <p>Please select your name and update your busy times for the week.</p>
        </div>
        
        {message && (
          <div className={`message ${message.includes('Failed') ? 'error' : 'success'}`}>
            {message}
          </div>
        )}
        
        {isLoading ? (
          <div className="loading">Loading...</div>
        ) : (
          <div className="user-page-layout">
            <div className="sidebar">
              <UserDropdown 
                users={users}
                selectedUser={selectedUser}
                onSelectUser={handleSelectUser}
              />
            </div>
            
            <div className="main-content">
              {selectedUser ? (
                <Calendar 
                  busyTimes={busyTimes}
                  onUpdateBusyTimes={handleUpdateBusyTimes}
                />
              ) : (
                <div className="no-selection">
                  <p>Please select a user from the list to view and update their schedule.</p>
                </div>
              )}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

export default UserPage;
