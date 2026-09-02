// src/hooks/useHealthCheck.js
//
// Polls /health on mount so the UI can show a "waking up" message during a
// Render free-tier cold start, instead of every chart just silently hanging
// or erroring on the first load after the API's been idle.
import { useEffect, useRef, useState } from 'react';
import { apiGet } from '../api/client';

const POLL_INTERVAL_MS = 3000;
const MAX_ATTEMPTS = 12; // ~36s, comfortably past a typical free-tier cold start

export function useHealthCheck() {
  const [status, setStatus] = useState('checking'); // 'checking' | 'ok' | 'slow' | 'unreachable'
  const attemptsRef = useRef(0);

  useEffect(() => {
    let cancelled = false;
    let timer;

    const check = async () => {
      attemptsRef.current += 1;
      try {
        const health = await apiGet('/health');
        if (cancelled) return;
        if (health.database === 'ok') {
          setStatus('ok');
          return;
        }
        throw new Error('database unreachable');
      } catch {
        if (cancelled) return;
        if (attemptsRef.current >= MAX_ATTEMPTS) {
          setStatus('unreachable');
          return;
        }
        setStatus('slow');
        timer = setTimeout(check, POLL_INTERVAL_MS);
      }
    };

    check();

    return () => {
      cancelled = true;
      clearTimeout(timer);
    };
  }, []);

  return status;
}
