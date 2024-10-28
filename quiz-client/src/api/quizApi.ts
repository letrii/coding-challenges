import axios from 'axios';
import { QuizSession, Answer, QuizApiError } from '../types/quiz';

const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000/api/v1';

const axiosInstance = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

export const quizApi = {
  async getSession(sessionId: string): Promise<QuizSession> {
    try {
      const response = await axiosInstance.get<QuizSession>(
        `/quizzes/sessions/${sessionId}`
      );
      return response.data;
    } catch (error) {
      if (axios.isAxiosError(error) && error.response?.data) {
        throw error.response.data as QuizApiError;
      }
      throw error;
    }
  },

  async submitAnswer(answer: Answer): Promise<void> {
    try {
      await axiosInstance.post(
        `/quizzes/sessions/${answer.session_id}/submit`,
        answer
      );
    } catch (error) {
      if (axios.isAxiosError(error) && error.response?.data) {
        throw error.response.data as QuizApiError;
      }
      throw error;
    }
  },

  async startSession(sessionId: string): Promise<void> {
    try {
      await axiosInstance.post(`/quizzes/sessions/${sessionId}/start`);
    } catch (error) {
      if (axios.isAxiosError(error) && error.response?.data) {
        throw error.response.data as QuizApiError;
      }
      throw error;
    }
  },
};