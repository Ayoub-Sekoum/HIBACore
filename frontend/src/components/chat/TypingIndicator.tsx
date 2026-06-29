
// src/components/chat/TypingIndicator.tsx
export default function TypingIndicator() {
  return (
    <div style={{ display: 'flex', alignItems: 'center', gap: '4px', padding: '8px 12px' }}>
      {[0, 1, 2].map((i) => (
        <span
          key={i}
          style={{
            width: '6px', height: '6px',
            borderRadius: '50%',
            backgroundColor: 'var(--apple-text-muted)',
            animation: `bounce 1.2s ease-in-out ${i * 0.2}s infinite`,
          }}
        />
      ))}
      <style>{`
        @keyframes bounce {
          0%, 80%, 100% { transform: translateY(0); }
          40% { transform: translateY(-6px); }
        }
      `}</style>
    </div>
  );
}
