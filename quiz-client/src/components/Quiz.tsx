import React, { FC, useState, useCallback } from 'react';
import { useQuizWebSocket } from '../hooks/useQuizWebSocket';
import { Question } from './Question';
import { Leaderboard } from './Leaderboard';
import { ParticipantList } from './ParticipantList';
import { quizApi } from '../api/quizApi';
import {
  QuizSession,
  Question as QuestionType,
  LeaderboardEntry,
  WebSocketMessage,
  QuizApiError,
  SessionStateMessage,
} from '../types/quiz';
import '../styles/Quiz.css';

interface QuizProps {
  sessionId: string;
  userId: string;
  isAdmin?: boolean;
  onComplete?: () => void;
}

export const Quiz: FC<QuizProps> = ({ sessionId, userId, isAdmin, onComplete }) => {
  const [session, setSession] = useState<QuizSession | null>(null);
  const [currentQuestion, setCurrentQuestion] = useState<QuestionType | null>(null);
  const [selectedAnswer, setSelectedAnswer] = useState<string>('');
  const [leaderboard, setLeaderboard] = useState<LeaderboardEntry[]>([]);
  const [timeLeft, setTimeLeft] = useState<number>(0);
  const [error, setError] = useState<string | null>(null);
  const [participants, setParticipants] = useState<Set<string>>(new Set());
  const [isSubmitting, setIsSubmitting] = useState(false);

  const handleMessage = useCallback((message: WebSocketMessage) => {
    console.log('Received message:', message);
    switch (message.type) {
      case 'session_state': {
        const sessionMsg = message as SessionStateMessage;

        setSession(prev => {
          if (!prev) {
            return {
              id: sessionMsg.session_id,
              quiz_id: sessionMsg.quiz_id,
              status: sessionMsg.status,
              current_question: sessionMsg.current_question,
              questions: sessionMsg.questions || [],
              participants: sessionMsg.participants || [],
              start_time: sessionMsg.start_time,
            };
          }
          return {
            ...prev,
            status: sessionMsg.status,
            current_question: sessionMsg.current_question,
            questions: sessionMsg.questions || prev.questions,
          };
        });

        if (sessionMsg.status === 'active' && sessionMsg.questions?.length > 0) {
          const currentQuestionIndex = sessionMsg.current_question || 0;
          const currentQ = sessionMsg.questions[currentQuestionIndex];
          if (currentQ) {
            console.log('Setting current question:', currentQ);
            setCurrentQuestion(currentQ);
            setTimeLeft(currentQ.time_limit);
          }
        }

        if (sessionMsg.participants) {
          console.log('Updating participants:', sessionMsg.participants);
          setParticipants(new Set(sessionMsg.participants));
        }
        break;
      }

      case 'session_started': {
        console.log('Session started:', message);

        setSession(prev => {
          if (!prev) return prev;
          return {
            ...prev,
            status: 'active',
            current_question: 0,
          };
        });

        if (message.current_question) {
          console.log('Setting initial question:', message.current_question);
          setCurrentQuestion(message.current_question);
          setTimeLeft(message.current_question.time_limit);
          setSelectedAnswer('');
        }

        if (message.participants) {
          setParticipants(new Set(message.participants));
        }
        break;
      }

      case 'next_question': {
        if (message.question) {
          setCurrentQuestion(message.question);
          setTimeLeft(message.question.time_limit);
          setSelectedAnswer('');
        }
        break;
      }

      case 'answer_submitted': {
        if (message.leaderboard) {
          setLeaderboard(message.leaderboard);
        }
        if (message.user_id === userId) {
          console.log(message.is_correct ? 'Correct!' : 'Incorrect');
        }
        break;
      }

      case 'quiz_completed': {
        setSession(prev => {
          if (!prev) return prev;
          return {
            ...prev,
            status: 'completed'
          };
        });
        if (message.final_leaderboard) {
          setLeaderboard(message.final_leaderboard);
        }
        onComplete?.();
        break;
      }

      case 'participant_joined': {
        console.log('Participant joined:', message.user_id);
        if (message.participants) {
          setParticipants(new Set(message.participants));
        } else {
          setParticipants(prev => new Set([...Array.from(prev), message.user_id]));
        }
        break;
      }

      case 'participant_left': {
        console.log('Participant left:', message.user_id);
        if (message.participants) {
          setParticipants(new Set(message.participants));
        } else {
          setParticipants(prev => {
            const updated = new Set(prev);
            updated.delete(message.user_id);
            return updated;
          });
        }
        break;
      }

      case 'connection_closed': {
        setError(`${message.reason}. This session is no longer active.`);
        break;
      }

      case 'error': {
        if (message.error) {
          setError(message.error);
        }
        break;
      }
    }
  }, [userId, onComplete]);

  const { isConnected, reconnect } = useQuizWebSocket({
    sessionId,
    userId,
    onMessage: handleMessage,
    onConnect: async () => {
      try {
        setError(null);
        const sessionData = await quizApi.getSession(sessionId);
        console.log('Loaded session:', sessionData);

        setSession(sessionData);
        setParticipants(new Set(sessionData.participants));

        if (sessionData.status === 'active' && sessionData.questions?.length > 0) {
          const currentQuestionIndex = sessionData.current_question || 0;
          const currentQ = sessionData.questions[currentQuestionIndex];
          if (currentQ) {
            console.log('Setting initial question:', currentQ);
            setCurrentQuestion(currentQ);
            setTimeLeft(currentQ.time_limit);
          }
        }
      } catch (error) {
        const apiError = error as QuizApiError;
        setError(apiError.message || 'Failed to load session');
      }
    },
    onDisconnect: () => {
      if (!error) {
        setError('Connection lost. Click to reconnect.');
      }
    },
  });

  const handleSubmitAnswer = async () => {
    if (!currentQuestion || !selectedAnswer || isSubmitting) return;

    setIsSubmitting(true);
    try {
      await quizApi.submitAnswer({
        session_id: sessionId,
        question_id: currentQuestion.id,
        user_id: userId,
        answer: selectedAnswer,
      });
      setError(null);
    } catch (error) {
      const apiError = error as QuizApiError;
      setError(apiError.message || 'Failed to submit answer');
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleStartQuiz = async () => {
    try {
      await quizApi.startSession(sessionId);
    } catch (error) {
      const apiError = error as QuizApiError;
      setError(apiError.message || 'Failed to start quiz');
    }
  };

  if (!session) {
    return (
      <div className="loading-container">
        <div className="loading-spinner" />
        <div>{isConnected ? 'Loading quiz session...' : 'Connecting to quiz session...'}</div>
        {error && (
          <div className="error-message">
            <span>{error}</span>
            <button
              className="retry-button"
              onClick={() => {
                setError(null);
                reconnect();
              }}
            >
              Reconnect
            </button>
          </div>
        )}
      </div>
    );
  }

  return (
    <div className="quiz-container">
      {error && (
        <div className="error-message">
          <span>{error}</span>
          <button className="error-dismiss" onClick={() => setError(null)}>
            Dismiss
          </button>
        </div>
      )}

      <div className="quiz-header">
        <div className="quiz-status">
          Status: <span className={`status-${session.status}`}>{session.status}</span>
        </div>
        {!isConnected && (
          <button className="reconnect-button" onClick={reconnect}>
            Reconnect
          </button>
        )}
      </div>

      {session.status === 'waiting' && (
        <div className="waiting-container">
          <div className="waiting-message">
            {isAdmin
              ? 'Waiting for participants...'
              : 'Waiting for quiz to start...'}
          </div>

          {isAdmin && (
            <button
              className="start-quiz-button"
              onClick={handleStartQuiz}
              disabled={participants.size < 1}
            >
              Start Quiz ({participants.size} participants)
            </button>
          )}

          <ParticipantList
            participants={participants}
            currentUserId={userId}
            adminId={isAdmin ? userId : undefined}
          />
        </div>
      )}

      {session.status === 'active' && (
        <div className="active-quiz-container">
          <div className="quiz-progress">
            Question {session.current_question + 1} of {session.questions.length}
          </div>

          {currentQuestion ? (
            <Question
              question={currentQuestion}
              selectedAnswer={selectedAnswer}
              onSelectAnswer={setSelectedAnswer}
              onSubmit={handleSubmitAnswer}
              timeLeft={timeLeft}
              disabled={isSubmitting}
            />
          ) : (
            <div className="error-message">
              No question available. Please try refreshing the page.
            </div>
          )}
        </div>
      )}

      {session.status === 'completed' && (
        <div className="completion-message">
          <h2>Quiz completed!</h2>
          <p>Thank you for participating</p>
        </div>
      )}

      <Leaderboard
        entries={leaderboard}
        currentUserId={userId}
      />
    </div>
  );

};