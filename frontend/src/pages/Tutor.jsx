import React, { useState, useRef } from 'react';
import { askAiTutor, transcribeAudioFile, synthesizeLessonAudio } from '../api/learningApi';
import MermaidDiagram from '../components/MermaidDiagram';

function ChatMessageContent({ text }) {
  if (!text) return null;

  const parts = [];
  const blockRegex = /```(c|C|mermaid)?\s*([\s\S]*?)```/g;
  let lastIndex = 0;
  let match;

  while ((match = blockRegex.exec(text)) !== null) {
    if (match.index > lastIndex) {
      const textChunk = text.substring(lastIndex, match.index).trim();
      if (textChunk) {
        parts.push({ type: 'text', content: textChunk });
      }
    }

    const lang = (match[1] || '').toLowerCase();
    const body = match[2].trim();

    if (lang === 'mermaid' || body.startsWith('flowchart') || body.startsWith('graph')) {
      parts.push({ type: 'diagram', content: body });
    } else {
      parts.push({ type: 'code', content: body });
    }

    lastIndex = blockRegex.lastIndex;
  }

  if (lastIndex < text.length) {
    const remaining = text.substring(lastIndex).trim();
    if (remaining) {
      parts.push({ type: 'text', content: remaining });
    }
  }

  // If no code or diagram blocks, render simple text
  if (parts.length === 0) {
    return <div style={{ whiteSpace: 'pre-line' }}>{text}</div>;
  }

  return (
    <div>
      {parts.map((p, idx) => {
        if (p.type === 'code') {
          return (
            <div key={idx} className="code-container" style={{ margin: '10px 0' }}>
              <div className="code-header">
                <span>C Code</span>
              </div>
              <pre className="code-block"><code>{p.content}</code></pre>
            </div>
          );
        }
        if (p.type === 'diagram') {
          return (
            <div key={idx} style={{ margin: '10px 0' }}>
              <MermaidDiagram code={p.content} title="Concept Architecture" />
            </div>
          );
        }
        return (
          <div key={idx} style={{ whiteSpace: 'pre-line', marginBottom: '8px' }}>
            {p.content}
          </div>
        );
      })}
    </div>
  );
}

