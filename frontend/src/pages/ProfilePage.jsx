import React, { useEffect, useState } from 'react';
import { fetchStudentsList, fetchStudentProfile } from '../api/learningApi';

export default function ProfilePage({
  currentStudentId = 'S001',
  studentProfile,
  onSelectStudent,
  onNavigate,
}) {
  const [students, setStudents] = useState([]);
  const [isLoading, setIsLoading] = useState(false);
  const [selectedDetails, setSelectedDetails] = useState(studentProfile);

  useEffect(() => {
    fetchStudentsList()
      .then((data) => {
        if (data && data.students) {
          setStudents(data.students);
        }
      })
      .catch((err) => console.warn('Failed to load students list:', err));
  }, []);

  const handleStudentClick = async (sId) => {
    setIsLoading(true);
    try {
      const prof = await fetchStudentProfile(sId);
      setSelectedDetails(prof);
      if (onSelectStudent) {
        onSelectStudent(sId, prof);
      }
    } catch (err) {
      alert('Unable to load student profile: ' + err.message);
    } finally {
      setIsLoading(false);
    }
  };

  const mastery = selectedDetails?.mastery !== undefined
    ? `${Math.round(selectedDetails.mastery * 100)}%`
    : '0%';
  const accuracy = selectedDetails?.accuracy !== undefined
    ? `${Math.round(selectedDetails.accuracy * 100)}%`
    : '0%';
  const pace = selectedDetails?.learning_pace || 'Moderate';
  const difficulty = selectedDetails?.recommended_difficulty || 'Beginner';
  const predictedMastery = selectedDetails?.predicted_mastery_level || 'New Learner';

  return (
    <div className="profile-page">
      <header className="page-header">
        <h2 className="page-title">Student Profile & Learning Twin</h2>
        <p className="page-subtitle">
          Real student cognitive models driving deterministic GenAI personalization across 15 pedagogical dimensions.
        </p>
      </header>

      {/* Panel Demonstration Student Switcher */}
      <div className="card" style={{ borderColor: 'var(--color-blue-border)', backgroundColor: 'var(--color-blue-light)', marginBottom: '24px' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '12px' }}>
          <div>
            <span className="badge-blue">Panel Demonstration Control</span>
            <h3 style={{ fontSize: '16px', fontWeight: 700, margin: '6px 0 2px' }}>
              Select Active Real Student Profile
            </h3>
            <p style={{ fontSize: '13px', color: 'var(--color-text-secondary)', margin: 0 }}>
              Switching students instantly reconfigures the non-agentic GenAI pipeline for different mastery tiers.
            </p>
          </div>
        </div>

        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(260px, 1fr))', gap: '10px' }}>
          {students.map((st) => {
            const isSelected = st.student_id === currentStudentId;
            const stMastery = Math.round((st.mastery || 0) * 100);
            return (
              <button
                key={st.student_id}
                type="button"
                className={`card ${isSelected ? 'active-student-card' : ''}`}
                style={{
                  margin: 0,
                  padding: '12px 16px',
                  textAlign: 'left',
                  cursor: 'pointer',
                  border: isSelected ? '2px solid var(--color-blue)' : '1px solid var(--color-border)',
                  backgroundColor: isSelected ? '#ffffff' : '#fafafa',
                }}
                onClick={() => handleStudentClick(st.student_id)}
                disabled={isLoading}
              >
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '4px' }}>
                  <strong style={{ fontSize: '15px' }}>{st.student_id}</strong>
                  <span className={stMastery >= 70 ? 'badge-green' : stMastery >= 40 ? 'badge-blue' : 'badge-yellow'}>
                    {st.recommended_difficulty || (stMastery >= 70 ? 'Advanced' : 'Beginner')}
                  </span>
                </div>
                <div style={{ fontSize: '12px', color: 'var(--color-text-secondary)' }}>
                  Mastery: <strong>{stMastery}%</strong> • Pace: <strong>{st.learning_pace || 'Moderate'}</strong> • Tests: <strong>{st.tests_completed || 0}</strong>
                </div>
              </button>
            );
          })}
        </div>
      </div>

      {/* Selected Student Learning Twin Telemetry */}
      <div className="card">
        <h3 className="card-title">
          <span>Active Learning Twin Telemetry</span>
          <span className="badge-green">XGBoost & Dynamic State</span>
        </h3>

        <div className="stats-grid" style={{ marginBottom: '20px' }}>
          <div className="stat-box">
            <div className="stat-label">Student ID</div>
            <div className="stat-value" style={{ fontSize: '18px' }}>{selectedDetails?.student_id || currentStudentId}</div>
          </div>
          <div className="stat-box">
            <div className="stat-label">Cognitive Mastery</div>
            <div className="stat-value" style={{ color: 'var(--color-green)' }}>{mastery}</div>
          </div>
          <div className="stat-box">
            <div className="stat-label">Assessment Accuracy</div>
            <div className="stat-value" style={{ color: 'var(--color-green)' }}>{accuracy}</div>
          </div>
          <div className="stat-box">
            <div className="stat-label">Assessed Pace</div>
            <div className="stat-value" style={{ fontSize: '18px' }}>{pace}</div>
          </div>
          <div className="stat-box">
            <div className="stat-label">Target Difficulty</div>
            <div className="stat-value" style={{ fontSize: '18px' }}>{difficulty}</div>
          </div>
          <div className="stat-box">
            <div className="stat-label">Predicted Level</div>
            <div className="stat-value" style={{ color: 'var(--color-blue)' }}>{predictedMastery}</div>
          </div>
        </div>

        {/* Detailed State Attributes */}
        <table className="kv-table">
          <tbody>
            <tr>
              <td className="kv-label">Learning Style</td>
              <td className="kv-value">{selectedDetails?.learning_style || 'Balanced'}</td>
            </tr>
            <tr>
              <td className="kv-label">Current Curriculum Topic</td>
              <td className="kv-value">{selectedDetails?.current_topic || 'Pointers'}</td>
            </tr>
            <tr>
              <td className="kv-label">Tests Completed in Dataset</td>
              <td className="kv-value">{selectedDetails?.tests_completed || 0}</td>
            </tr>
            <tr>
              <td className="kv-label">Common Misconceptions</td>
              <td className="kv-value">
                {Array.isArray(selectedDetails?.common_misconceptions) && selectedDetails.common_misconceptions.length > 0
                  ? selectedDetails.common_misconceptions.join(', ')
                  : 'None logged yet for active topic'}
              </td>
            </tr>
            <tr>
              <td className="kv-label">Deterministic Personalization Strategy</td>
              <td className="kv-value">
                {mastery.startsWith('100') || difficulty === 'Advanced'
                  ? 'High Mastery Track: Edge cases, memory optimization, pointer arithmetic pitfalls, concise high-density instruction'
                  : 'Beginner Scaffolding Track: Real-world analogies, step-by-step memory diagrams, defensive code checks, guided hints'}
              </td>
            </tr>
          </tbody>
        </table>
      </div>

      {/* Action to test live generation */}
      <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '10px', marginTop: '20px' }}>
        <button
          type="button"
          className="btn-secondary"
          onClick={() => onNavigate('practice')}
        >
          Practice with this Student Profile →
        </button>
        <button
          type="button"
          className="btn-primary"
          onClick={() => onNavigate('learn')}
        >
          Generate Personalized Lesson for {selectedDetails?.student_id || currentStudentId} →
        </button>
      </div>
    </div>
  );
}
