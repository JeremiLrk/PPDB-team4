import { useParams, useNavigate } from "react-router-dom"
import { useLadder } from "@/hooks/useLadder"

function Ladder() {
    const { clubId, ladderId } = useParams()
    const navigate = useNavigate()

    // Grab our new ruleset and ladderInfo from the hook
    const { players, ladderInfo, ruleset, loading } = useLadder(clubId, ladderId)

    return (
        <div className="mx-auto max-w-4xl">

            {/* Header */}
            <div className="mb-10 flex items-start justify-between">
                <div>
                    <h1 className="text-3xl font-semibold">
                        {/* Show the actual ladder name if we have it! */}
                        {ladderInfo ? ladderInfo.name : "Ladder Rankings"}
                    </h1>
                    {ladderInfo && ladderInfo.description && (
                        <p className="mt-2 text-slate-400">{ladderInfo.description}</p>
                    )}
                </div>

                <button
                    onClick={() => navigate(`/clubs/${clubId}`)}
                    className="flex items-center gap-2 text-sm text-slate-400 hover:text-white transition mt-2"
                >
                    <span className="text-lg"></span>
                    Back to club
                </button>
            </div>

            {/* NEW: Match Rules Display Box */}
            {!loading && ruleset && (
                <div className="mb-8 rounded-xl border border-indigo-500/30 bg-indigo-500/10 p-5">
                    <h3 className="mb-3 flex items-center gap-2 text-lg font-medium text-indigo-400">
                        <span>📜</span> Match Rules: {ruleset.name}
                    </h3>
                    {ruleset.rules && ruleset.rules.length > 0 ? (
                        <ul className="list-inside list-disc space-y-1 text-sm text-indigo-100/80">
                            {ruleset.rules.map(rule => (
                                <li key={rule.id}>{rule.content}</li>
                            ))}
                        </ul>
                    ) : (
                        <p className="text-sm text-indigo-100/60">No specific rules added to this set.</p>
                    )}
                </div>
            )}

            {/* Ladder Rankings Table */}
            <div className="rounded-2xl border border-white/10 bg-white/5 overflow-hidden">

                {loading && (
                    <p className="p-6 text-slate-400">Loading ladder...</p>
                )}

                {!loading && players.length === 0 && (
                    <p className="p-6 text-slate-400">No players in this ladder yet.</p>
                )}

                {!loading && players.length > 0 && (
                    <table className="w-full">
                        <thead className="border-b border-white/10 text-slate-400 text-sm">
                        <tr>
                            <th className="p-4 text-left">Rank</th>
                            <th className="p-4 text-left">Player</th>
                            <th className="p-4 text-left">Rating</th>
                        </tr>
                        </thead>

                        <tbody>
                        {players.map((player, index) => (
                            <tr
                                key={player.id}
                                className="border-b border-white/5 hover:bg-white/5 transition"
                            >
                                <td className="p-4 font-semibold">
                                    #{index + 1}
                                </td>

                                <td className="p-4">
                                    {player.name}
                                </td>

                                <td className="p-4">
                                    {player.rating}
                                </td>
                            </tr>
                        ))}
                        </tbody>
                    </table>
                )}

            </div>

        </div>
    )
}

export default Ladder