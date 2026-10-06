import React from 'react';

export default function Header({ studentId = 'S001' }) {
  return (
    <header className="app-header">
      <div>
        <h1 className="brand-title">EduAdapt</h1>
        <div className="brand-subtitle">Adaptive Learning Platform</div>
      </div>
      <div className="header-meta">
        <div className="student-tag">
          Student ID: {studentId}
        </div>
      </div>
    </header>
  );
}
