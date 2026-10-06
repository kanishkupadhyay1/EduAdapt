import React from 'react';

const DEFAULT_ROADMAP = [
  { num: '01', title: 'Basics & Variables', status: 'Completed' },
  { num: '02', title: 'Pointers Fundamentals', status: 'Current' },
  { num: '03', title: 'Pointer Arithmetic & Types', status: 'Next' },
  { num: '04', title: 'Dynamic Memory Allocation', status: 'Upcoming' },
  { num: '05', title: 'Structures & Pointers', status: 'Upcoming' },
  { num: '06', title: 'Double Pointers & Function Arguments', status: 'Upcoming' },
  { num: '07', title: 'Advanced Problem Solving', status: 'Upcoming' },
];

export default function Progress({
  student,
  learningState,
  currentTopic = 'Pointers',
  roadmapData,
  onNavigate,
}) {
  const current = learningState?.updated_state || learningState?.simulated_twin || student;
  const mastery = current?.mastery !== undefined ? `${Math.round(current.mastery * 100)}%` : '100%';
  const accuracy = current?.accuracy !== undefined ? `${Math.round(current.accuracy * 100)}%` : '100%';
  const pace = current?.learning_pace || 'Fast';
  const difficulty = current?.recommended_difficulty || 'Advanced';
  const predictedMastery = current?.predicted_mastery_level || student?.predicted_mastery_level || 'High';

  return (
    <div className="progress-page">
      <header className="page-header">
        <h2 className="page-title">Your Progress</h2>
        <p className="page-subtitle">Track your mastery level, Learning Twin updates, and milestone progression.</p>
      </header>

      {/* Current Learning State */}
      <div className="card">
        <h3 className="card-title">
          <span>Current Learning State</span>
          <span className="badge-green">Learning Twin Recomputed</span>
        </h3>
        <div className="stats-grid">
          <div className="stat-box">
            <div className="stat-label">Active Topic</div>
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
          <div className="stat-box">
            <div className="stat-label">Current Difficulty</div>
            <div className="stat-value" style={{ fontSize: '18px' }}>{difficulty}</div>
          </div>
          <div className="stat-box">
            <div className="stat-label">Predicted Mastery</div>
            <div className="stat-value" style={{ color: 'var(--color-blue)' }}>{predictedMastery}</div>
          </div>
        </div>

        {learningState?.status_message && (
          <div style={{ marginTop: '16px', fontSize: '12px', color: 'var(--color-text-secondary)', borderTop: '1px solid var(--color-border)', paddingTop: '10px' }}>
            {learningState.status_message}
          </div>
        )}
      </div>

      {/* Learning Roadmap */}
      <div className="card">
        <h3 className="card-title">
          <span>Learning Roadmap</span>
          <span className="badge-blue">Curriculum Milestones</span>
        </h3>
        <p style={{ fontSize: '14px', color: 'var(--color-text-secondary)', marginBottom: '16px' }}>
          Your personalized pathway towards PPS course competency:
        </p>

        <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
          {DEFAULT_ROADMAP.map((step, idx) => {
            const isCurrent = step.status === 'Current';
            const isCompleted = step.status === 'Completed';

            let badgeClass = 'badge-gray';
            if (isCompleted) badgeClass = 'badge-green';
            if (isCurrent) badgeClass = 'badge-blue';

            return (
              <div
                key={idx}
                className={`roadmap-step ${isCurrent ? 'active' : ''}`}
                style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}
              >
                <div style={{ display: 'flex', alignItems: 'center', gap: '14px' }}>
                  <span className="step-num">{step.num}</span>
                  <div>
                    <div style={{ fontSize: '14px', fontWeight: isCurrent ? 700 : 500 }}>
                      {step.title}
                    </div>
                  </div>
                </div>
                <div>
                  <span className={badgeClass}>{step.status}</span>
                </div>
              </div>
            );
          })}
        </div>
      </div>

      {/* Next Step Action */}
      <div style={{ display: 'flex', justifyContent: 'flex-end', marginTop: '16px' }}>
        <button
          type="button"
          className="btn-primary"
          style={{ width: 'auto' }}
          onClick={() => onNavigate('learn')}
        >
          Continue Learning Topic →
        </button>
      </div>
    </div>
  );
}
