import React, { FC } from 'react';

import { ParticipantItem } from './ParticipantItem';


interface ParticipantListProps {
  participants: Set<string>;
  currentUserId?: string;
  adminId?: string;
}

export const ParticipantList: FC<ParticipantListProps> = ({
                                                            participants,
                                                            currentUserId,
                                                            adminId,
                                                          }) => {
  return (
    <div className="participants-container">
      <h3>Participants ({participants.size})</h3>
      <div className="participant-list">
        {Array.from(participants).map((participantId) => (
          <ParticipantItem
            key={participantId}
            participantId={participantId}
            isCurrentUser={participantId === currentUserId}
            isAdmin={participantId === adminId}
          />
        ))}
      </div>
    </div>
  );
};