import React from 'react';

const NAV_ITEMS = [
  { id: 'home', label: 'Home', symbol: '•' },
  { id: 'learn', label: 'Learn', symbol: '→' },
  { id: 'tutor', label: 'AI Tutor', symbol: '?' },
  { id: 'practice', label: 'Practice', symbol: '+' },
  { id: 'tests', label: 'Tests', symbol: '✓' },
  { id: 'progress', label: 'Progress', symbol: '▲' },
];

export default function Sidebar({ activePage, onNavigate, studentId = 'S001' }) {
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
        <div className="student-badge-card">
          <div className="student-badge-label">Active Student</div>
          <div className="student-badge-id">{studentId}</div>
        </div>
        <div style={{ fontSize: '11px', color: 'var(--color-text-muted)' }}>
          PPS Course • Non-Agentic GenAI
        </div>
      </div>
    </aside>
  );
}
