import React from 'react';

export default function Home({
  student,
  currentTopic,
  onNavigate,
  recentActivity,
}) {
  const studentId = student?.student_id || 'S001';
  const mastery = student?.mastery !== undefined ? `${Math.round(student.mastery * 100)}%` : '100%';
  const accuracy = student?.accuracy !== undefined ? `${Math.round(student.accuracy * 100)}%` : '100%';
  const pace = student?.learning_pace || 'Fast';
  const difficulty = student?.recommended_difficulty || 'Advanced';

  return (
    <div className="home-page">
      <header className="page-header">
        <h2 className="page-title">Good to see you, {studentId}.</h2>
        <p className="page-subtitle">Continue where you left off in Programming for Problem Solving.</p>
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
              <span>Mastery: <strong style={{ color: 'var(--color-green)' }}>{mastery}</strong></span>
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
              Continue Learning →
            </button>
          </div>
        </div>
      </div>

      {/* Your Learning Progress */}
      <div className="card">
        <h3 className="card-title">
          <span>Your Learning Progress</span>
          <span className="card-title-sub">Verified Student State</span>
        </h3>
        <div className="stats-grid">
          <div className="stat-box">
            <div className="stat-label">Current Topic</div>
            <div className="stat-value" style={{ fontSize: '18px' }}>{currentTopic}</div>
          </div>
          <div className="stat-box">
            <div className="stat-label">Mastery</div>
            <div className="stat-value" style={{ color: 'var(--color-green)' }}>{mastery}</div>
          </div>
          <div className="stat-box">
            <div className="stat-label">Accuracy</div>
            <div className="stat-value" style={{ color: 'var(--color-green)' }}>{accuracy}</div>
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
          <span className="badge-gray">Roadmap Milestone</span>
        </h3>
        <p style={{ fontSize: '14px', color: 'var(--color-text-secondary)', marginBottom: '14px' }}>
          Based on your current mastery in <strong>{currentTopic}</strong>, your next target competency is:
        </p>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '14px 18px', border: '1px solid var(--color-border)', borderRadius: 'var(--radius-sm)', backgroundColor: 'var(--color-surface-subtle)' }}>
          <div>
            <div style={{ fontSize: '15px', fontWeight: 700 }}>Pointer Arithmetic & Dynamic Allocation</div>
            <div style={{ fontSize: '12px', color: 'var(--color-text-secondary)', marginTop: '2px' }}>
              Unit 2 • Limitations of Pointer Arithmetic & Void Pointers
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
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '12px 14px', border: '1px solid var(--color-border)', borderRadius: 'var(--radius-sm)' }}>
          <div>
            <div style={{ fontSize: '14px', fontWeight: 600 }}>{currentTopic} Assessment</div>
            <div style={{ fontSize: '12px', color: 'var(--color-text-secondary)' }}>
              Completed • Evaluated by PPS Assessment System
            </div>
          </div>
          <div style={{ textAlign: 'right' }}>
            <span className="badge-green">{recentActivity?.score || 95} / 100</span>
          </div>
        </div>
      </div>
    </div>
  );
}
