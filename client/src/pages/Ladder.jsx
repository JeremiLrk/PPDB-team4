// Page container for Ladder.

import { useState } from "react";
import { useParams, useNavigate } from "react-router-dom";
import { useLadder, useLadderPlayers } from "@/hooks/useLadder";
import { useLangContext } from "@/context/useLangContext.jsx";
import { usePageTexts } from "@/hooks/common/usePageTexts.js";
import { useThemeContext } from "@/context/useThemeContext.jsx";

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
    /*
     Maps raw ruleset values to readable labels.
    */
    return FORMAT_LABELS[key] ?? key;
}

function RulesetModal({ ruleset, onClose, isLight }) {
    /*
     Renders the ruleset details overlay for one ladder.
    */
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
            className={`fixed inset-0 z-50 flex items-center justify-center backdrop-blur-sm ${
                isLight ? "bg-black/30" : "bg-black/60"
            }`}
            onClick={onClose}
        >
            <div
                className={`relative w-full max-w-sm mx-4 rounded-2xl p-6 shadow-2xl ${
                    isLight
                        ? "border border-slate-200 bg-white"
                        : "border border-white/10 bg-slate-900"
                }`}
                onClick={e => e.stopPropagation()}
            >
                <button
                    onClick={onClose}
                    className={`absolute top-4 right-4 transition text-lg leading-none ${
                        isLight ? "text-slate-400 hover:text-slate-900" : "text-slate-500 hover:text-white"
                    }`}
                    aria-label="Sluiten"
                >
                    ✕
                </button>

                <h2 className={`text-lg font-semibold mb-1 ${isLight ? "text-slate-900" : "text-white"}`}>
                    {ruleset.name}
                </h2>
                {ruleset.description && (
                    <p className={`text-sm mb-4 ${isLight ? "text-slate-600" : "text-slate-400"}`}>
                        {ruleset.description}
                    </p>
                )}

                <ul className={`divide-y ${isLight ? "divide-slate-100" : "divide-white/5"}`}>
                    {rows.map(row => (
                        <li key={row.label} className="flex justify-between py-2.5 text-sm">
                            <span className={isLight ? "text-slate-500" : "text-slate-400"}>{row.label}</span>
                            <span className={`font-medium text-right ml-4 ${isLight ? "text-slate-900" : "text-white"}`}>
                                {row.value}
                            </span>
                        </li>
                    ))}
                </ul>
            </div>
        </div>
    );
}

function topOf(players, key) {
    /*
     Picks the player with the highest value for one stat.
    */
    if (!players.length) return null;
    return players.reduce((best, p) => ((p[key] ?? 0) > (best[key] ?? 0) ? p : best), players[0]);
}

function AchievementCard({ icon, label, name, value, unit, isLight }) {
    /*
     Renders one ladder achievement card when a stat exists.
    */
    if (!name || value === 0) return null;
    return (
        <div className={`flex flex-col gap-1 rounded-xl p-4 ${
            isLight
                ? "border border-slate-200 bg-white shadow-sm"
                : "border border-white/10 bg-white/5"
        }`}>
            <span className="text-xl">{icon}</span>
            <p className={`text-xs uppercase tracking-wider mt-1 ${isLight ? "text-slate-500" : "text-slate-500"}`}>
                {label}
            </p>
            <p className={`text-sm font-semibold truncate ${isLight ? "text-slate-700" : "text-slate-200"}`}>
                {name}
            </p>
            <p className={`text-2xl font-bold ${isLight ? "text-slate-900" : "text-white"}`}>
                {value}{" "}
                <span className={`text-sm font-normal ${isLight ? "text-slate-500" : "text-slate-400"}`}>
                    {unit}
                </span>
            </p>
        </div>
    );
}

function TopAchievements({ players, isLight }) {
    /*
     Renders the ladder achievement summary strip.
    */
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
            <h2 className={`text-lg font-semibold mb-3 ${isLight ? "text-slate-700" : "text-slate-200"}`}>
                Top Achievements
            </h2>
            <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
                {cards.map(c => <AchievementCard key={c.label} {...c} isLight={isLight} />)}
            </div>
        </div>
    );
}

