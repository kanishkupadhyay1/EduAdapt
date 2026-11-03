import React from 'react';

export default function Results({
  testResult,
  currentTopic = 'Pointers',
  onNavigate,
  onTopicChange,
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
            Complete a formal assessment in the Tests tab to view your score, performance breakdown, and roadmap progression.
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

  const score = testResult.score !== undefined ? testResult.score : 0;
  const isCorrect = testResult.is_correct ?? testResult.mastery_achieved ?? (score >= 60);
  const accuracy = testResult.accuracy !== undefined
    ? `${Math.round(testResult.accuracy * 100)}%`
    : `${score}%`;
  const timeTaken = testResult.time_taken_seconds || testResult.timeTaken || 0;
  const feedbackText = testResult.feedback || 'Assessment submitted and evaluated by EduAdapt Learning Twin.';
  const questions = testResult.results || testResult.questions || [];
  const weakConcepts = testResult.weak_concepts || [];
  const nextTopic = testResult.next_topic;

  const handleContinueNextTopic = () => {
    if (nextTopic && onTopicChange) {
      onTopicChange(nextTopic);
    }
    onNavigate('learn');
  };

  return (
    <div className="results-page">
      <header className="page-header">
        <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
          <span className={isCorrect ? 'badge-green' : 'badge-red'}>
            {isCorrect ? 'Mastery Verified' : 'Needs Practice'}
          </span>
          <span style={{ fontSize: '13px', color: 'var(--color-text-secondary)' }}>Topic: {currentTopic}</span>
        </div>
        <h2 className="page-title" style={{ marginTop: '8px' }}>Assessment Results</h2>
        <p className="page-subtitle">
          Authoritative evaluation by EduAdapt Learning Twin • PPS Diagnostic Assessment
        </p>
      </header>

      {/* Satisfactory Mastery Banner & Automatic Progression */}
      {isCorrect && nextTopic && nextTopic !== currentTopic && (
        <div
          style={{
            backgroundColor: 'var(--color-green-light)',
            border: '1px solid var(--color-green-border)',
            borderRadius: 'var(--radius-sm)',
            padding: '16px 20px',
            marginBottom: '20px',
          }}
          role="region"
          aria-label="Topic Completion and Progression"
        >
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '12px' }}>
            <div>
              <h3 style={{ fontSize: '16px', fontWeight: 700, color: 'var(--color-green)', margin: '0 0 4px 0' }}>
                🎉 Satisfactory Mastery Achieved in {currentTopic}!
              </h3>
              <p style={{ fontSize: '13px', color: 'var(--color-text-primary)', margin: 0 }}>
                Your roadmap has unlocked the next topic: <strong>{nextTopic}</strong>.
              </p>
            </div>
            <button
              type="button"
              className="btn-primary"
              style={{ backgroundColor: 'var(--color-green)', borderColor: 'var(--color-green)', padding: '8px 18px' }}
              onClick={handleContinueNextTopic}
            >
              Continue to {nextTopic} →
            </button>
          </div>
        </div>
      )}

      {/* Insufficient Mastery Remediation Guidance */}
      {!isCorrect && (
        <div
          style={{
            backgroundColor: 'var(--color-surface-subtle)',
            border: '1px solid var(--color-border)',
            borderRadius: 'var(--radius-sm)',
            padding: '16px 20px',
            marginBottom: '20px',
          }}
          role="region"
          aria-label="Targeted Remediation Guidance"
        >
          <h3 style={{ fontSize: '15px', fontWeight: 700, color: 'var(--color-text-primary)', marginBottom: '6px' }}>
            Targeted Revision Recommended for {currentTopic}
          </h3>
          <p style={{ fontSize: '13px', color: 'var(--color-text-secondary)', marginBottom: '12px' }}>
            Satisfactory mastery requires 60% (6/10). Review the weak concepts identified below, or practice further. You are never permanently locked from progressing.
          </p>
          <div style={{ display: 'flex', gap: '10px', flexWrap: 'wrap' }}>
            <button
              type="button"
              className="btn-primary"
              onClick={() => onNavigate('practice')}
            >
              Practice {currentTopic} MCQs →
            </button>
            <button
              type="button"
              className="btn-secondary"
              onClick={() => onNavigate('learn')}
            >
              Review Lesson
            </button>
            {nextTopic && (
              <button
                type="button"
                className="btn-secondary"
                onClick={handleContinueNextTopic}
              >
                Proceed to {nextTopic} Anyway →
              </button>
            )}
          </div>
        </div>
      )}

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
            <div className="stat-label">Total Questions</div>
            <div className="stat-value">{testResult.total_questions || questions.length || 10}</div>
          </div>
          <div className="stat-box">
            <div className="stat-label">Time Taken</div>
            <div className="stat-value">{timeTaken} sec</div>
          </div>
        </div>
      </div>

      {/* Weak Concepts Alert Box */}
      {weakConcepts.length > 0 && (
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
          aria-label="Weak Concepts"
        >
          <strong style={{ display: 'block', marginBottom: '4px' }}>
            ⚠️ Weak Concepts Identified for Focused Revision:
          </strong>
          <span>{weakConcepts.join(' • ')}</span>
        </div>
      )}

      {/* Detailed Question Review */}
      {questions.length > 0 && (
        <div className="card">
          <h3 className="card-title">Detailed Question Review ({questions.length} Questions)</h3>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '14px' }}>
            {questions.map((item, idx) => {
              const qText = item.question || item.question_text || `Question ${idx + 1}`;
              const studentChoice = item.student_answer || item.student_choice || testResult.studentAnswers?.[idx] || 'B';
              const correctChoice = item.correct_answer || item.correct_option || 'B';
              const passed = item.is_correct ?? (studentChoice === correctChoice);
              const concept = item.concept || currentTopic;
              const explanation = item.explanation || '';

              return (
                <div
                  key={idx}
                  style={{
                    border: '1px solid var(--color-border)',
                    borderRadius: 'var(--radius-sm)',
                    padding: '14px',
                    backgroundColor: passed ? 'var(--color-surface)' : 'var(--color-surface-subtle)',
                  }}
                >
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '8px' }}>
                    <span style={{ fontWeight: 700, fontSize: '13px' }}>
                      Question {idx + 1}: {concept}
                    </span>
                    <span className={passed ? 'badge-green' : 'badge-red'}>
                      {passed ? '✓ Correct' : '× Incorrect'}
                    </span>
                  </div>
                  <div style={{ fontSize: '14px', fontWeight: 600, marginBottom: '10px', color: 'var(--color-text-primary)' }}>
                    {qText}
                  </div>
                  <div style={{ fontSize: '13px', display: 'flex', gap: '20px', marginBottom: '8px' }}>
                    <span>Your answer: <strong>{studentChoice}</strong></span>
                    <span>Correct answer: <strong style={{ color: 'var(--color-green)' }}>{correctChoice}</strong></span>
                  </div>
                  {explanation && (
                    <div style={{ fontSize: '12px', color: 'var(--color-text-secondary)', borderTop: '1px solid var(--color-border)', paddingTop: '6px' }}>
                      <strong>Explanation:</strong> {explanation}
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
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '10px' }}>
        <button
          type="button"
          className="btn-secondary"
          onClick={() => onNavigate('learn')}
        >
          Review Lesson
        </button>
        <div style={{ display: 'flex', gap: '10px' }}>
          <button
            type="button"
            className="btn-secondary"
            onClick={() => onNavigate('progress')}
          >
            View Progress & Analytics
          </button>
          <button
            type="button"
            className="btn-primary"
            onClick={() => onNavigate('roadmap')}
          >
            View Updated Roadmap →
          </button>
        </div>
      </div>
    </div>
  );
}
