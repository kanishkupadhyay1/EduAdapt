import React from 'react';

export default function VerificationPanel({ verification }) {
  const status = verification?.overall_status || 'VERIFIED_SAFE';
  const matchedConcepts = verification?.matched_curriculum_terms_count ?? 'Not available';
  const groundingIndicator = verification?.grounding_ratio !== undefined
    ? Number(verification.grounding_ratio).toFixed(3)
    : 'Not available';
  const codeLines = verification?.extracted_code_lines ?? 0;
  const executionStatus = verification?.code_execution || 'NOT EXECUTED';
  const safetyStatus = verification?.safety_status || 'NOT_EXECUTED_UNTRUSTED';

  const isVerifiedSafe = status === 'VERIFIED_SAFE' || status === 'VERIFIED';

  return (
    <section className="panel" aria-labelledby="verification-heading">
      <div className="panel-header">
        <h2 id="verification-heading" className="panel-title">Verification</h2>
        <span className={isVerifiedSafe ? 'badge-green' : 'badge-red'}>
          {isVerifiedSafe ? 'VERIFIED SAFE' : status}
        </span>
      </div>
      <div className="panel-body">
        <div className="verification-grid">
          <div className="verification-card">
            <div className="verification-card-label">Curriculum Concepts Matched</div>
            <div className="verification-card-val">{matchedConcepts}</div>
          </div>

          <div className="verification-card">
            <div className="verification-card-label">Grounding Indicator</div>
            <div className="verification-card-val">{groundingIndicator}</div>
          </div>

          <div className="verification-card">
            <div className="verification-card-label">Generated C Code</div>
            <div className="verification-card-val">{codeLines} lines</div>
          </div>

          <div className="verification-card">
            <div className="verification-card-label">Execution Status</div>
            <div className="verification-card-val" style={{ fontSize: '13px' }}>
              {executionStatus}
            </div>
          </div>
        </div>

        <div style={{ marginTop: '14px', fontSize: '12px', color: 'var(--color-text-secondary)', borderTop: '1px solid var(--color-border)', paddingTop: '10px' }}>
          <strong>Safety Status:</strong> {safetyStatus}
        </div>
      </div>
    </section>
  );
}
