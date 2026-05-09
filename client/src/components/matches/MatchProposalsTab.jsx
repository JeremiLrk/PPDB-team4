import React, { useState } from "react";
import animationStyles from "@/style/common/Animation.module.css";
import buttonStyles from "@/style/common/Buttons.module.css";
import panelStyles from "@/style/common/Panel.module.css";
import formStyles from "@/style/common/Forms.module.css";
import { useMatchProposals } from "@/hooks/useMatchProposals.js";
import MatchProposalList from "@/components/matches/MatchProposalList.jsx";
import { useLangContext } from "@/context/useLangContext.jsx";
import { usePageTexts } from "@/hooks/common/usePageTexts.js";
import { useTeams } from "@/hooks/teams/useTeams.js";
import CreateMatchButton from "@/components/matches/CreateMatchButton.jsx";

export default function MatchProposalsTab() {
    const { lang } = useLangContext();
    const texts = usePageTexts("matches", lang);
    const dashboardTexts = usePageTexts("dashboard", lang);
    
    const {
        proposals,
        loading,
        error,
        submitting,
        load,
        setProposalStatus,
    } = useMatchProposals();

    const {
        teams: managedTeams,
        loading: managedLoading,
    } = useTeams({ endpoint: "/api/teams/my" });

    // --- Scoring State ---
    const [reportingMatchId, setReportingMatchId] = useState(null);
    const [isSubmittingScore, setIsSubmittingScore] = useState(false);
    const [scores, setScores] = useState({ s1: "", s2: "" });

    const handleOpenScoring = (matchId) => {
        setReportingMatchId(matchId);
    };

    const submitScore = async (e) => {
        e.preventDefault();
        setIsSubmittingScore(true);
        try {
            const res = await fetch(`/api/matches/${reportingMatchId}/score`, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({
                    score_team1: parseInt(scores.s1),
                    score_team2: parseInt(scores.s2)
                }),
                credentials: "include",
            });
            const data = await res.json();
            if (!res.ok) throw new Error(data.message);

            alert(texts.score_success || "Score recorded!");
            setReportingMatchId(null);
            setScores({ s1: "", s2: "" });
            load(); 
        } catch (err) {
            alert(err.message);
        } finally {
            setIsSubmittingScore(false);
        }
    };

    return (
        <article className={`${panelStyles.panel} ${animationStyles.contentFade}`}>
            <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: "1rem" }}>
                <h3 className={panelStyles.panelTitle} style={{ margin: 0 }}>
                    {texts.title || "Weekly Match Proposals"}
                    <span className={panelStyles.panelCounter} style={{ marginLeft: "0.6rem" }}>
                        {proposals.length}
                    </span>
                </h3>
                <div style={{ display: "flex", gap: "0.5rem" }}>
                    <button className={buttonStyles.primaryButton} onClick={load} disabled={loading}>
                        {texts.refresh || "Refresh"}
                    </button>
                    {!managedLoading && <CreateMatchButton managedTeams={managedTeams} onCreated={load} />}
                </div>
            </div>

            {/* Inline Scoring Form */}
            {reportingMatchId && (
                <div className={panelStyles.panel} style={{ background: "rgba(255,255,255,0.05)", marginBottom: "1rem" }}>
                    <form onSubmit={submitScore} style={{ display: "flex", alignItems: "center", gap: "1rem" }}>
                        <input 
                            type="number" placeholder="0" className={formStyles.formInput} style={{ width: "60px" }}
                            value={scores.s1} onChange={e => setScores({...scores, s1: e.target.value})} required
                        />
                        <span>-</span>
                        <input 
                            type="number" placeholder="0" className={formStyles.formInput} style={{ width: "60px" }}
                            value={scores.s2} onChange={e => setScores({...scores, s2: e.target.value})} required
                        />
                        <button type="submit" className={buttonStyles.primaryButton} disabled={isSubmittingScore}>
                            {isSubmittingScore ? "..." : texts.confirm || "Submit"}
                        </button>
                        <button type="button" className={buttonStyles.secondaryButton} onClick={() => setReportingMatchId(null)}>
                            {texts.cancel || "Cancel"}
                        </button>
                    </form>
                </div>
            )}

            <MatchProposalList
                proposals={proposals}
                loading={loading}
                error={error}
                submitting={submitting}
                onReload={load}
                onStatusChange={setProposalStatus}
                onReportScore={handleOpenScoring} // CRITICAL: This passes the trigger down
                texts={texts}
                statusTexts={dashboardTexts}
            />
        </article>
    );
}