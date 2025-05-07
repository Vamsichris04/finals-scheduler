import React, { useState, useEffect } from 'react';
import Header from '../components/Header';
import UserDropdown from '../components/UserDropdown';
import Calendar from '../components/Calendar';
import ConfirmationModal from '../components/ConfirmationModal';
import { fetchUsers, fetchUserBusyTimes, deleteUser, addUser } from '../services/api';
import './AdminPage.css';

function AdminPage({ onLogout }) {
  const [users, setUsers] = useState([]);
  const [selectedUser, setSelectedUser] = useState('');
  const [busyTimes, setBusyTimes] = useState({});
  const [isLoading, setIsLoading] = useState(true);
  const [message, setMessage] = useState('');
  const [showAddUserForm, setShowAddUserForm] = useState(false);
  const [newUserName, setNewUserName] = useState('');
  const [newUserEmail, setNewUserEmail] = useState('');
  const [showDeleteModal, setShowDeleteModal] = useState(false);

  useEffect(() => {
    loadUsers();
  }, []);

  useEffect(() => {
    if (selectedUser) {
      loadUserBusyTimes();
    }
  }, [selectedUser]);

  const loadUsers = async () => {
    setIsLoading(true);
    try {
      const userData = await fetchUsers();
      setUsers(userData);
    } catch (error) {
      console.error('Error loading users:', error);
      setMessage('Failed to load users. Please try again later.');
    } finally {
      setIsLoading(false);
    }
  };

  const loadUserBusyTimes = async () => {
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

  const handleSelectUser = (userId) => {
    setSelectedUser(userId);
  };

  const handleAddUser = async (e) => {
    e.preventDefault();
    setIsLoading(true);
    
    try {
      await addUser({ name: newUserName, email: newUserEmail });
      setMessage('User added successfully!');
      setNewUserName('');
      setNewUserEmail('');
      setShowAddUserForm(false);
      await loadUsers();
    } catch (error) {
      console.error('Error adding user:', error);
      setMessage('Failed to add user. Please try again.');
    } finally {
      setIsLoading(false);
    }
  };

  const handleDeleteUser = async () => {
    setIsLoading(true);
    try {
      await deleteUser(selectedUser);
      setMessage('User deleted successfully!');
      setSelectedUser('');
      setBusyTimes({});
      setShowDeleteModal(false);
      await loadUsers();
    } catch (error) {
      console.error('Error deleting user:', error);
      setMessage('Failed to delete user. Please try again.');
    } finally {
      setIsLoading(false);
    }
  };

  const clearMessage = () => {
    setTimeout(() => {
      setMessage('');
    }, 3000);
  };

  return (
    <div className="admin-page">
      <Header onLogout={onLogout} />
      
      <div className="admin-page-content">
        <div className="admin-header">
          <h2>Admin Dashboard</h2>
          <p>Manage users and view their schedules</p>
        </div>
        
        {message && (
          <div className={`message ${message.includes('Failed') ? 'error' : 'success'}`}>
            {message}
          </div>
        )}
        
        <div className="admin-actions">
          <button 
            className="btn btn-primary"
            onClick={() => setShowAddUserForm(!showAddUserForm)}
          >
            {showAddUserForm ? 'Cancel' : 'Add New User'}
          </button>
          
          {selectedUser && (
            <button 
              className="btn btn-danger"
              onClick={() => setShowDeleteModal(true)}
            >
              Delete Selected User
            </button>
          )}
        </div>
        
        {showAddUserForm && (
          <div className="add-user-form">
            <h3>Add New User</h3>
            <form onSubmit={handleAddUser}>
              <div className="form-group">
                <label htmlFor="userName">Name:</label>
                <input 
                  type="text" 
                  id="userName"
                  value={newUserName}
                  onChange={(e) => setNewUserName(e.target.value)}
                  required
                />
              </div>
              
              <div className="form-group">
                <label htmlFor="userEmail">Email:</label>
                <input 
                  type="email" 
                  id="userEmail"
                  value={newUserEmail}
                  onChange={(e) => setNewUserEmail(e.target.value)}
                  required
                />
              </div>
              
              <div className="form-actions">
                <button 
                  type="submit" 
                  className="btn btn-success"
                  disabled={isLoading}
                >
                  {isLoading ? 'Adding...' : 'Add User'}
                </button>
              </div>
            </form>
          </div>
        )}
        
        {isLoading && !showAddUserForm ? (
          <div className="loading">Loading...</div>
        ) : (
          <div className="admin-page-layout">
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
                  onUpdateBusyTimes={() => {}}
                  readOnly={true}
                />
              ) : (
                <div className="no-selection">
                  <p>Please select a user from the list to view their schedule.</p>
                </div>
              )}
            </div>
          </div>
        )}
      </div>
      
      <ConfirmationModal 
        isOpen={showDeleteModal}
        message={`Are you sure you want to delete this user? This action cannot be undone.`}
        onConfirm={handleDeleteUser}
        onCancel={() => setShowDeleteModal(false)}
      />
    </div>
  );
}

export default AdminPage;
