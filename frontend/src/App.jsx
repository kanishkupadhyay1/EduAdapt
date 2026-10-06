import React, { useEffect, useState } from 'react';
import Sidebar from './components/layout/Sidebar';
import Home from './pages/Home';
import Learn from './pages/Learn';
import Tutor from './pages/Tutor';
import Practice from './pages/Practice';
import Tests from './pages/Tests';
import Results from './pages/Results';
import Progress from './pages/Progress';
import { fetchStudentProfile, generateLearningSession } from './api/learningApi';

export default function App() {
  const [activePage, setActivePage] = useState('home');
  const [studentId, setStudentId] = useState('S001');
  const [currentTopic, setCurrentTopic] = useState('Pointers');

  const [studentProfile, setStudentProfile] = useState(null);
  const [sessionResult, setSessionResult] = useState(null);
  const [learningState, setLearningState] = useState(null);
  const [testResult, setTestResult] = useState(null);
  const [tutorContextCode, setTutorContextCode] = useState('');

  const [isLoadingLesson, setIsLoadingLesson] = useState(false);
  const [globalError, setGlobalError] = useState(null);

  // 1. Load initial student profile
  useEffect(() => {
    fetchStudentProfile(studentId)
      .then((data) => {
        setStudentProfile(data);
      })
      .catch((err) => {
        console.warn('Initial student profile warning:', err);
      });
  }, [studentId]);

  // 2. Fetch initial lesson session for Pointers
  const handleGenerateLesson = async (topicToUse = currentTopic) => {
    setIsLoadingLesson(true);
    setGlobalError(null);
    try {
      const data = await generateLearningSession(studentId, topicToUse, 3);
      setSessionResult(data);
      if (data.student) setStudentProfile(data.student);
      if (data.learning_state) setLearningState(data.learning_state);
    } catch (err) {
      const msg = err.message && err.message.includes('Mistral')
        ? err.message
        : 'EduAdapt could not connect to Mistral 7B. Please start Ollama and try again.';
      setGlobalError(msg);
    } finally {
      setIsLoadingLesson(false);
    }
  };

  // Auto-generate lesson on first navigation to learn if not already generated
  const handleNavigate = (pageId) => {
    setActivePage(pageId);
    if (pageId === 'learn' && !sessionResult && !isLoadingLesson) {
      handleGenerateLesson(currentTopic);
    }
  };

  const handleOpenTutorWithCode = (code) => {
    setTutorContextCode(code);
    setActivePage('tutor');
  };

  const handleAssessmentCompleted = (res) => {
    if (res.updated_learning_state) setLearningState(res.updated_learning_state);
    if (res.updated_student) setStudentProfile(res.updated_student);
  };

  const handleTestCompleted = (res) => {
    setTestResult(res);
    if (res.updated_learning_state) setLearningState(res.updated_learning_state);
    if (res.updated_student) setStudentProfile(res.updated_student);
    setActivePage('results');
  };

  return (
    <div className="platform-layout">
      {/* Sidebar Navigation */}
      <Sidebar
        activePage={activePage}
        onNavigate={handleNavigate}
        studentId={studentId}
      />

      {/* Main Content Area */}
      <main className="main-content">
        {globalError && (
          <div className="error-box">
            <h4>Backend Connection Notice</h4>
            <p>{globalError}</p>
          </div>
        )}

        {activePage === 'home' && (
          <Home
            student={studentProfile}
            currentTopic={currentTopic}
            onNavigate={handleNavigate}
            recentActivity={testResult}
          />
        )}

        {activePage === 'learn' && (
          <Learn
            currentTopic={currentTopic}
            onTopicChange={(t) => {
              setCurrentTopic(t);
              handleGenerateLesson(t);
            }}
            sessionResult={sessionResult}
            onGenerateLesson={() => handleGenerateLesson(currentTopic)}
            isLoading={isLoadingLesson}
            onNavigate={handleNavigate}
            onOpenTutorWithCode={handleOpenTutorWithCode}
          />
        )}

        {activePage === 'tutor' && (
          <Tutor
            studentId={studentId}
            currentTopic={currentTopic}
            initialContextCode={tutorContextCode}
          />
        )}

        {activePage === 'practice' && (
          <Practice
            studentId={studentId}
            currentTopic={currentTopic}
            onNavigate={handleNavigate}
            onAssessmentCompleted={handleAssessmentCompleted}
          />
        )}

        {activePage === 'tests' && (
          <Tests
            studentId={studentId}
            currentTopic={currentTopic}
            onTestCompleted={handleTestCompleted}
          />
        )}

        {activePage === 'results' && (
          <Results
            testResult={testResult}
            currentTopic={currentTopic}
            onNavigate={handleNavigate}
          />
        )}

        {activePage === 'progress' && (
          <Progress
            student={studentProfile}
            learningState={learningState}
            currentTopic={currentTopic}
            roadmapData={sessionResult?.roadmap}
            onNavigate={handleNavigate}
          />
        )}
      </main>
    </div>
  );
}
