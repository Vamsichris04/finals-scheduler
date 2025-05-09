import React from 'react';
import './UserList.css';

function UserList({ users }) {
  return (
    <div className="user-list-container">
      <h3 className="user-list-title">All Users</h3>
      <div className="user-list">
        {users.map(user => (
          <div key={user._id} className="user-item">
            <div className="user-info">
              <span className="user-name">{user.name}</span>
              <span className="user-email">{user.email}</span>
            </div>
            <div className="user-role">
              <span className={`role-badge ${user.role.toLowerCase()}`}>
                {user.role}
              </span>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

export default UserList; 