import React, { useState, useEffect } from 'react';
import Header from '../components/Header';
import UserDropdown from '../components/UserDropdown';
import Calendar from '../components/Calendar';
import ConfirmationModal from '../components/ConfirmationModal';
import { fetchUsers, fetchUserBusyTimes, deleteUser, addUser, updateUser } from '../services/api';
import './AdminPage.css';

function AdminPage({ onLogout }) {
  const [users, setUsers] = useState([]);
  const [selectedUser, setSelectedUser] = useState(null);
  const [busyTimes, setBusyTimes] = useState({});
  const [isLoading, setIsLoading] = useState(true);
  const [message, setMessage] = useState('');
  const [showAddUserForm, setShowAddUserForm] = useState(false);
  const [newUserData, setNewUserData] = useState({
    name: '',
    userId: '',
    email: '',
    role: 'user',
    position: 'Tier 1',
    isCommuter: false,
    isActive: true,
    desiredHours: 12,
  });
  const [showDeleteModal, setShowDeleteModal] = useState(false);
  const [showUpdateForm, setShowUpdateForm] = useState(false);
  const [updateFormData, setUpdateFormData] = useState({
    name: '',
    email: '',
    role: '',
    position: '',
    isCommuter: false,
    isActive: true
  });

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
      const times = await fetchUserBusyTimes(selectedUser._id);
      setBusyTimes(times);
    } catch (error) {
      console.error('Error loading busy times:', error);
      setMessage('Failed to load schedule. Please try again later.');
    } finally {
      setIsLoading(false);
    }
  };

  const handleSelectUser = (userId) => {
    const user = users.find(u => u._id === userId);
    if (!user) {
      setSelectedUser(null);
      return;
    }
    setSelectedUser(user);
    setUpdateFormData({
      name: user.name || '',
      email: user.email || '',
      role: user.role || '',
      position: user.position || '',
      isCommuter: user.isCommuter || false,
      isActive: user.isActive !== undefined ? user.isActive : true
    });
  };

  const handleAddUser = async (e) => {
    e.preventDefault();
    setIsLoading(true);
    try {
      await addUser(newUserData);
      setMessage('User added successfully!');
      setNewUserData({
        name: '',
        userId: '',
        email: '',
        role: 'user',
        position: 'Tier 1',
        isCommuter: false,
        isActive: true,
        desiredHours: 12,
      });
      setShowAddUserForm(false);
      await loadUsers();
    } catch (error) {
      setMessage('Failed to add user. Please try again.');
    } finally {
      setIsLoading(false);
    }
  };

  const handleDeleteUser = async () => {
    if (!selectedUser) return;
    
    if (window.confirm('Are you sure you want to delete this user?')) {
      try {
        await deleteUser(selectedUser._id);
        setMessage('User deleted successfully');
        setSelectedUser(null);
        setBusyTimes({});
        setShowDeleteModal(false);
        await loadUsers();
      } catch (error) {
        setMessage('Failed to delete user');
      }
    }
  };

  const handleUpdateClick = () => {
    setShowUpdateForm(true);
  };

  const handleUpdateSubmit = async (e) => {
    e.preventDefault();
    try {
      await updateUser(selectedUser._id, updateFormData);
      setMessage('User updated successfully');
      setShowUpdateForm(false);
      loadUsers();
    } catch (error) {
      setMessage('Failed to update user');
    }
  };

  const handleUpdateCancel = () => {
    setShowUpdateForm(false);
    if (!selectedUser) return;
    setUpdateFormData({
      name: selectedUser.name,
      email: selectedUser.email,
      role: selectedUser.role,
      position: selectedUser.position,
      isCommuter: selectedUser.isCommuter,
      isActive: selectedUser.isActive
    });
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
          
          <button
            className="btn btn-primary"
            onClick={handleUpdateClick}
            disabled={!selectedUser}
          >
            Update User
          </button>
        </div>
        
        {showAddUserForm && (
          <div className="add-user-form">
            <h3>Add New User</h3>
            <form onSubmit={handleAddUser}>
              <div className="form-group">
                <label>Name:</label>
                <input type="text" value={newUserData.name} onChange={e => setNewUserData({...newUserData, name: e.target.value})} required />
              </div>
              <div className="form-group">
                <label>User ID:</label>
                <input type="number" value={newUserData.userId} onChange={e => setNewUserData({...newUserData, userId: e.target.value})} required />
              </div>
              <div className="form-group">
                <label>Email:</label>
                <input type="email" value={newUserData.email} onChange={e => setNewUserData({...newUserData, email: e.target.value})} required />
              </div>
              <div className="form-group">
                <label>Role:</label>
                <select value={newUserData.role} onChange={e => setNewUserData({...newUserData, role: e.target.value})}>
                  <option value="user">User</option>
                  <option value="admin">Admin</option>
                </select>
              </div>
              <div className="form-group">
                <label>Position:</label>
                <select value={newUserData.position} onChange={e => setNewUserData({...newUserData, position: e.target.value})}>
                  <option value="Tier 1">Tier 1</option>
                  <option value="Tier 2">Tier 2</option>
                  <option value="Tier 3">Tier 3</option>
                  <option value="Tier 4">Tier 4</option>
                </select>
              </div>
              <div className="form-group">
                <label>
                  <input type="checkbox" checked={newUserData.isCommuter} onChange={e => setNewUserData({...newUserData, isCommuter: e.target.checked})} />
                  Is Commuter
                </label>
              </div>
              <div className="form-group">
                <label>
                  <input type="checkbox" checked={newUserData.isActive} onChange={e => setNewUserData({...newUserData, isActive: e.target.checked})} />
                  Is Active
                </label>
              </div>
              <div className="form-group">
                <label>Desired Hours:</label>
                <input type="number" min="10" max="20" value={newUserData.desiredHours} onChange={e => setNewUserData({...newUserData, desiredHours: e.target.value})} required />
              </div>
              <div className="form-actions">
                <button type="submit" className="btn btn-success" disabled={isLoading}>
                  {isLoading ? 'Adding...' : 'Add User'}
                </button>
              </div>
            </form>
          </div>
        )}
        
        {showUpdateForm ? (
          <div className="update-user-form">
            <h3>Update User</h3>
            <form onSubmit={handleUpdateSubmit}>
              <div className="form-group">
                <label htmlFor="updateUserName">Name:</label>
                <input
                  type="text"
                  id="updateUserName"
                  value={updateFormData.name}
                  onChange={(e) => setUpdateFormData({...updateFormData, name: e.target.value})}
                  required
                />
              </div>
              <div className="form-group">
                <label htmlFor="updateUserRole">Role:</label>
                <select
                  value={updateFormData.role}
                  onChange={(e) => setUpdateFormData({...updateFormData, role: e.target.value})}
                  required
                >
                  <option value="user">User</option>
                  <option value="admin">Admin</option>
                </select>
              </div>
              <div className="form-group">
                <label htmlFor="updateUserPosition">Position:</label>
                <select
                  value={updateFormData.position}
                  onChange={(e) => setUpdateFormData({...updateFormData, position: e.target.value})}
                  required
                >
                  <option value="Tier 1">Tier 1</option>
                  <option value="Tier 2">Tier 2</option>
                  <option value="Tier 3">Tier 3</option>
                  <option value="Tier 4">Tier 4</option>
                </select>
              </div>
              <div className="form-group">
                <label htmlFor="updateUserIsCommuter">Is Commuter:</label>
                <input
                  type="checkbox"
                  id="updateUserIsCommuter"
                  checked={updateFormData.isCommuter}
                  onChange={(e) => setUpdateFormData({...updateFormData, isCommuter: e.target.checked})}
                />
              </div>
              <div className="form-group">
                <label htmlFor="updateUserIsActive">Is Active:</label>
                <input
                  type="checkbox"
                  id="updateUserIsActive"
                  checked={updateFormData.isActive}
                  onChange={(e) => setUpdateFormData({...updateFormData, isActive: e.target.checked})}
                />
              </div>
              <div className="form-actions">
                <button
                  type="submit"
                  className="btn btn-success"
                  disabled={isLoading}
                >
                  {isLoading ? 'Updating...' : 'Update User'}
                </button>
                <button
                  type="button"
                  className="btn btn-secondary"
                  onClick={handleUpdateCancel}
                  style={{ marginLeft: 10 }}
                >
                  Cancel
                </button>
              </div>
            </form>
          </div>
        ) : (
          <div className="admin-page-layout">
            <div className="sidebar">
              <UserDropdown 
                users={users}
                selectedUser={selectedUser?._id}
                onSelectUser={handleSelectUser}
              />
            </div>
            
            <div className="main-content">
              {selectedUser ? (
                <>
                  <h2>
                    Weekly Calendar Worksheet
                    <span style={{ fontWeight: 'normal', fontSize: '1rem', marginLeft: 12 }}>
                    </span>
                  </h2>
                  <p style={{ color: '#666', marginBottom: 16 }}>
                  </p>
                  <Calendar 
                    busyTimes={busyTimes}
                    onUpdateBusyTimes={() => {}}
                    readOnly={true}
                    userName={selectedUser ? selectedUser.name : ''}
                  />
                </>
              ) : (
                <div className="no-selection">
                  <p>Please select a student worker from the list to view their schedule.</p>
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
