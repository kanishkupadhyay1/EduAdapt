const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';

export async function fetchStudentProfile(studentId = 'S001') {
  const res = await fetch(`${API_BASE_URL}/api/student/${encodeURIComponent(studentId)}`);
  if (!res.ok) {
    throw new Error(`HTTP ${res.status}: ${res.statusText}`);
  }
  return await res.json();
}

export async function generateLearningSession(studentId = 'S001', topic = 'Pointers', topK = 3, provider = 'ollama', model = 'mistral:7b') {
  const res = await fetch(`${API_BASE_URL}/api/session/generate`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      student_id: studentId,
      topic: topic,
      top_k: Number(topK),
      provider: provider,
      model: model,
    }),
  });
  if (!res.ok) {
    let detail = `HTTP ${res.status}`;
    try {
      const j = await res.json();
      if (j.detail) detail = j.detail;
    } catch {}
    throw new Error(detail);
  }
  return await res.json();
}

export async function askAiTutor(studentId = 'S001', topic = 'Pointers', message = '', promptVariation = null) {
  const res = await fetch(`${API_BASE_URL}/api/tutor/chat`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      student_id: studentId,
      topic: topic,
      message: message,
      prompt_variation: promptVariation,
    }),
  });
  if (!res.ok) {
    let detail = `HTTP ${res.status}`;
    try {
      const j = await res.json();
      if (j.detail) detail = j.detail;
    } catch {}
    throw new Error(detail);
  }
  return await res.json();
}

export async function fetchTopicAssessment(studentId = 'S001', topic = 'Pointers') {
  const res = await fetch(`${API_BASE_URL}/api/assessment/${encodeURIComponent(studentId)}/${encodeURIComponent(topic)}`);
  if (!res.ok) {
    throw new Error(`HTTP ${res.status}: ${res.statusText}`);
  }
  return await res.json();
}

export async function submitAssessmentAnswer(studentId = 'S001', topic = 'Pointers', selectedOption = 'B', timeTaken = 25) {
  const res = await fetch(`${API_BASE_URL}/api/assessment/submit`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      student_id: studentId,
      topic: topic,
      selected_option: selectedOption,
      time_taken_seconds: Number(timeTaken),
    }),
  });
  if (!res.ok) {
    let detail = `HTTP ${res.status}`;
    try {
      const j = await res.json();
      if (j.detail) detail = j.detail;
    } catch {}
    throw new Error(detail);
  }
  return await res.json();
}
