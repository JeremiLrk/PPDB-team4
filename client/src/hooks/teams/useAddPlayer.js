import { useState, useCallback, useRef, useEffect } from "react";

/**
 * useAddPlayer - manages player search and adding to a team.
 *
 * @param {{ teamId: number|string, onAdded?: (player: object) => void }} options
 */
export function useAddPlayer({ teamId, onAdded } = {}) {
    const [isOpen,    setIsOpen]    = useState(false);
    const [query,     setQuery]     = useState("");
    const [results,   setResults]   = useState([]);
    const [searching, setSearching] = useState(false);
    const [searchErr, setSearchErr] = useState(null);
    const [addingId,  setAddingId]  = useState(null);
    const [addedIds,  setAddedIds]  = useState(new Set());
    const [addErr,    setAddErr]    = useState(null);

    const debounceRef = useRef(null);
    const inputRef    = useRef(null); // controlled by hook, passed to component

    const openPanel = useCallback(() => {
        setIsOpen(true);
    }, []);

    const closePanel = useCallback(() => {
        setIsOpen(false);
        setQuery("");
        setResults([]);
        setSearchErr(null);
        setAddErr(null);
    }, []);

    // Auto-focus when opening
    useEffect(() => {
        if (isOpen) {
            const t = setTimeout(() => inputRef.current?.focus(), 60);
            return () => clearTimeout(t);
        }
    }, [isOpen]);

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
                body:    JSON.stringify({ accountId }),
            });
            const data = await res.json();
            if (!res.ok) throw new Error(data?.message || "Failed to add player.");

            setAddedIds(prev => new Set(prev).add(accountId));

            const found     = results.find(r => r.id === accountId);
            const newPlayer = {
                id:        accountId,
                accountId,
                name: found
                    ? [found.firstName, found.lastName].filter(Boolean).join(" ") || found.email
                    : "New player",
            };
            onAdded?.(newPlayer);
        } catch (err) {
            setAddErr(err.message);
        } finally {
            setAddingId(null);
        }
    }, [teamId, onAdded, results]); // results in deps — read the current list

    return {
        isOpen, openPanel, closePanel,
        query, setQuery,
        results, searching, searchErr,
        addPlayer, addingId, addedIds, addErr,
        inputRef, // component throws in <input ref={inputRef}>
    };
}