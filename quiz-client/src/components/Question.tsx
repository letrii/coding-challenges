import React, { FC } from 'react';
import { Question as QuestionType } from '../types/quiz';
import { Timer } from './Timer';

interface QuestionProps {
  question: QuestionType;
  selectedAnswer: string;
  onSelectAnswer: (answer: string) => void;
  onSubmit: () => void;
  timeLeft: number;
  disabled?: boolean;
}

export const Question: FC<QuestionProps> = ({
                                              question,
                                              selectedAnswer,
                                              onSelectAnswer,
                                              onSubmit,
                                              timeLeft,
                                              disabled,
                                            }) => {
  return (
    <div className="question-container">
      <Timer timeLeft={timeLeft} totalTime={question.time_limit} />

      <div className="question-text">
        <h3>{question.text}</h3>
      </div>

      <div className="options-container">
        {question.options.map((option) => (
          <button
            key={option}
            className={`option-button ${selectedAnswer === option ? 'selected' : ''}`}
            onClick={() => onSelectAnswer(option)}
            disabled={disabled || timeLeft === 0}
          >
            {option}
          </button>
        ))}
      </div>

      <button
        className="submit-button"
        onClick={onSubmit}
        disabled={disabled || !selectedAnswer || timeLeft === 0}
      >
        Submit Answer
      </button>
    </div>
  );
};