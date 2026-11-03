import React from 'react';

/**
 * Parses roadmap content into structured milestones.
 */
function parseRoadmapSteps(rawContent) {
  if (!rawContent) return [];
  const lines = rawContent.split('\n');
  const steps = [];
  let counter = 1;

  for (const line of lines) {
    const trimmed = line.trim();
    if (!trimmed || trimmed.startsWith('#')) continue;
    const match = trimmed.match(/^(?:(?:\d+\.|\*|-|•)\s*)?(.*)$/);
    const content = match ? match[1].trim() : trimmed;
    if (content.length > 3) {
      steps.push({
        num: String(counter).padStart(2, '0'),
        title: content,
        status: counter === 1 ? 'Completed' : counter === 2 ? 'Current' : 'Upcoming',
      });
      counter++;
    }
  }
  return steps;
}

export default function Progress({
  student,
  learningState,
  currentTopic = 'Pointers',
  roadmapData,
  onNavigate,
}) {
  const hasHistory = Boolean(learningState?.updated_state || (student?.tests_completed && student.tests_completed > 0));
  const current = learningState?.updated_state || learningState?.simulated_twin || student;
  const mastery = hasHistory && current?.mastery !== undefined ? `${Math.round(current.mastery * 100)}%` : '0%';
  const accuracy = hasHistory && current?.accuracy !== undefined ? `${Math.round(current.accuracy * 100)}%` : '0%';
  const pace = hasHistory ? (current?.learning_pace || 'Moderate') : 'Unassessed';
  const difficulty = hasHistory ? (current?.recommended_difficulty || 'Beginner') : 'Beginner';
  const predictedMastery = hasHistory ? (current?.predicted_mastery_level || 'Developing') : 'New Learner';

  const roadmapSteps = parseRoadmapSteps(roadmapData?.roadmap_content);

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
          <span className={hasHistory ? 'badge-green' : 'badge-gray'}>
            {hasHistory ? 'Learning Twin Recomputed' : 'Initial Baseline State'}
          </span>
        </h3>
        <div className="stats-grid">
          <div className="stat-box">
            <div className="stat-label">Active Topic</div>
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
          <div className="stat-box">
            <div className="stat-label">Current Difficulty</div>
            <div className="stat-value" style={{ fontSize: '18px' }}>{difficulty}</div>
          </div>
          <div className="stat-box">
            <div className="stat-label">Predicted Mastery</div>
            <div className="stat-value" style={{ color: hasHistory ? 'var(--color-blue)' : 'var(--color-text-secondary)' }}>{predictedMastery}</div>
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
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px' }}>
          <div>
            <h3 className="card-title" style={{ margin: 0 }}>
              <span>Adaptive Milestone Roadmap</span>
              <span className="badge-blue" style={{ marginLeft: '10px' }}>Curriculum Milestones</span>
            </h3>
          </div>
          <button
            type="button"
            className="btn-pill"
            onClick={() => onNavigate('roadmap')}
          >
            Open Roadmap Explorer ☵
          </button>
        </div>

        {roadmapSteps.length > 0 ? (
          <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
            {roadmapSteps.map((step, idx) => {
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
        ) : (
          <div style={{ padding: '20px 0', color: 'var(--color-text-secondary)', fontSize: '13px' }}>
            <p style={{ marginBottom: '12px' }}>
              No custom roadmap has been generated for <strong>{currentTopic}</strong> in the current session.
            </p>
            <button
              type="button"
              className="btn-secondary"
              onClick={() => onNavigate('roadmap')}
            >
              Generate Personalized Roadmap Now ☵
            </button>
          </div>
        )}
      </div>

      {/* Next Step Action */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginTop: '16px' }}>
        <button
          type="button"
          className="btn-secondary"
          onClick={() => onNavigate('profile')}
        >
          View Full Student Twin Profile 👤
        </button>
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
