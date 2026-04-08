import { useState, useCallback, useRef, useEffect } from "react";


/**
 * useAddPlayer - manages player search and adding to a team.
 *
 * @param {{ teamId: number|string, onAdded?: () => void }} options
 */
export function useAddPlayer({ teamId, onAdded } = {}) {
    const [isOpen,    setIsOpen]    = useState(false);
    const [query,     setQuery]     = useState("");
    const [results,   setResults]   = useState([]);
    const [searching, setSearching] = useState(false);
    const [searchErr, setSearchErr] = useState(null);
    const [addingId,  setAddingId]  = useState(null); // accountId currently being added
    const [addedIds,  setAddedIds]  = useState(new Set());
    const [addErr,    setAddErr]    = useState(null);

    const debounceRef = useRef(null);

    const openPanel  = useCallback(() => { setIsOpen(true);  }, []);
    const closePanel = useCallback(() => {
        setIsOpen(false);
        setQuery("");
        setResults([]);
        setSearchErr(null);
        setAddErr(null);
    }, []);

    // Debounced search
    useEffect(() => {
        if (!isOpen) return;
        if (!query.trim()) {
            setResults([]);
            setSearchErr(null);
            return;
        }

        clearTimeout(debounceRef.current);
        debounceRef.current = setTimeout(async () => {
            setSearching(true);
            setSearchErr(null);
            try {
                const res  = await fetch(`/api/teams/${teamId}/players/search?q=${encodeURIComponent(query.trim())}`);
                const data = await res.json();
                if (!res.ok) throw new Error(data?.message || "Search failed.");
                setResults(data.results ?? []);
            } catch (err) {
                setSearchErr(err.message);
                setResults([]);
            } finally {
                setSearching(false);
            }
        }, 350);

        return () => clearTimeout(debounceRef.current);
    }, [query, teamId, isOpen]);

    const addPlayer = useCallback(async (accountId) => {
        setAddingId(accountId);
        setAddErr(null);
        try {
            const res  = await fetch(`/api/teams/${teamId}/players`, {
                method:  "POST",
                headers: { "Content-Type": "application/json" },
                body:    JSON.stringify({accountId }),
            });
            const data = await res.json();
            if (!res.ok) throw new Error(data?.message || "Failed to add player.");
            setAddedIds(prev => new Set(prev).add(accountId));

            // optimistic update
            const newPlayer = {
                id: accountId,
                accountId,
                name: results.find(r => r.accountId === accountId)?.name ?? "New player"
            };
            setAddedIds(prev => new Set(prev).add(accountId));
            onAdded?.(newPlayer);
        } catch (err) {
            setAddErr(err.message);
        } finally {
            setAddingId(null);
        }
    }, [teamId, onAdded]);

    return {
        isOpen, openPanel, closePanel,
        query, setQuery,
        results, searching, searchErr,
        addPlayer, addingId, addedIds, addErr,
    };
}
