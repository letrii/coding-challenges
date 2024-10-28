import React, { FC } from 'react';
import { LeaderboardEntry } from '../types/quiz';

interface LeaderboardProps {
  entries: LeaderboardEntry[];
  currentUserId?: string;
}

export const Leaderboard: FC<LeaderboardProps> = ({ entries, currentUserId }) => {
  return (
    <div className="leaderboard">
      <h3>Leaderboard</h3>
      <div className="leaderboard-entries">
        {entries.map((entry, index) => (
          <div
            key={entry.user_id}
            className={`leaderboard-entry ${entry.user_id === currentUserId ? 'current-user' : ''}`}
          >
            <span className="position">{index + 1}</span>
            <span className="user-id">{entry.user_id}</span>
            <span className="score">{entry.score}</span>
          </div>
        ))}
      </div>
    </div>
  );
};