import React, { FC } from 'react';

interface TimerProps {
  timeLeft: number;
  totalTime: number;
}

export const Timer: FC<TimerProps> = ({ timeLeft, totalTime }) => {
  const percentage = (timeLeft / totalTime) * 100;

  return (
    <div className="timer-container">
      <div className="timer-info">
        Time remaining: {timeLeft} seconds
      </div>
      <div className="timer-bar-container">
        <div
          className="timer-bar"
          style={{
            width: `${percentage}%`,
            backgroundColor: percentage < 30 ? '#ff4444' : '#44ff44'
          }}
        />
      </div>
    </div>
  );
};