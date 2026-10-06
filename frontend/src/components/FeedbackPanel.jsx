import React from 'react';

export default function FeedbackPanel({ feedback }) {
  const content = feedback?.feedback || 'No feedback recorded.';
  const problem = feedback?.problem;

  return (
    <section className="panel" aria-labelledby="feedback-heading">
      <div className="panel-header">
        <h2 id="feedback-heading" className="panel-title">Personalized Feedback</h2>
        <span className="badge-blue">GenAI Formative Feedback</span>
      </div>
      <div className="panel-body">
        {problem && (
          <div style={{ fontSize: '13px', fontWeight: 600, marginBottom: '8px', color: 'var(--color-text-secondary)' }}>
            {problem}
          </div>
        )}
        <div style={{ fontSize: '14px', lineHeight: 1.6, whiteSpace: 'pre-line' }}>
          {content}
        </div>
      </div>
    </section>
  );
}
