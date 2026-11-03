import React from 'react';

const NAV_ITEMS = [
  { id: 'home', label: 'Home', symbol: '•' },
  { id: 'learn', label: 'Learn', symbol: '→' },
  { id: 'tutor', label: 'AI Tutor', symbol: '?' },
  { id: 'practice', label: 'Practice', symbol: '+' },
  { id: 'tests', label: 'Tests', symbol: '✓' },
  { id: 'roadmap', label: 'Roadmap', symbol: '☵' },
  { id: 'progress', label: 'Progress', symbol: '▲' },
  { id: 'profile', label: 'Student Profile', symbol: '👤' },
  { id: 'curriculum', label: 'PPS Curriculum', symbol: '📚' },
];

export default function Sidebar({ activePage, onNavigate, studentId = 'S001', onReset }) {
  return (
    <aside className="sidebar">
      <div>
        <div className="brand-section">
          <h1 className="brand-title">EduAdapt</h1>
          <div className="brand-subtitle">Adaptive Learning Platform</div>
        </div>

        <nav aria-label="Main Navigation">
          <ul className="nav-menu">
            {NAV_ITEMS.map((item) => (
              <li key={item.id}>
                <button
                  type="button"
                  className={`nav-item-btn ${activePage === item.id ? 'active' : ''}`}
                  onClick={() => onNavigate(item.id)}
                >
                  <span style={{ fontFamily: 'monospace', width: '16px', textAlign: 'center' }}>
                    {item.symbol}
                  </span>
                  <span>{item.label}</span>
                </button>
              </li>
            ))}
          </ul>
        </nav>
      </div>

      <div className="sidebar-footer">
        <div className="student-badge-card" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <div>
            <div className="student-badge-label">Active Student</div>
            <div className="student-badge-id">{studentId}</div>
          </div>
          {onReset && (
            <button
              type="button"
              className="btn-pill"
              style={{ padding: '2px 8px', fontSize: '11px', color: '#64748b', cursor: 'pointer' }}
              title="Reset session and start from 0"
              onClick={onReset}
            >
              Reset (0)
            </button>
          )}
        </div>
        <div style={{ fontSize: '11px', color: 'var(--color-text-muted)' }}>
          PPS Course • Non-Agentic GenAI
        </div>
      </div>
    </aside>
  );
}
