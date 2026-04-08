export function Mark({ className }: { className?: string }) {
  return (
    <svg viewBox="0 0 32 32" className={className} aria-hidden="true">
      <circle cx="16" cy="16" r="11" fill="none" stroke="currentColor" strokeWidth="1.4" />
      <circle cx="16" cy="16" r="3.5" fill="none" stroke="currentColor" strokeWidth="1.4" />
      <path
        d="M16 4.5v4.2M16 23.3v4.2M4.5 16h4.2M23.3 16h4.2"
        stroke="currentColor"
        strokeWidth="1.4"
        strokeLinecap="round"
      />
    </svg>
  );
}
