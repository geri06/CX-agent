import { useState, useEffect, useRef } from 'react';

export default function TypewriterText({ text, speed = 12 }) {
  const [displayed, setDisplayed] = useState('');
  const [isDone, setIsDone] = useState(false);
  const indexRef = useRef(0);

  useEffect(() => {
    // Reset on text change
    setDisplayed('');
    setIsDone(false);
    indexRef.current = 0;

    if (!text) return;

    const interval = setInterval(() => {
      indexRef.current += 1;
      const nextChunk = text.slice(0, indexRef.current);
      setDisplayed(nextChunk);

      if (indexRef.current >= text.length) {
        clearInterval(interval);
        setIsDone(true);
      }
    }, speed);

    return () => clearInterval(interval);
  }, [text, speed]);

  return (
    <span>
      {displayed}
      {!isDone && (
        <span className="inline-block w-[2px] h-[14px] bg-[var(--color-accent)] ml-0.5 animate-pulse align-middle" />
      )}
    </span>
  );
}
