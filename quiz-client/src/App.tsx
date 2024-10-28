import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { Quiz } from './components/Quiz';
import { UserSetup } from './components/UserSetup';
import { useQueryParams } from './hooks/useQueryParams';

const QuizPage = () => {
  const { userId, isAdmin } = useQueryParams();

  if (!userId) {
    return <Navigate to={`/join`} />;
  }

  return (
    <div className="app-container">
      <Quiz
        sessionId="session_671f3a6a146fd2c7407956f2_1730101288" // Change here ^^
        userId={userId}
        isAdmin={isAdmin}
        onComplete={() => {
          console.log('Quiz completed!');
        }}
      />
    </div>
  );
};

const App = () => {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<QuizPage />} />
        <Route path="/join" element={<UserSetup />} />
      </Routes>
    </BrowserRouter>
  );
};

export default App;