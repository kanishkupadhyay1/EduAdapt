import React, { useEffect, useState } from 'react';
import Header from '../components/Header';
import StudentProfile from '../components/StudentProfile';
import LearningControls from '../components/LearningControls';
import TeachingContent from '../components/TeachingContent';
import CurriculumContext from '../components/CurriculumContext';
import VerificationPanel from '../components/VerificationPanel';
import AssessmentPanel from '../components/AssessmentPanel';
import FeedbackPanel from '../components/FeedbackPanel';
import LearningState from '../components/LearningState';
import Roadmap from '../components/Roadmap';
import AccessibilityPanel from '../components/AccessibilityPanel';
import { fetchStudentProfile, generateLearningSession } from '../api/learningApi';

export default function Dashboard() {
  const [studentId, setStudentId] = useState('S001');
  const [selectedTopic, setSelectedTopic] = useState('Pointers');
  const [topK, setTopK] = useState(3);

  const [studentProfile, setStudentProfile] = useState(null);
  const [sessionResult, setSessionResult] = useState(null);
  const [isLoading, setIsLoading] = useState(false);
  const [errorMessage, setErrorMessage] = useState(null);

  // Load initial student state on mount
  useEffect(() => {
    let isMounted = true;
    fetchStudentProfile(studentId)
      .then((data) => {
        if (isMounted) {
          setStudentProfile(data);
        }
      })
      .catch((err) => {
        // Fallback default state for demo if backend is offline initially
        console.warn('Initial student profile fetch notice:', err.message);
      });
    return () => {
      isMounted = false;
    };
  }, [studentId]);

  const handleGenerate = async () => {
    setIsLoading(true);
    setErrorMessage(null);
    try {
      const data = await generateLearningSession(studentId, selectedTopic, topK);
      setSessionResult(data);
      if (data.student) {
        setStudentProfile(data.student);
      }
    } catch (err) {
      setErrorMessage(
        'Unable to generate learning session. Backend connection could not be established. Check that the EduAdapt backend is running.'
      );
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="app-container">
      <Header studentId={studentId} />

      <main className="dashboard-grid">
        {/* LEFT COLUMN: Student Profile & Controls */}
        <aside>
          <StudentProfile
            profile={studentProfile}
            currentTopic={selectedTopic}
          />

          <LearningControls
            selectedTopic={selectedTopic}
            onTopicChange={setSelectedTopic}
            topK={topK}
            onTopKChange={setTopK}
            onGenerate={handleGenerate}
            isLoading={isLoading}
          />
        </aside>

        {/* RIGHT COLUMN: Generated Learning Session */}
        <section aria-labelledby="session-title">
          {errorMessage && (
            <div className="error-banner" role="alert">
              <h4>Error</h4>
              <p>{errorMessage}</p>
              <button
                type="button"
                className="btn-retry"
                onClick={handleGenerate}
              >
                Retry
              </button>
            </div>
          )}

          {isLoading && (
            <div className="state-box" aria-live="polite">
              <div className="state-title">Generating personalized learning session...</div>
              <div className="state-text">
                Retrieving PPS curriculum context, tailoring content for Student {studentId}, and verifying safety.
              </div>
            </div>
          )}

          {!isLoading && !sessionResult && !errorMessage && (
            <div className="state-box">
              <h2 id="session-title" className="state-title">Learning Session</h2>
              <div className="state-text">
                No learning session generated yet. Select a topic and click "Generate Learning Session".
              </div>
            </div>
          )}

          {!isLoading && sessionResult && (
            <div id="session-title">
              {/* 1. Personalized Teaching */}
              <TeachingContent
                teaching={sessionResult.teaching}
                studentProfile={sessionResult.student || studentProfile}
                currentTopic={selectedTopic}
              />

              {/* 2. Curriculum / RAG Context */}
              <CurriculumContext
                curriculum={sessionResult.curriculum}
              />

              {/* 3. Verification & Safety */}
              <VerificationPanel
                verification={sessionResult.verification}
              />

              {/* 4. Assessment */}
              <AssessmentPanel
                assessment={sessionResult.assessment}
              />

              {/* 5. Personalized Feedback */}
              <FeedbackPanel
                feedback={sessionResult.feedback}
              />

              {/* 6. Updated Learning State */}
              <LearningState
                learningState={sessionResult.learning_state}
                initialStudent={sessionResult.student || studentProfile}
              />

              {/* 7. Personalized Roadmap */}
              <Roadmap
                roadmap={sessionResult.roadmap}
              />

              {/* 8. Accessibility */}
              <AccessibilityPanel
                accessibility={sessionResult.accessibility}
              />
            </div>
          )}
        </section>
      </main>
    </div>
  );
}
