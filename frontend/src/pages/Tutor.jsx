import React, { useState } from 'react';
import { askAiTutor } from '../api/learningApi';

export default function Tutor({
  studentId = 'S001',
  currentTopic = 'Pointers',
  initialContextCode = '',
}) {
  const [messages, setMessages] = useState([
    {
      role: 'assistant',
      text: `Hello! I am your EduAdapt AI Tutor for Programming for Problem Solving. Ask me anything about ${currentTopic}, memory layout, or C code implementation.`,
    },
  ]);
  const [inputMessage, setInputMessage] = useState(
    initialContextCode ? `Can you explain what this C code is doing?\n\`\`\`c\n${initialContextCode}\n\`\`\`` : ''
  );
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState(null);

  const sendMessage = async (messageText, variation = null) => {
    if (!messageText.trim() || isLoading) return;

    const userMsg = { role: 'student', text: messageText };
    setMessages((prev) => [...prev, userMsg]);
    setInputMessage('');
    setIsLoading(true);
    setError(null);

    try {
      const res = await askAiTutor(studentId, currentTopic, messageText, variation);
      setMessages((prev) => [
        ...prev,
        { role: 'assistant', text: res.reply || 'No explanation generated.' },
      ]);
    } catch (err) {
      setError('Unable to get response from AI Tutor. Please check that EduAdapt backend is online.');
    } finally {
      setIsLoading(false);
    }
  };

  const handleSubmit = (e) => {
    e.preventDefault();
    sendMessage(inputMessage);
  };

  return (
    <div className="tutor-page">
      <header className="page-header">
        <h2 className="page-title">AI Tutor</h2>
        <p className="page-subtitle">
          Ask anything about <strong>{currentTopic}</strong>. Explanations are curriculum-grounded and adapted to your learning level.
        </p>
      </header>

      {error && (
        <div className="error-box">
          <h4>Notice</h4>
          <p>{error}</p>
        </div>
      )}

      <div className="chat-container">
        {/* Chat Messages */}
        <div className="chat-messages">
          {messages.map((m, idx) => (
            <div key={idx} className={`chat-bubble ${m.role}`}>
              <div className="bubble-role">
                {m.role === 'assistant' ? 'AI Tutor' : `Student (${studentId})`}
              </div>
              <div style={{ whiteSpace: 'pre-line' }}>{m.text}</div>
            </div>
          ))}
          {isLoading && (
            <div className="chat-bubble assistant">
              <div className="bubble-role">AI Tutor</div>
              <div style={{ fontStyle: 'italic', color: 'var(--color-text-secondary)' }}>
                Consulting PPS curriculum context and generating explanation...
              </div>
            </div>
          )}
        </div>

        {/* Input & Shortcuts */}
        <div className="chat-input-area">
          <div className="chat-shortcuts">
            <span style={{ fontSize: '12px', fontWeight: 600, color: 'var(--color-text-secondary)', alignSelf: 'center' }}>
              Quick prompts:
            </span>
            <button
              type="button"
              className="btn-pill"
              disabled={isLoading}
              onClick={() => sendMessage(`Explain ${currentTopic} in simpler terms with an analogy.`, 'simpler')}
            >
              Explain simpler
            </button>
            <button
              type="button"
              className="btn-pill"
              disabled={isLoading}
              onClick={() => sendMessage(`Give me a clean practical C code example of ${currentTopic}.`, 'example')}
            >
              Give example
            </button>
            <button
              type="button"
              className="btn-pill"
              disabled={isLoading}
              onClick={() => sendMessage(`Give me a short conceptual practice question about ${currentTopic}.`, 'practice_question')}
            >
              Give practice question
            </button>
          </div>

          <form onSubmit={handleSubmit} className="chat-form">
            <input
              type="text"
              className="chat-input"
              placeholder={`Ask anything about ${currentTopic}...`}
              value={inputMessage}
              onChange={(e) => setInputMessage(e.target.value)}
              disabled={isLoading}
            />
            <button
              type="submit"
              className="btn-primary"
              disabled={isLoading || !inputMessage.trim()}
              style={{ width: 'auto', padding: '0 20px' }}
            >
              {isLoading ? '...' : 'Send'}
            </button>
          </form>
        </div>
      </div>
    </div>
  );
}
