import { useEffect, useState } from "react";

export function useLadders(clubId) {
  const [ladders, setLadders] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    if (!clubId) return;

    fetch(`/api/clubs/${clubId}/ladders`)
      .then(res => res.json())
      .then(data => {
        setLadders(data.ladders);
        setLoading(false);
      })
      .catch(err => {
        setError(err);
        setLoading(false);
      });

  }, [clubId]);

  return { ladders, loading, error };
}