import { useParams, useNavigate } from "react-router-dom"
import { useLadder } from "@/hooks/useLadder"

function Ladder() {
    const { clubId, ladderId } = useParams()
    const navigate = useNavigate()

    const { players, loading } = useLadder(clubId, ladderId)

    return (
        <div className="mx-auto max-w-4xl">

            {/* Header */}
            <div className="mb-10 flex items-center justify-between">
                <h1 className="text-3xl font-semibold">
                    Ladder Rankings
                </h1>

            <button
                onClick={() => navigate(`/clubs/${clubId}`)}
                className="flex items-center gap-2 text-sm text-slate-400 hover:text-white transition"
            >
                <span className="text-lg"></span>
                Back to club
            </button>
            </div>

            {/* Ladder */}
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