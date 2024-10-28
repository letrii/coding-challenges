import React, { useState, FC } from 'react';
import { useNavigate } from 'react-router-dom';
import '../styles/UserSetup.css';

export const UserSetup: FC = () => {
  const [userId, setUserId] = useState('');
  const [isAdmin, setIsAdmin] = useState(false);
  const navigate = useNavigate();

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    const params = new URLSearchParams({
      userId: userId || `user-${Date.now()}`,
      ...(isAdmin && { role: 'admin' }),
    });
    navigate(`/?${params.toString()}`);
  };

  return (
    <div className="user-setup">
      <form onSubmit={handleSubmit}>
        <div className="form-group">
          <label htmlFor="userId">User ID:</label>
          <input
            id="userId"
            type="text"
            value={userId}
            onChange={(e) => setUserId(e.target.value)}
            placeholder="Enter user ID or leave blank for random"
            autoComplete={'off'}
          />
        </div>

        <div className="form-group">
          <label>
            <input
              type="checkbox"
              checked={isAdmin}
              onChange={(e) => setIsAdmin(e.target.checked)}
            />
            Join as Admin
          </label>
        </div>

        <button type="submit">Join Quiz</button>
      </form>
    </div>
  );
};