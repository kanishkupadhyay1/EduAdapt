import React, { useEffect, useState } from 'react';
import { fetchTopicAssessment, submitAssessmentAnswer } from '../api/learningApi';

export default function Practice({
  studentId = 'S001',
  currentTopic = 'Pointers',
  onNavigate,
  onAssessmentCompleted,
}) {
  const [questionData, setQuestionData] = useState(null);
  const [selectedOption, setSelectedOption] = useState('');
  const [submitted, setSubmitted] = useState(false);
  const [result, setResult] = useState(null);
  const [isLoading, setIsLoading] = useState(true);
  const [isSubmitting, setIsSubmitting] = useState(false);

  useEffect(() => {
    let isMounted = true;
    setIsLoading(true);
    fetchTopicAssessment(studentId, currentTopic)
      .then((data) => {
        if (isMounted) {
          setQuestionData(data);
          setSelectedOption('');
          setSubmitted(false);
          setResult(null);
        }
      })
      .catch((err) => {
        console.warn('Practice fetch err:', err);
      })
      .finally(() => {
        if (isMounted) setIsLoading(false);
      });

    return () => {
      isMounted = false;
    };
  }, [studentId, currentTopic]);

  const handleSubmit = async () => {
    if (!selectedOption || isSubmitting) return;

    setIsSubmitting(true);
    const optionLetter = selectedOption.trim().charAt(0);

    try {
      const res = await submitAssessmentAnswer(studentId, currentTopic, optionLetter, 20);
      setResult(res);
      setSubmitted(true);
      if (onAssessmentCompleted) {
        onAssessmentCompleted(res);
      }
    } catch (err) {
      alert('Unable to submit answer: ' + err.message);
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="practice-page">
      <header className="page-header">
        <h2 className="page-title">Practice</h2>
        <p className="page-subtitle">Practice and reinforce concepts in <strong>{currentTopic}</strong> with instant formative feedback.</p>
      </header>

      {isLoading && (
        <div className="card" style={{ textAlign: 'center', padding: '40px', color: 'var(--color-text-secondary)' }}>
          Loading practice question for {currentTopic}...
        </div>
      )}

      {!isLoading && questionData && (
        <div className="card">
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '14px' }}>
            <span className="badge-blue">Recommended Practice</span>
            <span style={{ fontSize: '12px', color: 'var(--color-text-secondary)' }}>
              Curriculum Grounded • Post-learning check
            </span>
          </div>

          <h3 style={{ fontSize: '16px', fontWeight: 600, lineHeight: 1.5, marginBottom: '20px' }}>
            {questionData.question}
          </h3>

          {/* Options */}
          <div className="options-list">
            {(questionData.options || []).map((opt, idx) => {
              const letter = opt.trim().charAt(0);
              const isSelected = selectedOption.startsWith(letter);

              let optionClass = 'option-button';
              if (isSelected) optionClass += ' selected';
              if (submitted && letter === questionData.correct_option) {
                optionClass += ' correct';
              } else if (submitted && isSelected && letter !== questionData.correct_option) {
                optionClass += ' incorrect';
              }

              return (
                <button
                  key={idx}
                  type="button"
                  className={optionClass}
                  onClick={() => !submitted && setSelectedOption(opt)}
                  disabled={submitted || isSubmitting}
                >
                  <span style={{ fontWeight: 700, width: '28px', color: 'var(--color-text-secondary)' }}>
                    {letter})
                  </span>
                  <span>{opt.substring(opt.indexOf(')') + 1).trim() || opt}</span>
                </button>
              );
            })}
          </div>

          {/* Actions & Feedback */}
          {!submitted ? (
            <div style={{ marginTop: '20px', display: 'flex', justifyContent: 'flex-end' }}>
              <button
                type="button"
                className="btn-primary"
                onClick={handleSubmit}
                disabled={!selectedOption || isSubmitting}
              >
                {isSubmitting ? 'Evaluating answer...' : 'Submit Answer'}
              </button>
            </div>
          ) : (
            <div style={{ marginTop: '24px', borderTop: '1px solid var(--color-border)', paddingTop: '18px' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '10px', marginBottom: '12px' }}>
                <span className={result?.is_correct ? 'badge-green' : 'badge-red'}>
                  {result?.is_correct ? '✓ Correct Answer' : '× Incorrect'}
                </span>
                <span style={{ fontSize: '13px', color: 'var(--color-text-secondary)' }}>
                  Score: <strong>{result?.score} / 100</strong>
                </span>
              </div>

              <div style={{ backgroundColor: 'var(--color-surface-subtle)', border: '1px solid var(--color-border)', borderRadius: 'var(--radius-sm)', padding: '14px', marginBottom: '20px' }}>
                <div style={{ fontSize: '13px', fontWeight: 700, marginBottom: '6px' }}>Explanation:</div>
                <div style={{ fontSize: '13px', color: 'var(--color-text-primary)', lineHeight: 1.6 }}>
                  {questionData.explanation}
                </div>
              </div>

              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <button
                  type="button"
                  className="btn-secondary"
                  onClick={() => onNavigate('tutor')}
                >
                  Ask AI Tutor why ?
                </button>
                <button
                  type="button"
                  className="btn-primary"
                  onClick={() => onNavigate('tests')}
                >
                  Take Full Assessment Test →
                </button>
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
