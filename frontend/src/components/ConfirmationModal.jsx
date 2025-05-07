import React from 'react';
import './ConfirmationModal.css';

function ConfirmationModal({ isOpen, message, onConfirm, onCancel }) {
  if (!isOpen) return null;
  
  return (
    <div className="modal-overlay">
      <div className="modal-content">
        <h3>Confirmation</h3>
        <p>{message}</p>
        <div className="modal-actions">
          <button 
            className="btn btn-danger"
            onClick={onCancel}
          >
            Cancel
          </button>
          <button 
            className="btn btn-primary"
            onClick={onConfirm}
          >
            Confirm
          </button>
        </div>
      </div>
    </div>
  );
}

export default ConfirmationModal;
