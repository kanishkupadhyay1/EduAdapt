import React from 'react';

export default function Home({
  student,
  currentTopic,
  onNavigate,
  recentActivity,
}) {
  const studentId = student?.student_id || 'S001';
  const hasHistory = Boolean(recentActivity || (student?.tests_completed && student.tests_completed > 0));
  const mastery = hasHistory && student?.mastery !== undefined ? `${Math.round(student.mastery * 100)}%` : '0%';
  const accuracy = hasHistory && student?.accuracy !== undefined ? `${Math.round(student.accuracy * 100)}%` : '0%';
  const pace = hasHistory ? (student?.learning_pace || 'Moderate') : 'Unassessed';
  const difficulty = hasHistory ? (student?.recommended_difficulty || 'Beginner') : 'Beginner';

  return (
    <div className="home-page">
      <header className="page-header">
        <h2 className="page-title">{hasHistory ? `Welcome back, ${studentId}.` : `Welcome to EduAdapt, ${studentId}.`}</h2>
        <p className="page-subtitle">
          {hasHistory
            ? 'Continue your personalized learning path in Programming for Problem Solving.'
            : 'Start from baseline 0: learn concepts, practice questions, and watch your Learning Twin adapt.'}
        </p>
      </header>

      {/* Prominent Continue Learning Card */}
      <div className="card" style={{ borderColor: 'var(--color-blue-border)', backgroundColor: 'var(--color-blue-light)' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', flexWrap: 'wrap', gap: '16px' }}>
          <div>
            <span className="badge-blue" style={{ marginBottom: '8px' }}>Active Curriculum Topic</span>
            <h3 style={{ fontSize: '22px', fontWeight: 700, margin: '6px 0 10px', color: 'var(--color-text-primary)' }}>
              {currentTopic}
            </h3>
            <div style={{ display: 'flex', gap: '12px', fontSize: '13px', color: 'var(--color-text-secondary)' }}>
              <span>Difficulty: <strong>{difficulty}</strong></span>
              <span>•</span>
              <span>Mastery: <strong style={{ color: hasHistory ? 'var(--color-green)' : 'var(--color-text-secondary)' }}>{mastery}</strong></span>
              <span>•</span>
              <span>Pace: <strong>{pace}</strong></span>
            </div>
          </div>
          <div>
            <button
              type="button"
              className="btn-primary"
              onClick={() => onNavigate('learn')}
            >
              Start Learning →
            </button>
          </div>
        </div>
      </div>

      {/* Your Learning Progress */}
      <div className="card">
        <h3 className="card-title">
          <span>Your Learning Progress</span>
          <span className="card-title-sub">{hasHistory ? 'Verified Student Twin State' : 'Initial Baseline (0 Assessments)'}</span>
        </h3>
        <div className="stats-grid">
          <div className="stat-box">
            <div className="stat-label">Current Topic</div>
            <div className="stat-value" style={{ fontSize: '18px' }}>{currentTopic}</div>
          </div>
          <div className="stat-box">
            <div className="stat-label">Mastery</div>
            <div className="stat-value" style={{ color: hasHistory ? 'var(--color-green)' : 'var(--color-text-secondary)' }}>{mastery}</div>
          </div>
          <div className="stat-box">
            <div className="stat-label">Accuracy</div>
            <div className="stat-value" style={{ color: hasHistory ? 'var(--color-green)' : 'var(--color-text-secondary)' }}>{accuracy}</div>
          </div>
          <div className="stat-box">
            <div className="stat-label">Learning Pace</div>
            <div className="stat-value" style={{ fontSize: '18px' }}>{pace}</div>
          </div>
        </div>
      </div>

      {/* Recommended Next */}
      <div className="card">
        <h3 className="card-title">
          <span>Recommended Next</span>
          <span className="badge-gray">Curriculum Target</span>
        </h3>
        <p style={{ fontSize: '14px', color: 'var(--color-text-secondary)', marginBottom: '14px' }}>
          Target competency for <strong>{currentTopic}</strong>:
        </p>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '14px 18px', border: '1px solid var(--color-border)', borderRadius: 'var(--radius-sm)', backgroundColor: 'var(--color-surface-subtle)' }}>
          <div>
            <div style={{ fontSize: '15px', fontWeight: 700 }}>{currentTopic} Fundamentals & Implementation</div>
            <div style={{ fontSize: '12px', color: 'var(--color-text-secondary)', marginTop: '2px' }}>
              PPS Course Curriculum • Interactive GenAI & RAG Guided Scaffolding
            </div>
          </div>
          <button
            type="button"
            className="btn-secondary"
            onClick={() => onNavigate('learn')}
          >
            Start →
          </button>
        </div>
      </div>

      {/* Recent Activity */}
      <div className="card">
        <h3 className="card-title">Recent Activity</h3>
        {recentActivity ? (
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '12px 14px', border: '1px solid var(--color-border)', borderRadius: 'var(--radius-sm)' }}>
            <div>
              <div style={{ fontSize: '14px', fontWeight: 600 }}>{currentTopic} Assessment</div>
              <div style={{ fontSize: '12px', color: 'var(--color-text-secondary)' }}>
                Completed • Evaluated by PPS Assessment System
              </div>
            </div>
            <div style={{ textAlign: 'right' }}>
              <span className={recentActivity.score >= 60 ? 'badge-green' : 'badge-red'}>
                {recentActivity.score} / 100
              </span>
            </div>
          </div>
        ) : (
          <div style={{ padding: '16px', color: 'var(--color-text-secondary)', fontSize: '13px', backgroundColor: 'var(--color-surface-subtle)', borderRadius: 'var(--radius-sm)', textAlign: 'center' }}>
            No assessments completed yet. Start by generating a lesson in <strong>Learn</strong> or answering questions in <strong>Practice</strong> to initialize your Learning Twin!
          </div>
        )}
      </div>
    </div>
  );
}
