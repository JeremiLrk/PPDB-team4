// --- HELPER FUNCTION FOR DATA NORMALIZATION ---
function readField(source, ...keys) {
    /*
     Reads the first available field from a payload shape.
    */
    for (const key of keys) {
        if (source?.[key] !== undefined && source?.[key] !== null) {
            return source[key];
        }
    }
    return undefined;
}

function normalizePercentages(raw = {}) {
    /*
     Normalizes the win percentages payload shape.
    */
    return {
        team1WinPercentage: readField(raw, "team1WinPercentage", "team1_win_percentage") ?? 50.0,
        team2WinPercentage: readField(raw, "team2WinPercentage", "team2_win_percentage") ?? 50.0,
    };
}

/**
 * Fetches the win percentages for an accepted match proposal.
 * 
 * @param {number} matchId - The ID of the match proposal.
 * @returns {Promise<{team1WinPercentage: number, team2WinPercentage: number} | null>}
 */
export async function fetchMatchPercentages(matchId) {
    if (!matchId) return null;

    try {
        const response = await fetch(`/api/matches/${matchId}/percentages`, {
            method: 'GET',
            headers: {
                'Content-Type': 'application/json',
            }
        });

        if (response.status === 409) {
            const errorData = await response.json();
            console.warn(`Percentages unavailable: ${errorData.description}`);
            return null;
        }

        if (!response.ok) {
            throw new Error(`HTTP error! Status: ${response.status}`);
        }

        const payload = await response.json();
        return normalizePercentages(payload);

    } catch (error) {
        console.error(`Failed to fetch percentages for match ${matchId}:`, error);
        return null;
    }
}