export default function Tutor({
  studentId = 'S001',
  currentTopic = 'Pointers',
  initialContextCode = '',
  initialContextQuestion = null,
}) {
  const [messages, setMessages] = useState([
    {
      role: 'assistant',
      text: `Hello! I am your EduAdapt AI Tutor for Programming for Problem Solving. Ask me anything about ${currentTopic}, memory layout, or C code implementation.`,
    },
  ]);
  const [inputMessage, setInputMessage] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState(null);

  // Audio Accessibility State
  const [isRecording, setIsRecording] = useState(false);
  const [isTranscribing, setIsTranscribing] = useState(false);
  const [recordingError, setRecordingError] = useState(null);
  const [speakingIdx, setSpeakingIdx] = useState(null);
  const mediaRecorderRef = useRef(null);
  const audioChunksRef = useRef([]);
  const audioPlayerRef = useRef(null);

  const startVoiceRecording = async () => {
    setRecordingError(null);
    if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
      setRecordingError('Microphone audio recording is not supported in this browser environment.');
      return;
    }

    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      audioChunksRef.current = [];
      const recorder = new MediaRecorder(stream);
      mediaRecorderRef.current = recorder;

      recorder.ondataavailable = (e) => {
        if (e.data.size > 0) {
          audioChunksRef.current.push(e.data);
        }
      };

      recorder.onstop = async () => {
        stream.getTracks().forEach((track) => track.stop());
        const audioBlob = new Blob(audioChunksRef.current, { type: 'audio/wav' });
        if (audioBlob.size === 0) {
          setRecordingError('No audio recorded. Please try again.');
          return;
        }

        setIsTranscribing(true);
        try {
          const res = await transcribeAudioFile(audioBlob, 'question.wav');
          if (res && res.transcription) {
            setInputMessage((prev) => (prev ? `${prev} ${res.transcription}` : res.transcription));
          } else {
            setRecordingError('No transcription returned from speech engine.');
          }
        } catch (err) {
          setRecordingError(`Voice transcription error: ${err.message || 'Check backend audio pipeline'}`);
        } finally {
          setIsTranscribing(false);
        }
      };

      recorder.start();
      setIsRecording(true);
    } catch (err) {
      setRecordingError(`Could not access microphone: ${err.message}. Please allow microphone permissions.`);
    }
  };

  const stopVoiceRecording = () => {
    if (mediaRecorderRef.current && isRecording) {
      mediaRecorderRef.current.stop();
      setIsRecording(false);
    }
  };

  const handleSpeakMessage = async (idx, text) => {
    if (speakingIdx === idx) {
      if (audioPlayerRef.current) {
        audioPlayerRef.current.pause();
      }
      if (typeof window !== 'undefined' && window.speechSynthesis) {
        window.speechSynthesis.cancel();
      }
      setSpeakingIdx(null);
      return;
    }

    setSpeakingIdx(idx);

    try {
      const blob = await synthesizeLessonAudio(text, 170);
      const url = URL.createObjectURL(blob);
      if (!audioPlayerRef.current) {
        audioPlayerRef.current = new Audio();
      }
      audioPlayerRef.current.src = url;
      audioPlayerRef.current.onended = () => setSpeakingIdx(null);
      audioPlayerRef.current.onerror = () => setSpeakingIdx(null);
      await audioPlayerRef.current.play();
    } catch {
      // Browser Web Speech fallback
      if (typeof window !== 'undefined' && 'speechSynthesis' in window) {
        window.speechSynthesis.cancel();
        const clean = text.replace(/```[\s\S]*?```/g, ' [code displayed on screen] ');
        const utter = new SpeechSynthesisUtterance(clean);
        utter.onend = () => setSpeakingIdx(null);
        utter.onerror = () => setSpeakingIdx(null);
        window.speechSynthesis.speak(utter);
      } else {
        setSpeakingIdx(null);
      }
    }
  };

  const sendMessage = async (messageText, variation = null) => {
    if (!messageText || !messageText.trim() || isLoading) return;

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

  React.useEffect(() => {
    if (initialContextQuestion && initialContextQuestion.question) {
      const prompt = `I answered option ${initialContextQuestion.selectedOption} for the question: "${initialContextQuestion.question}". The correct answer is ${initialContextQuestion.correctOption}. Can you explain conceptually why this is correct and help me master this topic?`;
      sendMessage(prompt);
    } else if (initialContextCode) {
      setInputMessage(`Can you explain what this C code is doing?\n\`\`\`c\n${initialContextCode}\n\`\`\``);
    }
  }, [initialContextQuestion, initialContextCode]);

  const handleSubmit = (e) => {
    e.preventDefault();
    sendMessage(inputMessage);
  };

  return (
    <div className="tutor-page">
      <header className="page-header">
        <h2 className="page-title">AI Tutor</h2>
        <p className="page-subtitle">
          Ask anything about <strong>{currentTopic}</strong>. Explanations are curriculum-grounded and adapted to Student <strong>{studentId}</strong>.
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
              <div className="bubble-role" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <span>{m.role === 'assistant' ? 'AI Tutor' : `Student (${studentId})`}</span>
                {m.role === 'assistant' && (
                  <button
                    type="button"
                    onClick={() => handleSpeakMessage(idx, m.text)}
                    style={{
                      background: 'none',
                      border: 'none',
                      cursor: 'pointer',
                      fontSize: '13px',
                      color: 'var(--color-primary, #3b82f6)',
                      padding: '2px 6px',
                      borderRadius: '4px',
                    }}
                    title={speakingIdx === idx ? 'Stop reading' : 'Read explanation aloud'}
                    aria-label={speakingIdx === idx ? 'Stop reading' : 'Read explanation aloud'}
                  >
                    {speakingIdx === idx ? '⏹ Stop' : '🔊 Listen'}
                  </button>
                )}
              </div>
              <ChatMessageContent text={m.text} />
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

        {/* Recording / Transcribing Indicator & Error Box */}
        {recordingError && (
          <div style={{ padding: '8px 14px', background: '#fee2e2', color: '#991b1b', borderRadius: '6px', margin: '0 16px 8px 16px', fontSize: '13px' }}>
            {recordingError}
          </div>
        )}
        {isRecording && (
          <div style={{ padding: '8px 14px', background: '#ecfdf5', color: '#065f46', borderRadius: '6px', margin: '0 16px 8px 16px', fontSize: '13px', display: 'flex', alignItems: 'center', gap: '8px' }}>
            <span style={{ display: 'inline-block', width: '10px', height: '10px', borderRadius: '50%', background: '#ef4444', animation: 'pulse 1s infinite' }}></span>
            <span>Recording speech... Click <strong>Stop Recording</strong> when done.</span>
          </div>
        )}
        {isTranscribing && (
          <div style={{ padding: '8px 14px', background: '#eff6ff', color: '#1e40af', borderRadius: '6px', margin: '0 16px 8px 16px', fontSize: '13px' }}>
            Transcribing speech using Whisper...
          </div>
        )}

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
              onClick={() => sendMessage(`Explain ${currentTopic} in simpler terms with an analogy and memory diagram.`, 'simpler')}
            >
              Explain simpler with diagram
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
            <button
              type="button"
              className="btn-pill"
              onClick={isRecording ? stopVoiceRecording : startVoiceRecording}
              disabled={isLoading || isTranscribing}
              style={{
                backgroundColor: isRecording ? '#ef4444' : undefined,
                color: isRecording ? '#ffffff' : undefined,
                fontWeight: 600,
                whiteSpace: 'nowrap',
              }}
              aria-label={isRecording ? 'Stop voice recording' : 'Voice input via microphone'}
            >
              {isRecording ? '⏹ Stop Recording' : isTranscribing ? 'Transcribing...' : '🎤 Speak'}
            </button>
            <input
              type="text"
              className="chat-input"
              placeholder={`Ask anything about ${currentTopic}...`}
              value={inputMessage}
              onChange={(e) => setInputMessage(e.target.value)}
              disabled={isLoading || isRecording}
            />
            <button
              type="submit"
              className="btn-primary"
              disabled={isLoading || !inputMessage.trim() || isRecording}
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
