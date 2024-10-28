export interface QuizSession {
  id: string;
  quiz_id: string;
  status: 'waiting' | 'active' | 'completed';
  current_question: number;
  questions: Question[];
  participants: string[];
  start_time: string;
  end_time?: string;
}

export interface SessionStateMessage {
  type: 'session_state';
  session_id: string;
  status: 'waiting' | 'active' | 'completed';
  current_question: number;
  questions: Question[];
  participants: string[];
  quiz_id: string;
  start_time: string;
}

export interface Question {
  id: string;
  text: string;
  type: 'multiple_choice' | 'true_false';
  options: string[];
  correct_answer: string;
  points: number;
  time_limit: number;
}

export interface LeaderboardEntry {
  user_id: string;
  score: number;
}

export interface Answer {
  session_id: string;
  question_id: string;
  user_id: string;
  answer: string;
  timestamp?: string;
}

export interface WebSocketMessage {
  type: string;
  [key: string]: any;
}

export interface QuizApiError {
  status: string;
  message: string;
  status_code: number;
}