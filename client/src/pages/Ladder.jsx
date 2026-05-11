import { useState } from "react";
import { useParams, useNavigate } from "react-router-dom";
import { useLadder, useLadderPlayers } from "@/hooks/useLadder";
import { useLangContext } from "@/context/useLangContext.jsx";
import { usePageTexts } from "@/hooks/common/usePageTexts.js";

const FORMAT_LABELS = {
    best_of_3:      "Best of 3 sets",
    timed:          "Op tijd",
    pro_set:        "Pro Set",
    full_set:       "Volledige derde set",
    super_tiebreak: "Super Tiebreak (tot 10 punten)",
    advantage:      "Klassiek (Voordeel)",
    golden_point:   "Golden Point (No-Ad)",
    singles:        "Enkelspel (1v1)",
    doubles:        "Dubbelspel (2v2)",
};

function label(key) {
    return FORMAT_LABELS[key] ?? key;
}

function RulesetModal({ ruleset, onClose }) {
    const rows = [];

    const matchFormatText = ruleset.matchFormat === "timed"
        ? `${label("timed")} – ${ruleset.timedDurationMinutes} minuten`
        : ruleset.matchFormat === "pro_set"
            ? `${label("pro_set")} tot ${ruleset.proSetGames} games`
            : label(ruleset.matchFormat);

    rows.push({ label: "Wedstrijdformaat",  value: matchFormatText });

    if (ruleset.matchFormat === "best_of_3") {
        rows.push({ label: "Derde set",     value: label(ruleset.thirdSetFormat) });
    }

    rows.push({ label: "40-40 (Deuce)",     value: label(ruleset.deuceRule) });
    rows.push({ label: "Spelvorm",          value: label(ruleset.gameFormat) });

    return (
        <div
            className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm"
            onClick={onClose}
        >
            <div
                className="relative w-full max-w-sm mx-4 rounded-2xl border border-white/10 bg-slate-900 p-6 shadow-2xl"
                onClick={e => e.stopPropagation()}
            >
                <button
                    onClick={onClose}
                    className="absolute top-4 right-4 text-slate-500 hover:text-white transition text-lg leading-none"
                    aria-label="Sluiten"
                >
                    ✕
                </button>

                <h2 className="text-lg font-semibold text-white mb-1">{ruleset.name}</h2>
                {ruleset.description && (
                    <p className="text-sm text-slate-400 mb-4">{ruleset.description}</p>
                )}

                <ul className="divide-y divide-white/5">
                    {rows.map(row => (
                        <li key={row.label} className="flex justify-between py-2.5 text-sm">
                            <span className="text-slate-400">{row.label}</span>
                            <span className="text-white font-medium text-right ml-4">{row.value}</span>
                        </li>
                    ))}
                </ul>
            </div>
        </div>
    );
}

function topOf(players, key) {
    if (!players.length) return null;
    return players.reduce((best, p) => ((p[key] ?? 0) > (best[key] ?? 0) ? p : best), players[0]);
}

function AchievementCard({ icon, label, name, value, unit }) {
    if (!name || value === 0) return null;
    return (
        <div className="flex flex-col gap-1 rounded-xl border border-white/10 bg-white/5 p-4">
            <span className="text-xl">{icon}</span>
            <p className="text-xs text-slate-500 uppercase tracking-wider mt-1">{label}</p>
            <p className="text-sm font-semibold text-slate-200 truncate">{name}</p>
            <p className="text-2xl font-bold text-white">{value} <span className="text-sm font-normal text-slate-400">{unit}</span></p>
        </div>
    );
}

function TopAchievements({ players }) {
    const mostWins     = topOf(players, "wins");
    const bestStreak   = topOf(players, "best_win_streak");
    const bestRank1    = topOf(players, "best_rank1_streak");

    const cards = [
        { icon: "🏆", label: "Most wins",        name: mostWins?.name,   value: mostWins?.wins ?? 0,                unit: "wins" },
        { icon: "🔥", label: "Best win streak",  name: bestStreak?.name, value: bestStreak?.best_win_streak ?? 0,  unit: "in a row" },
        { icon: "👑", label: "Longest #1 reign", name: bestRank1?.name,  value: bestRank1?.best_rank1_streak ?? 0, unit: "matches" },
    ].filter(c => c.value > 0);

    if (!cards.length) return null;

    return (
        <div className="mt-8">
            <h2 className="text-lg font-semibold text-slate-200 mb-3">Top Achievements</h2>
            <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
                {cards.map(c => <AchievementCard key={c.label} {...c} />)}
            </div>
        </div>
    );
}

