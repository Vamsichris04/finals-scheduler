import React from 'react';
import './UserDropdown.css';

function UserDropdown({ users, selectedUser, onSelectUser }) {
  return (
    <div className="user-dropdown-container">
      <div className="dropdown-header">
        <span> Select student workeres name:</span>
      </div>
      <div className="dropdown-select">
        <select 
          value={selectedUser || ''} 
          onChange={(e) => onSelectUser(e.target.value)}
          className="user-select"
        >
          <option value="" disabled>Select a user</option>
          {users.map(user => (
            <option key={user.id} value={user.id}>
              {user.name}
            </option>
          ))}
        </select>
      </div>
      
      {users.map(user => (
        <div 
          key={user.id} 
          className={`user-item ${selectedUser === user.id ? 'selected' : ''}`}
          onClick={() => onSelectUser(user.id)}
        >
          <div className="user-avatar">
            <span>{user.name.charAt(0)}</span>
          </div>
          <div className="user-name">{user.name}</div>
        </div>
      ))}
    </div>
  
  );
}

export default UserDropdown;