function Ladder() {
    const { clubId, ladderId } = useParams();
    const navigate = useNavigate();
    const { lang } = useLangContext();
    const texts = usePageTexts("ladder", lang);
    const { theme } = useThemeContext();
    const isLight = theme === "light";

    const { players, loading: p_loading } = useLadderPlayers(clubId, ladderId);
    const { ladder, loading: l_loading }  = useLadder(clubId, ladderId);
    /*
     Tracks whether the ruleset details overlay is open.
    */
    const [showRuleset, setShowRuleset] = useState(false);

    return (
        <div className="mx-auto max-w-4xl px-4 py-6 sm:px-6">

            {/* Header & Navigation */}
            <div className="mb-8">
                <button
                    onClick={() => navigate(`/clubs/${clubId}`)}
                    className={`mb-4 flex items-center gap-2 text-sm transition ${
                        isLight
                            ? "text-slate-500 hover:text-slate-900"
                            : "text-slate-400 hover:text-white"
                    }`}
                >
                    ← {texts.back_to_club || "Back to club"}
                </button>

                {l_loading ? (
                    <div className={`h-10 w-48 animate-pulse rounded ${isLight ? "bg-slate-200" : "bg-white/10"}`} />
                ) : (
                    <div className="flex flex-col gap-2">
                        <div className="flex items-center gap-3">
                            <h1 className="text-3xl font-semibold">
                                {ladder?.name || (texts.ladder_rankings || "Ladder Rankings")}
                            </h1>
                            {ladder?.sport_type && (
                                <span className={`rounded-full px-3 py-1 text-xs font-medium border ${
                                    isLight
                                        ? "bg-blue-50 text-blue-700 border-blue-200"
                                        : "bg-blue-500/10 text-blue-400 border-blue-500/20"
                                }`}>
                                    {ladder.sport_type}
                                </span>
                            )}
                        </div>

                        {ladder?.description && (
                            <p className={isLight ? "text-slate-600" : "text-slate-400"}>
                                {ladder.description}
                            </p>
                        )}

                        <div className={`flex gap-4 mt-2 text-xs ${isLight ? "text-slate-500" : "text-slate-500"}`}>
                            {ladder?.ruleset && (
                                <span>
                                    {texts.ruleset_label || "Ruleset"}:{" "}
                                    <button
                                        onClick={() => setShowRuleset(true)}
                                        className={`hover:underline transition cursor-pointer ${
                                            isLight ? "text-blue-600 hover:text-blue-800" : "text-blue-400 hover:text-blue-300"
                                        }`}
                                    >
                                        {ladder.ruleset.name}
                                    </button>
                                </span>
                            )}
                            {ladder?.rating_function && (
                                <span>
                                    {texts.system_label || "System"}:{" "}
                                    <span className={isLight ? "text-slate-700" : "text-slate-300"}>
                                        {ladder.rating_function}
                                    </span>
                                </span>
                            )}
                        </div>
                    </div>
                )}
            </div>

            {/* Ladder Table */}
            <div className={`rounded-2xl overflow-hidden ${
                isLight
                    ? "border border-slate-200 bg-white shadow-sm"
                    : "border border-white/10 bg-white/5"
            }`}>
                {p_loading ? (
                    <p className={`p-6 ${isLight ? "text-slate-600" : "text-slate-400"}`}>
                        {texts.loading_rankings || "Loading rankings..."}
                    </p>
                ) : players.length === 0 ? (
                    <p className={`p-6 text-center ${isLight ? "text-slate-600" : "text-slate-400"}`}>
                        {texts.no_players || "No players in this ladder yet."}
                    </p>
                ) : (
                    <table className="w-full text-left">
                        <thead className={`text-xs uppercase tracking-wider border-b ${
                            isLight
                                ? "border-slate-200 text-slate-500"
                                : "border-white/10 text-slate-400"
                        }`}>
                            <tr>
                                <th className="p-4 font-medium">{texts.rank || "Rank"}</th>
                                <th className="p-4 font-medium">{texts.player || "Player"}</th>
                                <th className="p-4 font-medium">{texts.rating || "Rating"}</th>
                                <th className="p-4 font-medium hidden sm:table-cell">W</th>
                                <th className="p-4 font-medium hidden sm:table-cell">Streak</th>
                            </tr>
                        </thead>
                        <tbody className={`divide-y ${isLight ? "divide-slate-100" : "divide-white/5"}`}>
                            {players.map((player, index) => (
                                <tr key={player.id} className={`transition ${isLight ? "hover:bg-slate-50" : "hover:bg-white/[0.02]"}`}>
                                    <td className="p-4">
                                        <span className={`
                                            inline-flex h-8 w-8 items-center justify-center rounded-full text-sm font-bold
                                            ${index === 0 ? "bg-yellow-500/20 text-yellow-600" :
                                              index === 1 ? (isLight ? "bg-slate-200/60 text-slate-600" : "bg-slate-300/20 text-slate-300") :
                                              index === 2 ? "bg-orange-500/20 text-orange-600" :
                                              (isLight ? "text-slate-500" : "text-slate-400")}
                                        `}>
                                            {index + 1}
                                        </span>
                                    </td>
                                    <td className={`p-4 font-medium ${isLight ? "text-slate-800" : "text-slate-200"}`}>
                                        {player.name}
                                    </td>
                                    <td className={`p-4 font-mono ${isLight ? "text-blue-600" : "text-blue-400"}`}>
                                        {player.rating}
                                    </td>
                                    <td className={`p-4 hidden sm:table-cell ${isLight ? "text-slate-700" : "text-slate-300"}`}>
                                        {player.wins ?? 0}
                                    </td>
                                    <td className="p-4 hidden sm:table-cell">
                                        {(player.win_streak ?? 0) > 0 ? (
                                            <span className={`font-semibold ${isLight ? "text-green-700" : "text-green-400"}`}>
                                                🔥 {player.win_streak}
                                            </span>
                                        ) : (
                                            <span className={isLight ? "text-slate-400" : "text-slate-500"}>—</span>
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
                <TopAchievements players={players} isLight={isLight} />
            )}

            {showRuleset && ladder?.ruleset && (
                <RulesetModal
                    ruleset={ladder.ruleset}
                    onClose={() => setShowRuleset(false)}
                    isLight={isLight}
                />
            )}
        </div>
    );
}

export default Ladder;
