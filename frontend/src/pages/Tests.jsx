import React, { useEffect, useState } from 'react';
import { fetchTopicAssessment, submitAssessmentAnswer } from '../api/learningApi';

export default function Tests({
  studentId = 'S001',
  currentTopic = 'Pointers',
  onTestCompleted,
}) {
  const [testState, setTestState] = useState('intro'); // 'intro' | 'active' | 'confirm'
  const [questions, setQuestions] = useState([]);
  const [currentIdx, setCurrentIdx] = useState(0);
  const [answers, setAnswers] = useState({});
  const [startTime, setStartTime] = useState(null);
  const [isSubmitting, setIsSubmitting] = useState(false);

  useEffect(() => {
    fetchTopicAssessment(studentId, currentTopic)
      .then((data) => {
        // Construct realistic assessment questions for PPS
        setQuestions([
          data,
          {
            question: 'What is the format specifier used in printf to display a pointer address in C?',
            options: ['A) %d', 'B) %p', 'C) %x', 'D) %u'],
            correct_option: 'B',
            explanation: 'The %p format specifier formats memory addresses as hexadecimal pointer representations.',
          },
          {
            question: 'What occurs if an integer pointer `ptr` is incremented with `ptr++` where `sizeof(int) == 4`?',
            options: [
              'A) It points to memory 1 byte ahead',
              'B) It points to memory 4 bytes ahead',
              'C) It produces a compilation error',
              'D) It doubles the memory location',
            ],
            correct_option: 'B',
            explanation: 'Pointer arithmetic increments addresses by the byte size of the referenced data type.',
          },
        ]);
      })
      .catch((err) => console.warn(err));
  }, [studentId, currentTopic]);

  const handleStartTest = () => {
    setTestState('active');
    setStartTime(Date.now());
  };

  const handleSelectOption = (letter) => {
    setAnswers((prev) => ({
      ...prev,
      [currentIdx]: letter,
    }));
  };

  const handleSubmitTest = async () => {
    setIsSubmitting(true);
    const durationSec = Math.round((Date.now() - (startTime || Date.now())) / 1000);
    const primaryOption = answers[0] || 'B';

    try {
      const res = await submitAssessmentAnswer(studentId, currentTopic, primaryOption, durationSec || 25);
      if (onTestCompleted) {
        onTestCompleted({
          ...res,
          questions: questions,
          studentAnswers: answers,
          timeTaken: durationSec || 25,
        });
      }
    } catch (err) {
      alert('Error submitting test: ' + err.message);
    } finally {
      setIsSubmitting(false);
    }
  };

  if (testState === 'intro') {
    return (
      <div className="tests-page">
        <header className="page-header">
          <h2 className="page-title">PPS Assessment</h2>
          <p className="page-subtitle">Test and verify your conceptual understanding of <strong>{currentTopic}</strong>.</p>
        </header>

        <div className="card">
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px' }}>
            <span className="badge-blue">Diagnostic Assessment</span>
            <span style={{ fontSize: '13px', color: 'var(--color-text-secondary)' }}>
              Course: Programming for Problem Solving
            </span>
          </div>

          <div style={{ marginBottom: '20px' }}>
            <table className="kv-table" style={{ width: '100%', fontSize: '14px' }}>
              <tbody>
                <tr style={{ borderBottom: '1px solid var(--color-border)' }}>
                  <td style={{ padding: '8px 0', color: 'var(--color-text-secondary)' }}>Topic</td>
                  <td style={{ textAlign: 'right', fontWeight: 600 }}>{currentTopic}</td>
                </tr>
                <tr style={{ borderBottom: '1px solid var(--color-border)' }}>
                  <td style={{ padding: '8px 0', color: 'var(--color-text-secondary)' }}>Difficulty</td>
                  <td style={{ textAlign: 'right', fontWeight: 600 }}>Advanced</td>
                </tr>
                <tr style={{ borderBottom: '1px solid var(--color-border)' }}>
                  <td style={{ padding: '8px 0', color: 'var(--color-text-secondary)' }}>Questions</td>
                  <td style={{ textAlign: 'right', fontWeight: 600 }}>{questions.length || 3}</td>
                </tr>
                <tr>
                  <td style={{ padding: '8px 0', color: 'var(--color-text-secondary)' }}>Estimated Time</td>
                  <td style={{ textAlign: 'right', fontWeight: 600 }}>3 minutes</td>
                </tr>
              </tbody>
            </table>
          </div>

          <button
            type="button"
            className="btn-primary"
            onClick={handleStartTest}
            disabled={questions.length === 0}
          >
            Start Test →
          </button>
        </div>
      </div>
    );
  }

  const q = questions[currentIdx] || {};
  const currentAnswer = answers[currentIdx];
  const answeredCount = Object.keys(answers).length;

  return (
    <div className="tests-page">
      <header className="page-header" style={{ marginBottom: '16px' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <div>
            <h2 className="page-title" style={{ fontSize: '20px' }}>
              {currentTopic} Assessment
            </h2>
            <p className="page-subtitle">
              Question {currentIdx + 1} of {questions.length}
            </p>
          </div>
          {/* Question Progress Dots */}
          <div style={{ display: 'flex', gap: '6px' }}>
            {questions.map((_, idx) => {
              const isAnswered = answers[idx] !== undefined;
              const isCur = idx === currentIdx;
              return (
                <button
                  key={idx}
                  type="button"
                  style={{
                    width: '32px',
                    height: '32px',
                    border: '1px solid var(--color-border)',
                    borderRadius: 'var(--radius-sm)',
                    fontWeight: 700,
                    fontSize: '12px',
                    cursor: 'pointer',
                    backgroundColor: isCur
                      ? 'var(--color-blue)'
                      : isAnswered
                      ? 'var(--color-green-light)'
                      : '#ffffff',
                    color: isCur
                      ? '#ffffff'
                      : isAnswered
                      ? 'var(--color-green)'
                      : 'var(--color-text-secondary)',
                    borderColor: isCur ? 'var(--color-blue)' : 'var(--color-border)',
                  }}
                  onClick={() => setCurrentIdx(idx)}
                >
                  {idx + 1}
                </button>
              );
            })}
          </div>
        </div>
      </header>

      {/* Question Card */}
      <div className="card">
        <h3 style={{ fontSize: '16px', fontWeight: 600, lineHeight: 1.5, marginBottom: '20px' }}>
          {q.question}
        </h3>

        <div className="options-list">
          {(q.options || []).map((opt, idx) => {
            const letter = opt.trim().charAt(0);
            const isSelected = currentAnswer === letter;
            return (
              <button
                key={idx}
                type="button"
                className={`option-button ${isSelected ? 'selected' : ''}`}
                onClick={() => handleSelectOption(letter)}
              >
                <span style={{ fontWeight: 700, width: '28px' }}>{letter})</span>
                <span>{opt.substring(opt.indexOf(')') + 1).trim() || opt}</span>
              </button>
            );
          })}
        </div>

        {/* Footer controls */}
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginTop: '24px' }}>
          <button
            type="button"
            className="btn-secondary"
            disabled={currentIdx === 0}
            onClick={() => setCurrentIdx((prev) => prev - 1)}
          >
            ← Previous
          </button>

          {currentIdx < questions.length - 1 ? (
            <button
              type="button"
              className="btn-primary"
              style={{ width: 'auto' }}
              onClick={() => setCurrentIdx((prev) => prev + 1)}
            >
              Next →
            </button>
          ) : (
            <button
              type="button"
              className="btn-primary"
              style={{ width: 'auto', backgroundColor: 'var(--color-green)', borderColor: 'var(--color-green)' }}
              onClick={() => setTestState('confirm')}
            >
              Finish & Review →
            </button>
          )}
        </div>
      </div>

      {/* Confirmation Modal / Section */}
      {testState === 'confirm' && (
        <div className="card" style={{ border: '2px solid var(--color-blue)', backgroundColor: 'var(--color-surface)' }}>
          <h3 style={{ fontSize: '16px', fontWeight: 700, marginBottom: '10px' }}>Submit Assessment</h3>
          <p style={{ fontSize: '14px', color: 'var(--color-text-secondary)', marginBottom: '14px' }}>
            Are you sure you want to submit your answers?
          </p>
          <div style={{ display: 'flex', gap: '16px', marginBottom: '18px', fontSize: '13px' }}>
            <span>Answered: <strong>{answeredCount} / {questions.length}</strong></span>
            <span>Unanswered: <strong>{questions.length - answeredCount}</strong></span>
          </div>
          <div style={{ display: 'flex', gap: '10px' }}>
            <button
              type="button"
              className="btn-secondary"
              onClick={() => setTestState('active')}
              disabled={isSubmitting}
            >
              Cancel
            </button>
            <button
              type="button"
              className="btn-primary"
              style={{ width: 'auto' }}
              onClick={handleSubmitTest}
              disabled={isSubmitting}
            >
              {isSubmitting ? 'Evaluating Assessment...' : 'Submit Test'}
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
