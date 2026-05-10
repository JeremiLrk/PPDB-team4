import { useState, useCallback, useEffect } from "react";

/**
 * useCreateMatch
 *
 * State machine for the three-step "Create Match" form:
 *
 *   step 0  - pick which managed team is team1
 *   step 1  - pick which ladder that team belongs to
 *   step 2  - pick the opponent (team2) from the same ladder
 *   step 3  - submit the proposal
 *
 * Separate boolean flags drive loading/success/closed states so that
 * step numbers 0-2 are never overloaded with a second meaning.
 */
export function useCreateMatch({ managedTeams = [], onCreated } = {}) {
    // -1 = closed, 0-2 = wizard page index
    const [step,      setStep]      = useState(-1);
    const [isLoading, setIsLoading] = useState(false);
    const [isSuccess, setIsSuccess] = useState(false);
    const [error,     setError]     = useState("");

    // Step 0 — chosen team (team1)
    const [selectedTeamId, setSelectedTeamId] = useState("");

    // Step 1 — ladders for the chosen team
    const [ladders,          setLadders]          = useState([]);
    const [laddersLoading,   setLaddersLoading]   = useState(false);
    const [laddersError,     setLaddersError]     = useState("");
    const [selectedLadderId, setSelectedLadderId] = useState("");

    // Step 2 — peer teams in the same ladder
    const [peers,          setPeers]          = useState([]);
    const [peersLoading,   setPeersLoading]   = useState(false);
    const [peersError,     setPeersError]     = useState("");
    const [selectedPeerId, setSelectedPeerId] = useState("");

    // ------------------------------------------------------------------
    // Open / close
    // ------------------------------------------------------------------

    const openPanel = useCallback(() => {
        setStep(0);
        setIsLoading(false);
        setIsSuccess(false);
        setError("");
        setSelectedTeamId(managedTeams.length === 1 ? String(managedTeams[0].id) : "");
        setSelectedLadderId("");
        setSelectedPeerId("");
        setLadders([]);
        setPeers([]);
        setLaddersError("");
        setPeersError("");
    }, [managedTeams]);

    const closePanel = useCallback(() => {
        setStep(-1);
        setIsLoading(false);
        setIsSuccess(false);
        setError("");
    }, []);

    // ------------------------------------------------------------------
    // Step 0 -> effect: load ladders whenever selectedTeamId changes
    //
    // Calls the club's ladder list, then probes each ladder via the
    // GET /api/teams/<id>/ladder-peers endpoint in parallel.
    // A 200 response means the team is a member of that ladder.
    // ------------------------------------------------------------------

    useEffect(() => {
        if (!selectedTeamId) return;

        let alive = true;

        setLaddersLoading(true);
        setLaddersError("");
        setLadders([]);
        setSelectedLadderId("");
        setPeers([]);
        setSelectedPeerId("");

        async function loadLadders() {
            try {
                const team = managedTeams.find(t => String(t.id) === String(selectedTeamId));
                if (!team) throw new Error("Selected team not found.");

                if (!team.clubId) {
                    if (alive) {
                        setLadders([]);
                        setLaddersError("This team does not belong to a club and has no ladders.");
                        setLaddersLoading(false);
                    }
                    return;
                }

                // 1. All ladders for the team's club
                const clubRes  = await fetch(
                    `/api/clubs/${team.clubId}/ladders`,
                    { credentials: "include" },
                );
                const clubData = await clubRes.json();
                if (!clubRes.ok) {
                    throw new Error(clubData?.message || "Failed to load club ladders.");
                }

                const allLadders = clubData.ladders ?? [];

                // 2. Keep only ladders where this team is a member (parallel)
                const membership = await Promise.all(
                    allLadders.map(async (ladder) => {
                        const res = await fetch(
                            `/api/teams/${selectedTeamId}/ladder-peers?ladder_id=${ladder.id}`,
                            { credentials: "include" },
                        );
                        return res.ok ? ladder : null;
                    }),
                );

                const joined = membership.filter(Boolean);

                if (alive) {
                    setLadders(joined);
                    // Auto-select when there is exactly one ladder
                    if (joined.length === 1) setSelectedLadderId(String(joined[0].id));
                    setLaddersLoading(false);
                }
            } catch (err) {
                if (alive) {
                    setLaddersError(err.message);
                    setLaddersLoading(false);
                }
            }
        }

        loadLadders();
        return () => { alive = false; };
    }, [selectedTeamId, managedTeams]);

    // ------------------------------------------------------------------
    // Step 1 -> effect: load peer teams when ladder selection changes
    // ------------------------------------------------------------------

    useEffect(() => {
        if (!selectedTeamId || !selectedLadderId) return;

        let alive = true;

        setPeersLoading(true);
        setPeersError("");
        setPeers([]);
        setSelectedPeerId("");

        async function loadPeers() {
            try {
                const res  = await fetch(
                    `/api/teams/${selectedTeamId}/ladder-peers?ladder_id=${selectedLadderId}`,
                    { credentials: "include" },
                );
                const data = await res.json();

                if (!res.ok) {
                    throw new Error(
                        data?.description || data?.message || "Failed to load opponents.",
                    );
                }

                if (alive) {
                    setPeers(data.peers ?? []);
                    setPeersLoading(false);
                }
            } catch (err) {
                if (alive) {
                    setPeersError(err.message);
                    setPeersLoading(false);
                }
            }
        }

        loadPeers();
        return () => { alive = false; };
    }, [selectedTeamId, selectedLadderId]);

    // ------------------------------------------------------------------
    // Navigation
    // ------------------------------------------------------------------

    const nextStep = useCallback(() => {
        setError("");
        setStep(s => s + 1);
    }, []);

    const prevStep = useCallback(() => {
        setError("");
        setStep(s => s - 1);
    }, []);

    // Whether the current step allows moving forward
    const canNext = (() => {
        if (step === 0) return !!selectedTeamId;
        if (step === 1) return !!selectedLadderId && !laddersLoading;
        if (step === 2) return !!selectedPeerId   && !peersLoading;
        return true;
    })();

    // ------------------------------------------------------------------
    // Submit
    // ------------------------------------------------------------------

    const submit = useCallback(async () => {
        if (!selectedTeamId || !selectedPeerId) return;

        setIsLoading(true);
        setError("");

        try {
            const team = managedTeams.find(t => String(t.id) === String(selectedTeamId));

            const body = {
                team1Id:     Number(selectedTeamId),
                team2Id:     Number(selectedPeerId),
                sportTypeId: team?.sportTypeId ?? null,
            };

            if (selectedLadderId) body.ladderId = Number(selectedLadderId);

            const res  = await fetch("/api/matches", {
                method:      "POST",
                credentials: "include",
                headers:     { "Content-Type": "application/json" },
                body:        JSON.stringify(body),
            });
            const data = await res.json();

            if (!res.ok) {
                setError(data?.description || data?.message || "Failed to create match.");
                setIsLoading(false);
                return;
            }

            setIsLoading(false);
            setIsSuccess(true);
            onCreated?.(data.match);
            setTimeout(closePanel, 1600);

        } catch {
            setError("Network error. Please try again.");
            setIsLoading(false);
        }
    }, [
        selectedTeamId, selectedPeerId, selectedLadderId,
        managedTeams, onCreated, closePanel,
    ]);

    // ------------------------------------------------------------------
    // Public interface
    // ------------------------------------------------------------------

    return {
        // Panel lifecycle
        isOpen:    step !== -1,
        isLoading,
        isSuccess,
        error,
        openPanel,
        closePanel,

        // Wizard navigation
        step,
        nextStep,
        prevStep,
        canNext,

        // Step 0
        selectedTeamId,
        setSelectedTeamId,

        // Step 1
        ladders,
        laddersLoading,
        laddersError,
        selectedLadderId,
        setSelectedLadderId,

        // Step 2
        peers,
        peersLoading,
        peersError,
        selectedPeerId,
        setSelectedPeerId,

        submit,
    };
}
