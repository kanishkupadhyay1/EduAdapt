import React, { useState } from 'react';

export default function AccessibilityPanel({ accessibility }) {
  const [showSummary, setShowSummary] = useState(false);
  const screenReaderSummary = accessibility?.screen_reader_summary;
  const modality = accessibility?.modality || 'screen_reader_and_text_optimized';

  return (
    <section className="panel" aria-labelledby="accessibility-heading">
      <div className="panel-header">
        <h2 id="accessibility-heading" className="panel-title">Accessibility</h2>
        <span className="badge-gray">WCAG Accessible</span>
      </div>
      <div className="panel-body">
        <div className="accessibility-features">
          <div className="accessibility-row">
            <span>Speech Input</span>
            <span className="badge-gray">Available / Optional</span>
          </div>

          <div className="accessibility-row">
            <span>Text-to-Speech</span>
            <span className="badge-gray">Available / Optional</span>
          </div>

          <div className="accessibility-row">
            <span>Screen Reader View</span>
            <span className="badge-green">Available</span>
          </div>
        </div>

        {screenReaderSummary && (
          <div style={{ marginTop: '14px', borderTop: '1px solid var(--color-border)', paddingTop: '10px' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '8px' }}>
              <span style={{ fontSize: '12px', fontWeight: 600, color: 'var(--color-text-secondary)' }}>
                Screen Reader Transcript
              </span>
              <button
                type="button"
                className="btn-secondary"
                onClick={() => setShowSummary(!showSummary)}
              >
                {showSummary ? 'Hide Transcript' : 'View Transcript'}
              </button>
            </div>

            {showSummary && (
              <div style={{ fontSize: '13px', lineHeight: 1.5, backgroundColor: 'var(--color-surface-subtle)', padding: '10px', border: '1px solid var(--color-border)', borderRadius: 'var(--radius-sm)' }}>
                {screenReaderSummary}
              </div>
            )}
          </div>
        )}

        <div style={{ marginTop: '10px', fontSize: '11px', color: 'var(--color-text-muted)' }}>
          Active Formatter: {modality}
        </div>
      </div>
    </section>
  );
}
