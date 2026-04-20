import { useEffect, useState } from "react"

export function useLadder(clubId, ladderId) {
    const [players, setPlayers] = useState([])
    const [ladderInfo, setLadderInfo] = useState(null)
    const [ruleset, setRuleset] = useState(null)
    const [loading, setLoading] = useState(true)

    useEffect(() => {
        if (!clubId || !ladderId) return;

        async function fetchData() {
            setLoading(true);

            // 1. Fetch Players (Safely)
            try {
                const pRes = await fetch(`/api/clubs/${clubId}/ladders/${ladderId}`);
                if (pRes.ok) {
                    setPlayers(await pRes.json());
                }
            } catch (err) { console.error("Error fetching players:", err); }

            let currentLadder = null;
            try {
                const lRes = await fetch(`/api/clubs/${clubId}/ladders`);
                if (lRes.ok) {
                    const rawData = await lRes.json();
                    console.log("RAW LADDERS DATA:", rawData); // Let's see exactly what the backend sent!

                    // The Fix: Safely get the array, whether it's [...] or { ladders: [...] }
                    const laddersArray = Array.isArray(rawData) ? rawData : (rawData.ladders || []);

                    currentLadder = laddersArray.find(l => l.id === parseInt(ladderId));
                    setLadderInfo(currentLadder);
                    console.log("Current Ladder Data:", currentLadder);
                }
            } catch (err) { console.error("Error fetching ladder info:", err); }

            // 3. Fetch Rulesets ONLY if the ladder has a ruleset_id attached
            if (currentLadder && currentLadder.ruleset_id) {
                try {
                    const rRes = await fetch(`/api/rulesets`);
                    if (rRes.ok) {
                        const rulesetsData = await rRes.json();
                        const matchingRuleset = rulesetsData.find(rs => rs.id === currentLadder.ruleset_id);
                        setRuleset(matchingRuleset);
                        console.log("Matched Ruleset Data:", matchingRuleset); // DEBUG LOG
                    }
                } catch (err) { console.error("Error fetching rulesets:", err); }
            } else {
                console.log("Notice: This ladder has no ruleset_id attached."); // DEBUG LOG
            }

            setLoading(false);
        }

        fetchData();
    }, [clubId, ladderId]);

    return { players, ladderInfo, ruleset, loading };
}