import React from 'react';

export default function LearningState({ learningState, initialStudent }) {
  // Use updated_state or simulated_twin if present, otherwise initial_state
  const state = learningState?.updated_state || learningState?.simulated_twin || learningState?.initial_state || initialStudent;

  const mastery = state?.mastery !== undefined
    ? `${Math.round(state.mastery * 100)}%`
    : 'Not available';
  const pace = state?.learning_pace || 'Not available';
  const difficulty = state?.recommended_difficulty || 'Not available';
  const predictedMastery = state?.predicted_mastery_level || initialStudent?.predicted_mastery_level || 'High';
  const statusMessage = learningState?.status_message;

  return (
    <section className="panel" aria-labelledby="state-heading">
      <div className="panel-header">
        <h2 id="state-heading" className="panel-title">Updated Learning State</h2>
        <span className="badge-green">Learning Twin Recomputed</span>
      </div>
      <div className="panel-body">
        <table className="kv-table">
          <tbody>
            <tr>
              <td className="kv-label">Mastery</td>
              <td className="kv-value">
                <span className="badge-green">{mastery}</span>
              </td>
            </tr>
            <tr>
              <td className="kv-label">Learning Pace</td>
              <td className="kv-value">{pace}</td>
            </tr>
            <tr>
              <td className="kv-label">Recommended Difficulty</td>
              <td className="kv-value">{difficulty}</td>
            </tr>
            <tr>
              <td className="kv-label">Predicted Mastery Level</td>
              <td className="kv-value">
                <span className="badge-blue">{predictedMastery}</span>
              </td>
            </tr>
          </tbody>
        </table>

        {statusMessage && (
          <div style={{ marginTop: '12px', fontSize: '12px', color: 'var(--color-text-secondary)', borderTop: '1px solid var(--color-border)', paddingTop: '8px' }}>
            {statusMessage}
          </div>
        )}
      </div>
    </section>
  );
}
