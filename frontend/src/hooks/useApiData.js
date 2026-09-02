// src/hooks/useApiData.js
import { useCallback, useEffect, useState } from 'react';
import { apiGet } from '../api/client';

export function useApiData(path) {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [attempt, setAttempt] = useState(0);

  const retry = useCallback(() => setAttempt((a) => a + 1), []);

  useEffect(() => {
    let cancelled = false;
    setLoading(true);
    setError(null);

    apiGet(path)
      .then((json) => {
        if (!cancelled) {
          setData(json);
          setLoading(false);
        }
      })
      .catch((err) => {
        if (!cancelled) {
          setError(err.message || 'Something went wrong.');
          setLoading(false);
        }
      });

    return () => {
      cancelled = true;
    };
  }, [path, attempt]);

  return { data, loading, error, retry };
}
