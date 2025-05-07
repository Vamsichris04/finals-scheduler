import React, { useState } from 'react';
import './Calendar.css';

function Calendar({ busyTimes, onUpdateBusyTimes, userName }) {
  const days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday'];
  
  // Generate hours for Monday-Thursday (7:30 AM to 8:00 PM)
  const weekdayHours = [];
  for (let i = 7; i <= 20; i++) {
    if (i === 7) {
      weekdayHours.push('7:30 am');
    }
    if (i > 7) {
      weekdayHours.push(`${i}:00 ${i < 12 ? 'am' : 'pm'}`);
    }
  }
  
  // Generate hours for Friday (7:30 AM to 5:00 PM)
  const fridayHours = [];
  for (let i = 7; i <= 17; i++) {
    if (i === 7) {
      fridayHours.push('7:30 am');
    }
    if (i > 7) {
      fridayHours.push(`${i}:00 ${i < 12 ? 'am' : 'pm'}`);
    }
  }
  
  const [selectedCell, setSelectedCell] = useState(null);
  const [cellNote, setCellNote] = useState('');
  
  const handleCellClick = (day, hour) => {
    const cellKey = `${day}-${hour}`;
    setSelectedCell(cellKey);
    setCellNote(busyTimes[cellKey] || '');
  };
  
  const handleNoteChange = (e) => {
    setCellNote(e.target.value);
  };
  
  const handleNoteSubmit = () => {
    if (selectedCell) {
      const [day, hour] = selectedCell.split('-');
      const updatedBusyTimes = {
        ...busyTimes,
        [selectedCell]: cellNote
      };
      onUpdateBusyTimes(updatedBusyTimes);
      setSelectedCell(null);
    }
  };
  
  const handleCancelNote = () => {
    setSelectedCell(null);
    setCellNote('');
  };

  // Get hours for a specific day
  const getHoursForDay = (day) => {
    return day === 'Friday' ? fridayHours : weekdayHours;
  };

  return (
    <div className="calendar-container">
      <h2 className="calendar-title">Weekly Calendar Worksheet</h2>
      <div className="calendar-subtitle">Weekly Calendar of {userName || 'User'}</div>
      
      <div className="calendar-grid">
        <div className="calendar-header">
          <div className="time-column">Time/Day</div>
          {days.map(day => (
            <div key={day} className="day-column">{day}</div>
          ))}
        </div>
        
        <div className="calendar-body">
          {weekdayHours.map(hour => (
            <div key={hour} className="calendar-row">
              <div className="time-cell">{hour}</div>
              {days.map(day => {
                const cellKey = `${day}-${hour}`;
                const hasBusyTime = busyTimes[cellKey];
                const hoursForDay = getHoursForDay(day);
                
                // Skip rendering cells for hours that don't exist for that day
                if (!hoursForDay.includes(hour)) {
                  return <div key={cellKey} className="day-cell disabled"></div>;
                }
                
                return (
                  <div 
                    key={cellKey} 
                    className={`day-cell ${hasBusyTime ? 'busy' : ''}`}
                    onClick={() => handleCellClick(day, hour)}
                  >
                    {hasBusyTime && <span className="busy-indicator">*</span>}
                  </div>
                );
              })}
            </div>
          ))}
        </div>
      </div>
      
      {selectedCell && (
        <div className="note-modal">
          <div className="note-modal-content">
            <h3>Add Note for {selectedCell.replace('-', ' at ')}</h3>
            <textarea 
              value={cellNote}
              onChange={handleNoteChange}
              placeholder="Enter your busy time note here..."
              rows={4}
            ></textarea>
            <div className="note-actions">
              <button 
                className="btn btn-primary"
                onClick={handleNoteSubmit}
              >
                Save
              </button>
              <button 
                className="btn btn-danger"
                onClick={handleCancelNote}
              >
                Cancel
              </button>
            </div>
          </div>
        </div>
      )}
      
      <div className="calendar-actions">
        <button className="btn btn-primary" onClick={() => onUpdateBusyTimes(busyTimes)}>
          Save Schedule
        </button>
      </div>
    </div>
  );
}

export default Calendar;
