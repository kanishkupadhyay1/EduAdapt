import React from 'react';

export default function StudentProfile({ profile, currentTopic }) {
  // If backend returns profile data, use it; otherwise fallback cleanly
  const studentId = profile?.student_id || 'S001';
  const topic = currentTopic || profile?.current_topic || 'Pointers';
  const mastery = profile?.mastery !== undefined 
    ? `${Math.round(profile.mastery * 100)}%` 
    : '100%';
  const accuracy = profile?.accuracy !== undefined 
    ? `${Math.round(profile.accuracy * 100)}%` 
    : '100%';
  const pace = profile?.learning_pace || 'Fast';
  const difficulty = profile?.recommended_difficulty || 'Advanced';
  const predictedMastery = profile?.predicted_mastery_level || 'High';
  const learningStyle = profile?.learning_style || 'Balanced';

  return (
    <section className="panel" aria-labelledby="profile-heading">
      <div className="panel-header">
        <h2 id="profile-heading" className="panel-title">Student Profile</h2>
        <span className="panel-badge badge-blue">Learning Twin</span>
      </div>
      <div className="panel-body">
        <table className="kv-table">
          <tbody>
            <tr>
              <td className="kv-label">Student ID</td>
              <td className="kv-value">{studentId}</td>
            </tr>
            <tr>
              <td className="kv-label">Topic</td>
              <td className="kv-value">{topic}</td>
            </tr>
            <tr>
              <td className="kv-label">Mastery</td>
              <td className="kv-value">
                <span className="badge-green">{mastery}</span>
              </td>
            </tr>
            <tr>
              <td className="kv-label">Accuracy</td>
              <td className="kv-value">
                <span className="badge-green">{accuracy}</span>
              </td>
            </tr>
            <tr>
              <td className="kv-label">Learning Pace</td>
              <td className="kv-value">{pace}</td>
            </tr>
            <tr>
              <td className="kv-label">Difficulty</td>
              <td className="kv-value">{difficulty}</td>
            </tr>
            <tr>
              <td className="kv-label">Predicted Level</td>
              <td className="kv-value">
                <span className="badge-blue">{predictedMastery}</span>
              </td>
            </tr>
            <tr>
              <td className="kv-label">Learning Style</td>
              <td className="kv-value">{learningStyle}</td>
            </tr>
          </tbody>
        </table>
      </div>
    </section>
  );
}
