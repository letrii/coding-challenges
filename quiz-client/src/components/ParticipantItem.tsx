import React, { FC } from 'react';

interface ParticipantItemProps {
  participantId: string;
  isCurrentUser?: boolean;
  isAdmin?: boolean;
}

export const ParticipantItem: FC<ParticipantItemProps> = ({
                                                            participantId,
                                                            isCurrentUser,
                                                            isAdmin,
                                                          }) => {
  return (
    <div
      className={`participant ${isCurrentUser ? 'current-user' : ''} ${isAdmin ? 'admin' : ''}`}
    >
      {isAdmin && <span className="admin-badge">👑</span>}
      {participantId}
      {isCurrentUser && <span className="current-user-badge">(You)</span>}
    </div>
  );
};
