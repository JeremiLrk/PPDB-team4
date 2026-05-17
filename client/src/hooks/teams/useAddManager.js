// Team management hook for useAddManager.

import { useState, useCallback, useRef, useEffect } from "react";

/**
 * useAddManager - controls the account search and adding of a team manager.
 *
 * Step 0: Account search
 * Step 1: Select rights (TeamManagerTeam)
 *
 * @param {{ teamId: number|string, onAdded?: (manager: object) => void }} options
 */
export function useAddManager({ teamId, onAdded } = {}) {
    /*
     Owns the manager-search wizard and permission selection flow.
    */
    const [isOpen,    setIsOpen]    = useState(false);
    const [step,      setStep]      = useState(0);
    const [query,     setQuery]     = useState("");
    const [results,   setResults]   = useState([]);
    const [searching, setSearching] = useState(false);
    const [searchErr, setSearchErr] = useState(null);

    const [selected,  setSelected]  = useState(null);

    const [permissions, setPermissions] = useState({
        canRename:       true,
        canDelete:       true,
        canEditPlayers:  true,
        canEditManagers: true,
    });

    const [addingId,  setAddingId]  = useState(null);
    const [addedIds,  setAddedIds]  = useState(new Set());
    const [addErr,    setAddErr]    = useState(null);
    const [isSuccess, setIsSuccess] = useState(false);

    const debounceRef = useRef(null);
    const inputRef    = useRef(null);

    const openPanel = useCallback(() => {
        /*
         Opens the manager picker at the first step.
        */
        setIsOpen(true);
        setStep(0);
    }, []);

    const closePanel = useCallback(() => {
        /*
         Closes the picker and resets every draft field.
        */
        setIsOpen(false);
        setStep(0);
        setQuery("");
        setResults([]);
        setSelected(null);
        setSearchErr(null);
        setAddErr(null);
        setIsSuccess(false);
        setPermissions({
            canRename:       true,
            canDelete:       true,
            canEditPlayers:  true,
            canEditManagers: true,
        });
    }, []);

    useEffect(() => {
        /*
         Focuses the search field when the first step opens.
        */
        if (isOpen && step === 0) {
            const t = setTimeout(() => inputRef.current?.focus(), 60);
            return () => clearTimeout(t);
        }
    }, [isOpen, step]);

    useEffect(() => {
        /*
         Debounces manager search requests only on the search step.
        */
        if (!isOpen || step !== 0) return;

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
                const res  = await fetch(
                    `/api/teams/${teamId}/managers/search?q=${encodeURIComponent(query.trim())}`,
                    { credentials: "include" }
                );
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
    }, [query, teamId, isOpen, step]);

    // Select an account and go to step 1
    const selectAccount = useCallback((account) => {
        /*
         Locks in the chosen account and advances to the permissions step.
        */
        setSelected(account);
        setAddErr(null);
        setStep(1);
    }, []);

    // Return to step 0
    const goBack = useCallback(() => {
        /*
         Returns from the permissions step to search.
        */
        setStep(0);
        setSelected(null);
        setAddErr(null);
    }, []);

    const togglePermission = useCallback((key) => {
        /*
         Flips one manager permission checkbox.
        */
        setPermissions(prev => ({ ...prev, [key]: !prev[key] }));
    }, []);

    // Send request to server
    const submit = useCallback(async () => {
        /*
         Sends the selected manager and chosen permissions to the backend.
        */
        if (!selected) return;
        setAddingId(selected.id);
        setAddErr(null);
        try {
            const res = await fetch(`/api/teams/${teamId}/managers`, {
                method:      "POST",
                credentials: "include",
                headers:     { "Content-Type": "application/json" },
                body:        JSON.stringify({
                    accountId:       selected.id,
                    canRename:       permissions.canRename,
                    canDelete:       permissions.canDelete,
                    canEditPlayers:  permissions.canEditPlayers,
                    canEditManagers: permissions.canEditManagers,
                }),
            });
            const data = await res.json();
            if (!res.ok) throw new Error(data?.description || data?.message || "Failed to add manager.");

            setAddedIds(prev => new Set(prev).add(selected.id));
            setIsSuccess(true);
            onAdded?.(data.manager ?? selected);
            setTimeout(closePanel, 1400);
        } catch (err) {
            setAddErr(err.message);
        } finally {
            setAddingId(null);
        }
    }, [selected, permissions, teamId, onAdded, closePanel]);

    return {
        isOpen, openPanel, closePanel,
        step,
        query, setQuery,
        results, searching, searchErr,
        selected, selectAccount, goBack,
        permissions, togglePermission,
        submit, addingId, addedIds, addErr,
        isSuccess,
        inputRef,
    };
}
