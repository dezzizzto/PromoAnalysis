import { useState, useEffect, useCallback } from "react";

export function usePolling(fn, interval = 3000) {
  const [data, setData] = useState(null);
  const [error, setError] = useState(null);

  const refetch = useCallback(async () => {
    try {
      const result = await fn();
      setData(result);
      setError(null);
    } catch (err) {
      setError(err.message);
    }
  }, [fn]);

  useEffect(() => {
    refetch();
    const id = setInterval(refetch, interval);
    return () => clearInterval(id);
  }, [refetch, interval]);

  return { data, error, refetch };
}
