import React, { useState } from 'react';

export default function AssessmentPanel({ assessment }) {
  const [showDetails, setShowDetails] = useState(false);

  const score = assessment?.score !== undefined ? assessment.score : 95;
  const accuracy = assessment?.accuracy !== undefined 
    ? `${Math.round(assessment.accuracy * 100)}%` 
    : '100%';
  const attempts = assessment?.attempts ?? 1;
  const time = assessment?.time_taken_seconds !== undefined
    ? `${assessment.time_taken_seconds} sec`
    : '25 sec';

  const question = assessment?.question;
  const options = assessment?.options || [];
  const correctOption = assessment?.correct_option;
  const explanation = assessment?.explanation;

  return (
    <section className="panel" aria-labelledby="assessment-heading">
      <div className="panel-header">
        <h2 id="assessment-heading" className="panel-title">Assessment</h2>
        <span className="badge-green">Completed</span>
      </div>
      <div className="panel-body">
        <div style={{ marginBottom: '14px' }}>
          <table className="kv-table">
            <tbody>
              <tr>
                <td className="kv-label">Score</td>
                <td className="kv-value">
                  <span className="badge-green">{score} / 100</span>
                </td>
              </tr>
              <tr>
                <td className="kv-label">Accuracy</td>
                <td className="kv-value">
                  <span className="badge-green">{accuracy}</span>
                </td>
              </tr>
              <tr>
                <td className="kv-label">Attempts</td>
                <td className="kv-value">{attempts}</td>
              </tr>
              <tr>
                <td className="kv-label">Time</td>
                <td className="kv-value">{time}</td>
              </tr>
            </tbody>
          </table>
        </div>

        {question && (
          <div>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '8px' }}>
              <span style={{ fontSize: '13px', fontWeight: 600 }}>Post-learning Question</span>
              <button
                type="button"
                className="btn-secondary"
                onClick={() => setShowDetails(!showDetails)}
              >
                {showDetails ? 'Hide Question' : 'View Question'}
              </button>
            </div>

            {showDetails && (
              <div className="assessment-question-box">
                <div className="question-text">{question}</div>
                {options.length > 0 && (
                  <ul className="options-list">
                    {options.map((opt, idx) => {
                      const isCorrect = correctOption && opt.startsWith(correctOption);
                      return (
                        <li key={idx} className={`option-item ${isCorrect ? 'correct' : ''}`}>
                          {opt} {isCorrect ? ' ✓' : ''}
                        </li>
                      );
                    })}
                  </ul>
                )}
                {explanation && (
                  <div style={{ marginTop: '10px', fontSize: '12px', color: 'var(--color-text-secondary)', borderTop: '1px solid var(--color-border)', paddingTop: '6px' }}>
                    <strong>Explanation:</strong> {explanation}
                  </div>
                )}
              </div>
            )}
          </div>
        )}
      </div>
    </section>
  );
}
