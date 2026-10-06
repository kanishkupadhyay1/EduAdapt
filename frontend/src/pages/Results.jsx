import React from 'react';

export default function Results({
  testResult,
  currentTopic = 'Pointers',
  onNavigate,
}) {
  if (!testResult) {
    return (
      <div className="results-page">
        <header className="page-header">
          <h2 className="page-title">Assessment Results</h2>
          <p className="page-subtitle">No recent test completed.</p>
        </header>
        <div className="card" style={{ textAlign: 'center', padding: '40px' }}>
          <p style={{ color: 'var(--color-text-secondary)', marginBottom: '16px' }}>
            Complete an assessment in the Tests tab to view your score, performance breakdown, and personalized feedback.
          </p>
          <button
            type="button"
            className="btn-primary"
            style={{ width: 'auto' }}
            onClick={() => onNavigate('tests')}
          >
            Go to Tests →
          </button>
        </div>
      </div>
    );
  }

  const score = testResult.score ?? 95;
  const isCorrect = testResult.is_correct ?? true;
  const accuracy = isCorrect ? '100%' : '35%';
  const timeTaken = testResult.time_taken_seconds || testResult.timeTaken || 25;
  const feedbackText = testResult.feedback || 'You have demonstrated strong understanding of PPS pointer fundamentals.';
  const questions = testResult.questions || [];
  const studentAnswers = testResult.studentAnswers || {};

  return (
    <div className="results-page">
      <header className="page-header">
        <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
          <span className="badge-green">Test Completed</span>
          <span style={{ fontSize: '13px', color: 'var(--color-text-secondary)' }}>Topic: {currentTopic}</span>
        </div>
        <h2 className="page-title" style={{ marginTop: '8px' }}>Assessment Results</h2>
        <p className="page-subtitle">Evaluated by EduAdapt Post-Learning Assessment & Learning Twin verification.</p>
      </header>

      {/* Summary Score Card */}
      <div className="card">
        <h3 className="card-title">Performance Summary</h3>
        <div className="stats-grid">
          <div className="stat-box">
            <div className="stat-label">Score</div>
            <div className="stat-value" style={{ color: isCorrect ? 'var(--color-green)' : 'var(--color-red)' }}>
              {score} / 100
            </div>
          </div>
          <div className="stat-box">
            <div className="stat-label">Accuracy</div>
            <div className="stat-value" style={{ color: isCorrect ? 'var(--color-green)' : 'var(--color-red)' }}>
              {accuracy}
            </div>
          </div>
          <div className="stat-box">
            <div className="stat-label">Attempts</div>
            <div className="stat-value">1</div>
          </div>
          <div className="stat-box">
            <div className="stat-label">Time Taken</div>
            <div className="stat-value">{timeTaken} sec</div>
          </div>
        </div>
      </div>

      {/* Question Review */}
      {questions.length > 0 && (
        <div className="card">
          <h3 className="card-title">Question Review</h3>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
            {questions.map((q, idx) => {
              const studentChoice = studentAnswers[idx] || testResult.selected_option || 'B';
              const correctChoice = q.correct_option || 'B';
              const passed = studentChoice === correctChoice;

              return (
                <div
                  key={idx}
                  style={{
                    border: '1px solid var(--color-border)',
                    borderRadius: 'var(--radius-sm)',
                    padding: '14px',
                    backgroundColor: 'var(--color-surface-subtle)',
                  }}
                >
                  <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '8px' }}>
                    <span style={{ fontWeight: 700, fontSize: '13px' }}>Question {idx + 1}</span>
                    <span className={passed ? 'badge-green' : 'badge-red'}>
                      {passed ? '✓ Correct' : '× Incorrect'}
                    </span>
                  </div>
                  <div style={{ fontSize: '14px', fontWeight: 600, marginBottom: '10px' }}>
                    {q.question}
                  </div>
                  <div style={{ fontSize: '13px', display: 'flex', gap: '20px', marginBottom: '8px' }}>
                    <span>Your answer: <strong>{studentChoice}</strong></span>
                    <span>Correct answer: <strong style={{ color: 'var(--color-green)' }}>{correctChoice}</strong></span>
                  </div>
                  <div style={{ fontSize: '12px', color: 'var(--color-text-secondary)', borderTop: '1px solid var(--color-border)', paddingTop: '6px' }}>
                    <strong>Explanation:</strong> {q.explanation}
                  </div>
                  {!passed && (
                    <div style={{ marginTop: '8px', fontSize: '12px', color: 'var(--color-red)' }}>
                      <strong>What to revise:</strong> Review memory address referencing (&) and dereferencing (*) syntax in C.
                    </div>
                  )}
                </div>
              );
            })}
          </div>
        </div>
      )}

      {/* Personalized Feedback */}
      <div className="card">
        <h3 className="card-title">Personalized Formative Feedback</h3>
        <p style={{ fontSize: '14px', lineHeight: 1.6, whiteSpace: 'pre-line', color: 'var(--color-text-primary)' }}>
          {feedbackText}
        </p>
      </div>

      {/* Action Footer */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <button
          type="button"
          className="btn-secondary"
          onClick={() => onNavigate('learn')}
        >
          Review Lesson
        </button>
        <button
          type="button"
          className="btn-primary"
          style={{ width: 'auto' }}
          onClick={() => onNavigate('progress')}
        >
          View Updated Progress & Roadmap →
        </button>
      </div>
    </div>
  );
}
