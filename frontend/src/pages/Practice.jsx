import React, { useEffect, useState } from 'react';
import {
  fetchPracticeMcqs,
  submitPracticeSession,
  generatePracticeProblems,
  executePracticeCode,
} from '../api/learningApi';

const PPS_UNITS = [
  {
    unit: 'Unit 1: Fundamentals of C',
    topics: ['Variables and Data Types', 'Operators and Expressions'],
  },
  {
    unit: 'Unit 2: Control Structures',
    topics: ['Conditionals', 'Loops'],
  },
  {
    unit: 'Unit 3: Arrays & Strings',
    topics: ['Arrays', 'Strings'],
  },
  {
    unit: 'Unit 4: Functions & Pointers',
    topics: ['Functions', 'Pointers'],
  },
  {
    unit: 'Unit 5: Structures & Dynamic Memory',
    topics: ['Structures', 'Dynamic Memory Allocation'],
  },
];

export default function Practice({
  studentId = 'S001',
  currentTopic = 'Pointers',
  onTopicChange,
  onNavigate,
  onAssessmentCompleted,
  onAskTutorWithContext,
}) {
  const [activeTab, setActiveTab] = useState('mcq'); // 'mcq' | 'ai_challenge'

  // ==========================================
  // Mode 1: 5-Question Curriculum MCQs (|P| = 5)
  // ==========================================
  const [practiceQuestions, setPracticeQuestions] = useState([]);
  const [currentQIdx, setCurrentQIdx] = useState(0);
  const [practiceAnswers, setPracticeAnswers] = useState({});
  const [practiceSubmitted, setPracticeSubmitted] = useState(false);
  const [practiceResult, setPracticeResult] = useState(null);
  const [startTime, setStartTime] = useState(Date.now());
  const [isLoadingMcq, setIsLoadingMcq] = useState(true);
  const [isSubmittingMcq, setIsSubmittingMcq] = useState(false);

  // ==========================================
  // Mode 2: AI Coding Challenge with Hint Ladder
  // ==========================================
  const [aiProblems, setAiProblems] = useState(null);
  const [isLoadingAi, setIsLoadingAi] = useState(false);
  const [revealedHints, setRevealedHints] = useState({});
  const [studentCode, setStudentCode] = useState('');
  const [isRunningCode, setIsRunningCode] = useState(false);
  const [isSubmittingCode, setIsSubmittingCode] = useState(false);
  const [execResult, setExecResult] = useState(null);
  const [errorMessage, setErrorMessage] = useState(null);

  // Load 5-Question Curriculum Practice Session
  useEffect(() => {
    let isMounted = true;
    setIsLoadingMcq(true);
    setErrorMessage(null);
    setPracticeAnswers({});
    setPracticeSubmitted(false);
    setPracticeResult(null);
    setCurrentQIdx(0);
    setStartTime(Date.now());

    fetchPracticeMcqs(studentId, currentTopic)
      .then((data) => {
        if (isMounted) {
          const qs = data?.questions || [];
          setPracticeQuestions(qs);
        }
      })
      .catch((err) => {
        if (isMounted) setErrorMessage(err.message || 'Unable to fetch practice questions.');
      })
      .finally(() => {
        if (isMounted) setIsLoadingMcq(false);
      });

    return () => {
      isMounted = false;
    };
  }, [studentId, currentTopic]);

  // Handle adaptive change when studentId or currentTopic changes
  useEffect(() => {
    if (activeTab === 'ai_challenge') {
      handleGenerateAiPractice(studentId, currentTopic);
    } else {
      setAiProblems(null);
      setExecResult(null);
    }
  }, [studentId, currentTopic]);

  const handleGenerateAiPractice = async (sid = studentId, top = currentTopic) => {
    setIsLoadingAi(true);
    setRevealedHints({});
    setErrorMessage(null);
    setExecResult(null);
    try {
      const data = await generatePracticeProblems(sid, top);
      setAiProblems(data);
      const chal = data?.challenge || (Array.isArray(data?.practice_problems) ? data.practice_problems[0] : null);
      if (chal && chal.starter_code) {
        setStudentCode(chal.starter_code);
      } else {
        setStudentCode(
          `#include <stdio.h>\n\n// Complete solution for ${top}\nint main() {\n    printf("Hello EduAdapt\\n");\n    return 0;\n}`
        );
      }
    } catch (err) {
      setErrorMessage('Unable to generate AI challenge: ' + (err.message || 'Check backend status'));
    } finally {
      setIsLoadingAi(false);
    }
  };

  const handleSelectAnswer = (optionStr) => {
    if (practiceSubmitted) return;
    const letter = optionStr.trim().charAt(0).toUpperCase();
    setPracticeAnswers((prev) => ({
      ...prev,
      [currentQIdx]: letter,
    }));
  };

  const handleSubmitPractice = async () => {
    if (isSubmittingMcq || practiceQuestions.length === 0) return;
    setIsSubmittingMcq(true);
    setErrorMessage(null);
    const duration = Math.round((Date.now() - startTime) / 1000) || 25;

    try {
      const res = await submitPracticeSession(studentId, currentTopic, practiceAnswers, duration);
      setPracticeResult(res);
      setPracticeSubmitted(true);
      if (onAssessmentCompleted) {
        onAssessmentCompleted({
          ...res,
          type: 'practice_mcq',
        });
      }
    } catch (err) {
      setErrorMessage('Unable to submit practice session: ' + (err.message || 'Check network connection'));
    } finally {
      setIsSubmittingMcq(false);
    }
  };

  const handleResetPractice = () => {
    setPracticeAnswers({});
    setPracticeSubmitted(false);
    setPracticeResult(null);
    setCurrentQIdx(0);
    setStartTime(Date.now());
  };

  const handleRunCode = async () => {
    if (!studentCode.trim() || isRunningCode) return;
    setIsRunningCode(true);
    setErrorMessage(null);
    const chal = aiProblems?.challenge || (Array.isArray(aiProblems?.practice_problems) ? aiProblems.practice_problems[0] : null);
    try {
      const res = await executePracticeCode(
        studentId,
        currentTopic,
        studentCode,
        chal?.expected_output || null,
        false,
        chal?.sample_input || null
      );
      setExecResult(res);
    } catch (err) {
      setErrorMessage('Code execution error: ' + (err.message || 'Compiler execution failed'));
    } finally {
      setIsRunningCode(false);
    }
  };

  const handleSubmitCode = async () => {
    if (!studentCode.trim() || isSubmittingCode) return;
    setIsSubmittingCode(true);
    setErrorMessage(null);
    const chal = aiProblems?.challenge || (Array.isArray(aiProblems?.practice_problems) ? aiProblems.practice_problems[0] : null);
    try {
      const res = await executePracticeCode(
        studentId,
        currentTopic,
        studentCode,
        chal?.expected_output || chal?.sample_output || null,
        true,
        chal?.sample_input || null
      );
      setExecResult(res);
      if (res.passed && onAssessmentCompleted) {
        onAssessmentCompleted({
          is_correct: true,
          score: 100,
          topic: currentTopic,
          student_id: studentId,
          type: 'coding_challenge',
        });
      }
    } catch (err) {
      setErrorMessage('Submission evaluation error: ' + (err.message || 'Evaluation failed'));
    } finally {
      setIsSubmittingCode(false);
    }
  };

  const handleResetCode = () => {
    const chal = aiProblems?.challenge || (Array.isArray(aiProblems?.practice_problems) ? aiProblems.practice_problems[0] : null);
    if (chal && chal.starter_code) {
      setStudentCode(chal.starter_code);
    }
    setExecResult(null);
  };

  const currentQ = practiceQuestions[currentQIdx];
  const totalQuestions = practiceQuestions.length || 5;
  const answeredCount = Object.keys(practiceAnswers).length;
  const currentChallenge = aiProblems?.challenge || (Array.isArray(aiProblems?.practice_problems) ? aiProblems.practice_problems[0] : null);

  return (
    <div className="practice-page">
      <header className="page-header">
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', flexWrap: 'wrap', gap: '12px' }}>
          <div>
            <h2 className="page-title">Practice: {currentTopic}</h2>
            <p className="page-subtitle">
              Solve adaptive conceptual checks and C coding challenges for Student <strong>{studentId}</strong>.
            </p>
          </div>
          <div style={{ display: 'flex', gap: '8px', alignItems: 'center', flexWrap: 'wrap' }}>
            {onTopicChange && (
              <select
                className="form-select"
                style={{ width: 'auto', minWidth: '180px', padding: '6px 10px', fontSize: '12px' }}
                value={currentTopic}
                onChange={(e) => onTopicChange(e.target.value)}
              >
                {PPS_UNITS.map((u) => (
                  <optgroup key={u.unit} label={u.unit}>
                    {u.topics.map((t) => (
                      <option key={t} value={t}>
                        {t}
                      </option>
                    ))}
                  </optgroup>
                ))}
              </select>
            )}
            <button
              type="button"
              className={activeTab === 'mcq' ? 'btn-primary' : 'btn-secondary'}
              onClick={() => setActiveTab('mcq')}
              style={{ fontSize: '12px', padding: '6px 12px' }}
            >
              Curriculum MCQs (5 Questions) ✓
            </button>
            <button
              type="button"
              className={activeTab === 'ai_challenge' ? 'btn-primary' : 'btn-secondary'}
              onClick={() => {
                setActiveTab('ai_challenge');
                if (!aiProblems && !isLoadingAi) handleGenerateAiPractice(studentId, currentTopic);
              }}
              style={{ fontSize: '12px', padding: '6px 12px' }}
            >
              AI Coding Challenge (Hint Ladder) +
            </button>
          </div>
        </div>
      </header>

      {errorMessage && (
        <div className="error-box" style={{ marginBottom: '16px' }} role="alert">
          <h4>Notice</h4>
          <p>{errorMessage}</p>
        </div>
      )}

      {/* Mode 1: 5-Question Curriculum MCQs */}
      {activeTab === 'mcq' && (
        <>
          {isLoadingMcq && (
            <div className="card" style={{ textAlign: 'center', padding: '40px', color: 'var(--color-text-secondary)' }}>
              Loading 5 verified practice questions for {currentTopic}...
            </div>
          )}

          {!isLoadingMcq && practiceQuestions.length > 0 && !practiceSubmitted && currentQ && (
            <div className="card">
              {/* Question Navigation Header Bar */}
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px', flexWrap: 'wrap', gap: '10px' }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                  <span className="badge-blue">
                    Question {currentQIdx + 1} of {totalQuestions}
                  </span>
                  <span style={{ fontSize: '12px', color: 'var(--color-text-secondary)' }}>
                    Concept: <strong>{currentQ.concept || currentTopic}</strong> • Difficulty: <strong>{currentQ.difficulty || 'Intermediate'}</strong>
                  </span>
                </div>
                <div style={{ fontSize: '12px', color: 'var(--color-text-secondary)' }}>
                  Answered: <strong>{answeredCount} / {totalQuestions}</strong>
                </div>
              </div>

              {/* Progress Pills */}
              <div style={{ display: 'flex', gap: '6px', marginBottom: '20px' }}>
                {practiceQuestions.map((_, idx) => {
                  const isCurrent = idx === currentQIdx;
                  const isAnswered = practiceAnswers[idx] !== undefined;
                  return (
                    <button
                      key={idx}
                      type="button"
                      onClick={() => setCurrentQIdx(idx)}
                      style={{
                        padding: '6px 12px',
                        borderRadius: 'var(--radius-sm)',
                        fontSize: '12px',
                        fontWeight: 600,
                        border: isCurrent ? '2px solid var(--color-blue)' : '1px solid var(--color-border)',
                        backgroundColor: isCurrent ? 'var(--color-blue-light)' : isAnswered ? '#e0f2fe' : 'var(--color-surface)',
                        color: isCurrent ? 'var(--color-blue)' : 'var(--color-text-primary)',
                        cursor: 'pointer',
                        transition: 'all 0.15s ease',
                      }}
                      aria-label={`Jump to question ${idx + 1}`}
                    >
                      Q{idx + 1} {isAnswered ? '✓' : ''}
                    </button>
                  );
                })}
              </div>

              {/* Question Text */}
              <h3 style={{ fontSize: '16px', fontWeight: 600, lineHeight: 1.5, marginBottom: '20px', color: 'var(--color-text-primary)' }}>
                {currentQ.question}
              </h3>

              {/* Options List */}
              <div className="options-list" style={{ display: 'flex', flexDirection: 'column', gap: '10px', marginBottom: '24px' }}>
                {(currentQ.options || []).map((opt, optIdx) => {
                  const letter = opt.trim().charAt(0).toUpperCase();
                  const isSelected = practiceAnswers[currentQIdx] === letter;

                  return (
                    <button
                      key={optIdx}
                      type="button"
                      className={`option-button ${isSelected ? 'selected' : ''}`}
                      onClick={() => handleSelectAnswer(opt)}
                      style={{
                        textAlign: 'left',
                        padding: '12px 16px',
                        borderRadius: 'var(--radius-sm)',
                        border: isSelected ? '2px solid var(--color-blue)' : '1px solid var(--color-border)',
                        backgroundColor: isSelected ? 'var(--color-blue-light)' : '#ffffff',
                        cursor: 'pointer',
                        display: 'flex',
                        alignItems: 'center',
                        gap: '12px',
                        fontSize: '14px',
                        transition: 'all 0.1s ease',
                      }}
                    >
                      <span style={{ fontWeight: 700, width: '24px', color: isSelected ? 'var(--color-blue)' : 'var(--color-text-secondary)' }}>
                        {letter})
                      </span>
                      <span style={{ color: 'var(--color-text-primary)' }}>
                        {opt.substring(opt.indexOf(')') + 1).trim() || opt}
                      </span>
                    </button>
                  );
                })}
              </div>

              {/* Navigation Controls & Submit */}
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', borderTop: '1px solid var(--color-border)', paddingTop: '16px' }}>
                <button
                  type="button"
                  className="btn-secondary"
                  onClick={() => setCurrentQIdx((prev) => Math.max(0, prev - 1))}
                  disabled={currentQIdx === 0}
                  style={{ fontSize: '13px', padding: '6px 14px' }}
                >
                  ← Previous Question
                </button>

                <div style={{ display: 'flex', gap: '10px' }}>
                  {currentQIdx < totalQuestions - 1 ? (
                    <button
                      type="button"
                      className="btn-secondary"
                      onClick={() => setCurrentQIdx((prev) => Math.min(totalQuestions - 1, prev + 1))}
                      style={{ fontSize: '13px', padding: '6px 14px' }}
                    >
                      Next Question →
                    </button>
                  ) : null}

                  <button
                    type="button"
                    className="btn-primary"
                    onClick={handleSubmitPractice}
                    disabled={isSubmittingMcq || answeredCount === 0}
                    style={{ fontSize: '13px', padding: '6px 16px' }}
                  >
                    {isSubmittingMcq ? 'Evaluating Session...' : `Submit Practice Session (${answeredCount}/${totalQuestions})`}
                  </button>
                </div>
              </div>
            </div>
          )}

          {/* Mode 1: Comprehensive Practice Results View */}
          {practiceSubmitted && practiceResult && (
            <div className="card">
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px', flexWrap: 'wrap', gap: '10px' }}>
                <div>
                  <h3 style={{ fontSize: '18px', fontWeight: 700, margin: 0, color: 'var(--color-text-primary)' }}>
                    Practice Session Results: {currentTopic}
                  </h3>
                  <span style={{ fontSize: '12px', color: 'var(--color-text-secondary)' }}>
                    Authoritative Backend Evaluation • 5 Grounded Practice Questions
                  </span>
                </div>
                <span className={practiceResult.score >= 60 ? 'badge-green' : 'badge-red'} style={{ fontSize: '13px', padding: '4px 10px' }}>
                  {practiceResult.score >= 60 ? '✓ Practice Passed' : 'Needs Review'}
                </span>
              </div>

              {/* Performance Stats Grid */}
              <div className="stats-grid" style={{ marginBottom: '20px' }}>
                <div className="stat-box">
                  <div className="stat-label">Score</div>
                  <div className="stat-value" style={{ color: practiceResult.score >= 60 ? 'var(--color-green)' : 'var(--color-red)' }}>
                    {practiceResult.score} / 100
                  </div>
                </div>
                <div className="stat-box">
                  <div className="stat-label">Accuracy</div>
                  <div className="stat-value">
                    {Math.round(practiceResult.accuracy * 100)}%
                  </div>
                </div>
                <div className="stat-box">
                  <div className="stat-label">Correct Answers</div>
                  <div className="stat-value">
                    {practiceResult.correct_count} / {practiceResult.total_questions}
                  </div>
                </div>
                <div className="stat-box">
                  <div className="stat-label">Time Taken</div>
                  <div className="stat-value">
                    {practiceResult.time_taken_seconds} sec
                  </div>
                </div>
              </div>

              {/* Weak Concepts Alert Box */}
              {practiceResult.weak_concepts && practiceResult.weak_concepts.length > 0 && (
                <div
                  style={{
                    backgroundColor: 'var(--color-red-light)',
                    border: '1px solid var(--color-red-border)',
                    borderRadius: 'var(--radius-sm)',
                    padding: '14px 18px',
                    marginBottom: '20px',
                    color: 'var(--color-red)',
                    fontSize: '13px',
                  }}
                  role="region"
                  aria-label="Weak Concepts Review"
                >
                  <strong style={{ display: 'block', marginBottom: '4px' }}>
                    ⚠️ Weak Concepts Identified for Focused Revision:
                  </strong>
                  <span>{practiceResult.weak_concepts.join(' • ')}</span>
                </div>
              )}

              {/* Feedback Text */}
              <div style={{ backgroundColor: 'var(--color-surface-subtle)', border: '1px solid var(--color-border)', borderRadius: 'var(--radius-sm)', padding: '14px', marginBottom: '24px' }}>
                <div style={{ fontSize: '13px', fontWeight: 700, marginBottom: '4px' }}>Learning Twin Analysis:</div>
                <div style={{ fontSize: '13px', color: 'var(--color-text-primary)', lineHeight: 1.5 }}>
                  {practiceResult.feedback}
                </div>
              </div>

              {/* Detailed Breakdown for All 5 Questions */}
              <h4 style={{ fontSize: '14px', fontWeight: 700, marginBottom: '12px', color: 'var(--color-text-primary)' }}>
                Detailed Question Review (5 Questions):
              </h4>
              <div style={{ display: 'flex', flexDirection: 'column', gap: '14px', marginBottom: '24px' }}>
                {(practiceResult.results || []).map((item, idx) => (
                  <div
                    key={idx}
                    style={{
                      border: '1px solid var(--color-border)',
                      borderRadius: 'var(--radius-sm)',
                      padding: '14px',
                      backgroundColor: item.is_correct ? 'var(--color-surface)' : 'var(--color-surface-subtle)',
                    }}
                  >
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '8px' }}>
                      <span style={{ fontWeight: 700, fontSize: '13px' }}>Question {idx + 1}: {item.concept}</span>
                      <span className={item.is_correct ? 'badge-green' : 'badge-red'}>
                        {item.is_correct ? '✓ Correct' : '× Incorrect'}
                      </span>
                    </div>
                    <div style={{ fontSize: '14px', fontWeight: 600, marginBottom: '8px', color: 'var(--color-text-primary)' }}>
                      {item.question}
                    </div>
                    <div style={{ fontSize: '13px', display: 'flex', gap: '20px', marginBottom: '8px' }}>
                      <span>Your answer: <strong>{item.student_answer}</strong></span>
                      <span>Correct answer: <strong style={{ color: 'var(--color-green)' }}>{item.correct_answer}</strong></span>
                    </div>
                    <div style={{ fontSize: '12px', color: 'var(--color-text-secondary)', borderTop: '1px solid var(--color-border)', paddingTop: '6px' }}>
                      <strong>Explanation:</strong> {item.explanation}
                    </div>
                  </div>
                ))}
              </div>

              {/* Action Buttons */}
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', borderTop: '1px solid var(--color-border)', paddingTop: '16px', flexWrap: 'wrap', gap: '10px' }}>
                <button
                  type="button"
                  className="btn-secondary"
                  onClick={handleResetPractice}
                >
                  Practice Again ⟳
                </button>
                <div style={{ display: 'flex', gap: '10px' }}>
                  <button
                    type="button"
                    className="btn-secondary"
                    onClick={() => onNavigate('tutor')}
                  >
                    Ask AI Tutor ?
                  </button>
                  <button
                    type="button"
                    className="btn-primary"
                    onClick={() => onNavigate('tests')}
                  >
                    Take Full 10-Question Assessment Test →
                  </button>
                </div>
              </div>
            </div>
          )}
        </>
      )}

      {/* Mode 2: AI Adaptive Coding Challenge with Scaffolding Hint Ladder */}
      {activeTab === 'ai_challenge' && (
        <div className="card">
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '14px', flexWrap: 'wrap', gap: '10px' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
              <span className="badge-blue">GenAI Adaptive Practice with Mistral 7B</span>
              <span style={{ fontSize: '12px', color: 'var(--color-text-secondary)' }}>
                Curriculum Grounded • XGBoost Adaptive
              </span>
            </div>
            <button
              type="button"
              className="btn-pill"
              onClick={() => handleGenerateAiPractice(studentId, currentTopic)}
              disabled={isLoadingAi}
            >
              {isLoadingAi ? 'Generating Challenge...' : 'Regenerate Challenge ⟳'}
            </button>
          </div>

          {isLoadingAi && (
            <div style={{ textAlign: 'center', padding: '40px', color: 'var(--color-text-secondary)' }}>
              Generating mastery-adapted C coding challenge with scaffolded hint ladder for Student <strong>{studentId}</strong>...
            </div>
          )}

          {!isLoadingAi && aiProblems && currentChallenge && (
            <div>
              {/* Challenge Information Bar */}
              <div style={{ backgroundColor: 'var(--color-surface-subtle)', border: '1px solid var(--color-border)', borderRadius: 'var(--radius-sm)', padding: '12px 16px', marginBottom: '20px', display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '10px', fontSize: '13px' }}>
                <div>
                  Adapted for: <strong>Student {aiProblems.student_id}</strong> &nbsp;•&nbsp; 
                  Target Mastery: <strong>{aiProblems.target_mastery || '1.00'}</strong> &nbsp;•&nbsp; 
                  Difficulty: <strong className="badge-blue" style={{ fontSize: '11px', padding: '2px 8px', marginLeft: '4px' }}>{aiProblems.recommended_difficulty || currentChallenge.difficulty || 'Advanced'}</strong>
                  {aiProblems.learning_pace && (
                    <span> &nbsp;•&nbsp; Pace: <strong>{aiProblems.learning_pace}</strong></span>
                  )}
                </div>
                <div style={{ fontSize: '12px', color: 'var(--color-text-muted)' }}>
                  Model: <strong>{aiProblems.model || 'mistral:7b'}</strong>
                </div>
              </div>

              {/* Problem Statement Section */}
              <div style={{ marginBottom: '24px' }}>
                <h3 style={{ fontSize: '18px', fontWeight: 700, marginBottom: '10px', color: 'var(--color-text-primary)' }}>
                  {currentChallenge.title || `${currentTopic}: Adaptive Coding Challenge`}
                </h3>
                <p style={{ fontSize: '14px', lineHeight: 1.6, marginBottom: '16px', color: 'var(--color-text-primary)', whiteSpace: 'pre-line' }}>
                  {currentChallenge.problem_statement || currentChallenge.description}
                </p>

                {/* Specification Table / Grid */}
                <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))', gap: '12px', marginBottom: '16px', backgroundColor: '#fff', border: '1px solid var(--color-border)', borderRadius: 'var(--radius-sm)', padding: '14px' }}>
                  <div>
                    <div style={{ fontSize: '12px', fontWeight: 700, color: 'var(--color-text-secondary)', marginBottom: '4px' }}>Input Format:</div>
                    <div style={{ fontSize: '13px', color: 'var(--color-text-primary)' }}>{currentChallenge.input_format || 'Standard input or test harness initial parameters.'}</div>
                  </div>
                  <div>
                    <div style={{ fontSize: '12px', fontWeight: 700, color: 'var(--color-text-secondary)', marginBottom: '4px' }}>Output Format:</div>
                    <div style={{ fontSize: '13px', color: 'var(--color-text-primary)' }}>{currentChallenge.output_format || 'Exact output printed to stdout.'}</div>
                  </div>
                  <div style={{ gridColumn: '1 / -1' }}>
                    <div style={{ fontSize: '12px', fontWeight: 700, color: 'var(--color-text-secondary)', marginBottom: '4px' }}>Constraints:</div>
                    <div style={{ fontSize: '13px', color: 'var(--color-text-primary)' }}>{currentChallenge.constraints || 'Standard C99 compliance, no invalid memory references.'}</div>
                  </div>
                </div>

                {/* Sample Test Case Box */}
                {(currentChallenge.sample_input || currentChallenge.sample_output) && (
                  <div style={{ backgroundColor: 'var(--color-surface-subtle)', border: '1px solid var(--color-border)', borderRadius: 'var(--radius-sm)', padding: '14px', marginBottom: '20px' }}>
                    <div style={{ fontSize: '13px', fontWeight: 700, marginBottom: '8px' }}>Sample Test Case:</div>
                    <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '12px', marginBottom: '8px' }}>
                      {currentChallenge.sample_input && (
                        <div>
                          <div style={{ fontSize: '11px', fontWeight: 600, color: 'var(--color-text-secondary)', marginBottom: '2px' }}>Sample Input:</div>
                          <pre style={{ backgroundColor: '#fff', border: '1px solid var(--color-border)', padding: '6px 10px', borderRadius: 'var(--radius-sm)', fontSize: '12px', fontFamily: 'var(--font-mono)' }}>
                            {currentChallenge.sample_input}
                          </pre>
                        </div>
                      )}
                      {currentChallenge.sample_output && (
                        <div>
                          <div style={{ fontSize: '11px', fontWeight: 600, color: 'var(--color-text-secondary)', marginBottom: '2px' }}>Sample Output:</div>
                          <pre style={{ backgroundColor: '#fff', border: '1px solid var(--color-border)', padding: '6px 10px', borderRadius: 'var(--radius-sm)', fontSize: '12px', fontFamily: 'var(--font-mono)' }}>
                            {currentChallenge.sample_output}
                          </pre>
                        </div>
                      )}
                    </div>
                    {currentChallenge.sample_explanation && (
                      <div style={{ fontSize: '12px', color: 'var(--color-text-secondary)', marginTop: '4px' }}>
                        <strong>Explanation:</strong> {currentChallenge.sample_explanation}
                      </div>
                    )}
                  </div>
                )}

                {/* Interactive 4-Tier Scaffolded Hint Ladder */}
                <div style={{ backgroundColor: 'var(--color-surface-subtle)', border: '1px solid var(--color-border)', borderRadius: 'var(--radius-sm)', padding: '16px', marginBottom: '24px' }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '10px' }}>
                    <h4 style={{ fontSize: '13px', fontWeight: 700, color: 'var(--color-text-primary)' }}>
                      Scaffolded Hint Ladder (Progressive Guidance):
                    </h4>
                    <span style={{ fontSize: '11px', color: 'var(--color-text-muted)' }}>
                      Click to reveal progressive hints without spoiling the solution
                    </span>
                  </div>
                  <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
                    {[
                      { key: 'hint_1', label: '💡 Hint 1: Conceptual Guidance', text: currentChallenge.hint_1 || (currentChallenge.hints && currentChallenge.hints[0]) },
                      { key: 'hint_2', label: '🔍 Hint 2: Specific Approach', text: currentChallenge.hint_2 || (currentChallenge.hints && currentChallenge.hints[1]) },
                      { key: 'hint_3', label: '⚙️ Hint 3: Algorithmic Guidance', text: currentChallenge.hint_3 || (currentChallenge.hints && currentChallenge.hints[2]) },
                      { key: 'hint_4', label: '🔑 Hint 4: Pseudocode / Implementation Direction', text: currentChallenge.hint_4 || (currentChallenge.hints && currentChallenge.hints[3]) },
                    ].map((h, hIdx) => {
                      const isRevealed = !!revealedHints[h.key];
                      if (!h.text) return null;
                      return (
                        <div key={hIdx} style={{ border: '1px solid var(--color-border)', borderRadius: 'var(--radius-sm)', backgroundColor: '#fff' }}>
                          <button
                            type="button"
                            onClick={() => setRevealedHints((prev) => ({ ...prev, [h.key]: !prev[h.key] }))}
                            style={{
                              width: '100%',
                              textAlign: 'left',
                              padding: '10px 14px',
                              background: 'transparent',
                              border: 'none',
                              cursor: 'pointer',
                              display: 'flex',
                              justifyContent: 'space-between',
                              alignItems: 'center',
                              fontSize: '13px',
                              fontWeight: 600,
                              color: isRevealed ? 'var(--color-blue)' : 'var(--color-text-primary)',
                            }}
                          >
                            <span>{h.label}</span>
                            <span style={{ fontSize: '11px', color: 'var(--color-text-muted)' }}>
                              {isRevealed ? 'Hide ▲' : 'Reveal ▼'}
                            </span>
                          </button>
                          {isRevealed && (
                            <div style={{ padding: '0 14px 12px 14px', fontSize: '13px', color: 'var(--color-text-secondary)', lineHeight: 1.5, borderTop: '1px dashed var(--color-border)', paddingTop: '8px' }}>
                              {h.text}
                            </div>
                          )}
                        </div>
                      );
                    })}
                  </div>
                </div>

                {/* C Language Source Editor Section */}
                <div style={{ marginBottom: '20px' }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '8px' }}>
                    <div style={{ fontSize: '13px', fontWeight: 700, color: 'var(--color-text-primary)' }}>
                      C Source Code Editor (C99 • Sandboxed Execution)
                    </div>
                    <button
                      type="button"
                      className="btn-pill"
                      onClick={handleResetCode}
                      style={{ fontSize: '11px' }}
                    >
                      Reset Starter Code ↺
                    </button>
                  </div>

                  <textarea
                    value={studentCode}
                    onChange={(e) => setStudentCode(e.target.value)}
                    rows={24}
                    style={{
                      width: '100%',
                      minHeight: '480px',
                      fontFamily: 'var(--font-mono)',
                      fontSize: '13px',
                      lineHeight: 1.5,
                      padding: '16px 18px',
                      backgroundColor: '#0f172a',
                      color: '#f8fafc',
                      borderRadius: 'var(--radius-sm)',
                      border: '1px solid #334155',
                      boxSizing: 'border-box',
                      resize: 'vertical',
                    }}
                    placeholder="// Write your C solution here..."
                    aria-label="C code editor"
                  />
                </div>

                {/* Editor Action Buttons */}
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '20px', flexWrap: 'wrap', gap: '10px' }}>
                  <span style={{ fontSize: '12px', color: 'var(--color-text-muted)' }}>
                    Protected execution via 64-bit GCC compiler (C99 • Sandboxed • Strict 3.0s Timeout).
                  </span>
                  <div style={{ display: 'flex', gap: '10px' }}>
                    <button
                      type="button"
                      className="btn-secondary"
                      onClick={handleRunCode}
                      disabled={isRunningCode || isSubmittingCode}
                    >
                      {isRunningCode ? 'Compiling & Running...' : '▶ Run Code'}
                    </button>
                    <button
                      type="button"
                      className="btn-primary"
                      onClick={handleSubmitCode}
                      disabled={isSubmittingCode || isRunningCode}
                    >
                      {isSubmittingCode ? 'Evaluating Test Cases...' : '✓ Submit Code'}
                    </button>
                  </div>
                </div>

                {/* Compilation & Execution Results Panel */}
                {execResult && (
                  <div
                    style={{
                      backgroundColor:
                        execResult.status === 'ACCEPTED' || execResult.passed
                          ? 'var(--color-green-light)'
                          : execResult.status === 'WRONG_ANSWER'
                          ? '#fff7ed'
                          : execResult.status === 'SUCCESS'
                          ? '#eff6ff'
                          : 'var(--color-red-light)',
                      border: `1px solid ${
                        execResult.status === 'ACCEPTED' || execResult.passed
                          ? 'var(--color-green-border)'
                          : execResult.status === 'WRONG_ANSWER'
                          ? '#fed7aa'
                          : execResult.status === 'SUCCESS'
                          ? '#bfdbfe'
                          : 'var(--color-red-border)'
                      }`,
                      borderRadius: 'var(--radius-sm)',
                      padding: '16px 18px',
                      marginBottom: '16px',
                    }}
                    role="region"
                    aria-label="Code execution results"
                  >
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '10px', flexWrap: 'wrap', gap: '8px' }}>
                      <div
                        style={{
                          fontWeight: 700,
                          fontSize: '15px',
                          color:
                            execResult.status === 'ACCEPTED' || execResult.passed
                              ? 'var(--color-green)'
                              : execResult.status === 'WRONG_ANSWER'
                              ? '#ea580c'
                              : execResult.status === 'SUCCESS'
                              ? 'var(--color-blue)'
                              : 'var(--color-red)',
                        }}
                      >
                        {execResult.status === 'ACCEPTED' || execResult.passed
                          ? '✓ Accepted — Test Case Passed!'
                          : execResult.status === 'WRONG_ANSWER'
                          ? '× Wrong Answer — Output Mismatch'
                          : execResult.status === 'COMPILATION_ERROR'
                          ? '× Compilation Failed'
                          : execResult.status === 'RUNTIME_ERROR'
                          ? `× Runtime Error (Exit Code: ${execResult.exit_code ?? -1})`
                          : execResult.status === 'TIMEOUT'
                          ? '⏱ Time Limit Exceeded (3.0s Timeout)'
                          : '▶ Program Executed Successfully'}
                      </div>
                      <div style={{ fontSize: '12px', color: 'var(--color-text-secondary)' }}>
                        Execution Time: <strong>{execResult.execution_time_seconds ?? 0}s</strong>
                      </div>
                    </div>

                    {execResult.diagnostic_message && (
                      <p style={{ fontSize: '13px', margin: '0 0 12px 0', color: 'var(--color-text-primary)' }}>
                        {execResult.diagnostic_message}
                      </p>
                    )}

                    {/* Compilation Error Display */}
                    {(execResult.status === 'COMPILATION_ERROR' || execResult.compiler_output) && !execResult.success && (
                      <div style={{ marginBottom: '12px' }}>
                        <div style={{ fontSize: '12px', fontWeight: 700, color: 'var(--color-red)', marginBottom: '4px' }}>
                          GCC Compiler Diagnostics (stderr):
                        </div>
                        <pre
                          style={{
                            backgroundColor: '#0f172a',
                            color: '#f87171',
                            padding: '12px 14px',
                            borderRadius: 'var(--radius-sm)',
                            fontSize: '12px',
                            fontFamily: 'var(--font-mono)',
                            overflowX: 'auto',
                            whiteSpace: 'pre-wrap',
                            margin: 0,
                          }}
                        >
                          {execResult.compiler_output || execResult.stderr || 'Compilation failed without output.'}
                        </pre>
                      </div>
                    )}

                    {/* Runtime Error Display */}
                    {execResult.status === 'RUNTIME_ERROR' && execResult.stderr && (
                      <div style={{ marginBottom: '12px' }}>
                        <div style={{ fontSize: '12px', fontWeight: 700, color: 'var(--color-red)', marginBottom: '4px' }}>
                          Runtime Diagnostics (stderr):
                        </div>
                        <pre
                          style={{
                            backgroundColor: '#0f172a',
                            color: '#f87171',
                            padding: '12px 14px',
                            borderRadius: 'var(--radius-sm)',
                            fontSize: '12px',
                            fontFamily: 'var(--font-mono)',
                            overflowX: 'auto',
                            whiteSpace: 'pre-wrap',
                            margin: 0,
                          }}
                        >
                          {execResult.stderr}
                        </pre>
                      </div>
                    )}

                    {/* Timeout Guidance */}
                    {execResult.status === 'TIMEOUT' && (
                      <div style={{ marginBottom: '12px', backgroundColor: '#fff', border: '1px solid var(--color-red-border)', padding: '10px 14px', borderRadius: 'var(--radius-sm)', fontSize: '12px', color: 'var(--color-red)' }}>
                        <strong>Diagnostic Note:</strong> {execResult.notes || 'The program took longer than 3.0 seconds to finish. Check for infinite loops or waiting for unsupplied scanf() input.'}
                      </div>
                    )}

                    {/* Wrong Answer Output Comparison */}
                    {execResult.status === 'WRONG_ANSWER' && (
                      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))', gap: '12px', marginBottom: '12px' }}>
                        <div>
                          <div style={{ fontSize: '12px', fontWeight: 700, color: 'var(--color-green)', marginBottom: '4px' }}>
                            Expected Output:
                          </div>
                          <pre
                            style={{
                              backgroundColor: '#0f172a',
                              color: '#4ade80',
                              padding: '10px 12px',
                              borderRadius: 'var(--radius-sm)',
                              fontSize: '12px',
                              fontFamily: 'var(--font-mono)',
                              overflowX: 'auto',
                              whiteSpace: 'pre-wrap',
                              margin: 0,
                            }}
                          >
                            {execResult.expected_output || '(Empty expected output)'}
                          </pre>
                        </div>
                        <div>
                          <div style={{ fontSize: '12px', fontWeight: 700, color: 'var(--color-red)', marginBottom: '4px' }}>
                            Your Actual Output:
                          </div>
                          <pre
                            style={{
                              backgroundColor: '#0f172a',
                              color: '#f87171',
                              padding: '10px 12px',
                              borderRadius: 'var(--radius-sm)',
                              fontSize: '12px',
                              fontFamily: 'var(--font-mono)',
                              overflowX: 'auto',
                              whiteSpace: 'pre-wrap',
                              margin: 0,
                            }}
                          >
                            {execResult.actual_output || '(No standard output generated)'}
                          </pre>
                        </div>
                      </div>
                    )}

                    {/* Standard Output Display for Accepted or Success */}
                    {(execResult.status === 'ACCEPTED' || execResult.status === 'SUCCESS' || execResult.passed) && execResult.stdout && (
                      <div style={{ marginBottom: '10px' }}>
                        <div style={{ fontSize: '12px', fontWeight: 700, color: 'var(--color-text-secondary)', marginBottom: '4px' }}>
                          Program Output (stdout):
                        </div>
                        <pre
                          style={{
                            backgroundColor: '#0f172a',
                            color: '#f8fafc',
                            padding: '10px 12px',
                            borderRadius: 'var(--radius-sm)',
                            fontSize: '12px',
                            fontFamily: 'var(--font-mono)',
                            overflowX: 'auto',
                            whiteSpace: 'pre-wrap',
                            margin: 0,
                          }}
                        >
                          {execResult.stdout}
                        </pre>
                      </div>
                    )}
                  </div>
                )}
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