function Ladder() {
    const { clubId, ladderId } = useParams();
    const navigate = useNavigate();
    const { lang } = useLangContext();
    const texts = usePageTexts("ladder", lang);

    const { players, loading: p_loading } = useLadderPlayers(clubId, ladderId);
    const { ladder, loading: l_loading }  = useLadder(clubId, ladderId);

    const [showRuleset, setShowRuleset] = useState(false);

    return (
        <div className="mx-auto max-w-4xl p-6">

            {/* Header & Navigation */}
            <div className="mb-8">
                <button
                    onClick={() => navigate(`/clubs/${clubId}`)}
                    className="mb-4 flex items-center gap-2 text-sm text-slate-400 hover:text-white transition"
                >
                    ← {texts.back_to_club || "Back to club"}
                </button>

                {l_loading ? (
                    <div className="h-10 w-48 animate-pulse rounded bg-white/10" />
                ) : (
                    <div className="flex flex-col gap-2">
                        <div className="flex items-center gap-3">
                            <h1 className="text-3xl font-semibold">
                                {ladder?.name || (texts.ladder_rankings || "Ladder Rankings")}
                            </h1>
                            {ladder?.sport_type && (
                                <span className="rounded-full bg-blue-500/10 px-3 py-1 text-xs font-medium text-blue-400 border border-blue-500/20">
                                    {ladder.sport_type}
                                </span>
                            )}
                        </div>

                        {ladder?.description && (
                            <p className="text-slate-400 max-w-2xl">{ladder.description}</p>
                        )}

                        <div className="flex gap-4 mt-2 text-xs text-slate-500">
                            {ladder?.ruleset && (
                                <span>
                                    {texts.ruleset_label || "Ruleset"}:{" "}
                                    <button
                                        onClick={() => setShowRuleset(true)}
                                        className="text-blue-400 hover:text-blue-300 hover:underline transition cursor-pointer"
                                    >
                                        {ladder.ruleset.name}
                                    </button>
                                </span>
                            )}
                            {ladder?.rating_function && (
                                <span>
                                    {texts.system_label || "System"}:{" "}
                                    <span className="text-slate-300">{ladder.rating_function}</span>
                                </span>
                            )}
                        </div>
                    </div>
                )}
            </div>

            {/* Ladder Table */}
            <div className="rounded-2xl border border-white/10 bg-white/5 overflow-hidden">
                {p_loading ? (
                    <p className="p-6 text-slate-400">{texts.loading_rankings || "Loading rankings..."}</p>
                ) : players.length === 0 ? (
                    <p className="p-6 text-slate-400 text-center">{texts.no_players || "No players in this ladder yet."}</p>
                ) : (
                    <table className="w-full text-left">
                        <thead className="border-b border-white/10 text-slate-400 text-sm uppercase tracking-wider">
                            <tr>
                                <th className="p-4 font-medium">{texts.rank || "Rank"}</th>
                                <th className="p-4 font-medium">{texts.player || "Player"}</th>
                                <th className="p-4 font-medium">{texts.rating || "Rating"}</th>
                                <th className="p-4 font-medium hidden sm:table-cell">W</th>
                                <th className="p-4 font-medium hidden sm:table-cell">Streak</th>
                            </tr>
                        </thead>
                        <tbody className="divide-y divide-white/5">
                            {players.map((player, index) => (
                                <tr key={player.id} className="hover:bg-white/[0.02] transition">
                                    <td className="p-4">
                                        <span className={`
                                            inline-flex h-8 w-8 items-center justify-center rounded-full text-sm font-bold
                                            ${index === 0 ? "bg-yellow-500/20 text-yellow-500" :
                                              index === 1 ? "bg-slate-300/20 text-slate-300" :
                                              index === 2 ? "bg-orange-500/20 text-orange-500" :
                                              "text-slate-400"}
                                        `}>
                                            {index + 1}
                                        </span>
                                    </td>
                                    <td className="p-4 font-medium text-slate-200">{player.name}</td>
                                    <td className="p-4 font-mono text-blue-400">{player.rating}</td>
                                    <td className="p-4 text-slate-300 hidden sm:table-cell">{player.wins ?? 0}</td>
                                    <td className="p-4 hidden sm:table-cell">
                                        {(player.win_streak ?? 0) > 0 ? (
                                            <span className="text-green-400 font-semibold">🔥 {player.win_streak}</span>
                                        ) : (
                                            <span className="text-slate-500">—</span>
                                        )}
                                    </td>
                                </tr>
                            ))}
                        </tbody>
                    </table>
                )}
            </div>

            {/* Top Achievements */}
            {!p_loading && players.length > 0 && (
                <TopAchievements players={players} />
            )}

            {showRuleset && ladder?.ruleset && (
                <RulesetModal
                    ruleset={ladder.ruleset}
                    onClose={() => setShowRuleset(false)}
                />
            )}
        </div>
    );
}

export default Ladder;
