import { useParams, useNavigate } from "react-router-dom";
import { useLadder, useLadderPlayers } from "@/hooks/useLadder";

function Ladder() {
    const { clubId, ladderId } = useParams();
    const navigate = useNavigate();

    // Note: ensure these variable names match what the hook returns 
    // (In your previous hook they were just called 'loading')
    const { players, loading: p_loading } = useLadderPlayers(clubId, ladderId);
    const { ladder, loading: l_loading } = useLadder(clubId, ladderId);

    return (
        <div className="mx-auto max-w-4xl p-6">

            {/* Header & Navigation */}
            <div className="mb-8">
                <button
                    onClick={() => navigate(`/clubs/${clubId}`)}
                    className="mb-4 flex items-center gap-2 text-sm text-slate-400 hover:text-white transition"
                >
                    ← Back to club
                </button>

                {l_loading ? (
                    <div className="h-10 w-48 animate-pulse rounded bg-white/10" />
                ) : (
                    <div className="flex flex-col gap-2">
                        <div className="flex items-center gap-3">
                            <h1 className="text-3xl font-semibold">
                                {ladder?.name || "Ladder Rankings"}
                            </h1>
                            {ladder?.sport_type && (
                                <span className="rounded-full bg-blue-500/10 px-3 py-1 text-xs font-medium text-blue-400 border border-blue-500/20">
                                    {ladder.sport_type}
                                </span>
                            )}
                        </div>
                        
                        {ladder?.description && (
                            <p className="text-slate-400 max-w-2xl">
                                {ladder.description}
                            </p>
                        )}
                        
                        <div className="flex gap-4 mt-2 text-xs text-slate-500">
                             {ladder?.ruleset && (
                                <span>Ruleset: <span className="text-slate-300">{ladder.ruleset}</span></span>
                             )}
                             {ladder?.rating_function && (
                                <span>System: <span className="text-slate-300">{ladder.rating_function}</span></span>
                             )}
                        </div>
                    </div>
                )}
            </div>

            {/* Ladder Table */}
            <div className="rounded-2xl border border-white/10 bg-white/5 overflow-hidden">
                {p_loading ? (
                    <p className="p-6 text-slate-400">Loading rankings...</p>
                ) : players.length === 0 ? (
                    <p className="p-6 text-slate-400 text-center">No players in this ladder yet.</p>
                ) : (
                    <table className="w-full text-left">
                        <thead className="border-b border-white/10 text-slate-400 text-sm uppercase tracking-wider">
                            <tr>
                                <th className="p-4 font-medium">Rank</th>
                                <th className="p-4 font-medium">Player</th>
                                <th className="p-4 font-medium">Rating</th>
                            </tr>
                        </thead>

                        <tbody className="divide-y divide-white/5">
                            {players.map((player, index) => (
                                <tr
                                    key={player.id}
                                    className="hover:bg-white/[0.02] transition"
                                >
                                    <td className="p-4">
                                        <span className={`
                                            inline-flex h-8 w-8 items-center justify-center rounded-full text-sm font-bold
                                            ${index === 0 ? 'bg-yellow-500/20 text-yellow-500' : 
                                              index === 1 ? 'bg-slate-300/20 text-slate-300' : 
                                              index === 2 ? 'bg-orange-500/20 text-orange-500' : 
                                              'text-slate-400'}
                                        `}>
                                            {index + 1}
                                        </span>
                                    </td>

                                    <td className="p-4 font-medium text-slate-200">
                                        {player.name}
                                    </td>

                                    <td className="p-4 font-mono text-blue-400">
                                        {player.rating}
                                    </td>
                                </tr>
                            ))}
                        </tbody>
                    </table>
                )}
            </div>
        </div>
    );
}

export default Ladder;