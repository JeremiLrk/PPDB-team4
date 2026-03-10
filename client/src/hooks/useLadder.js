import { useEffect, useState } from "react";

export function useLadders() {
  const [ladders, setLadders] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    fetch("/api/ladders")
      .then(res => res.json())
      .then(data => {
        setLadders(data);
        setLoading(false);
      })
      .catch(err => {
        setError(err);
        setLoading(false);
      });
  }, []);


  return { ladders, loading, error };
}