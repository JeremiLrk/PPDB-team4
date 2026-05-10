import { useMemo, useState } from "react";
import animationStyles from "@/style/common/Animation.module.css";
import buttonStyles from "@/style/common/Buttons.module.css";
import panelStyles from "@/style/common/Panel.module.css";
import styles from "@/style/matches/MatchProposalsTab.module.css";
import { useMatchProposals } from "@/hooks/useMatchProposals.js";
import MatchProposalList from "@/components/matches/MatchProposalList.jsx";
import { useLangContext } from "@/context/useLangContext.jsx";
import { usePageTexts } from "@/hooks/common/usePageTexts.js";
import { useCurrentUserContext } from "@/context/useCurrentUserContext.jsx";
import { useTeams } from "@/hooks/teams/useTeams.js";
import CreateMatchButton from "@/components/matches/CreateMatchButton.jsx";

function toIdSet(values) {
    return new Set(
        (Array.isArray(values) ? values : [])
            .map((value) => Number(value))
            .filter(Number.isFinite),
    );
}

function proposalIsManaged(proposal, currentUser) {
    if ((currentUser?.role || "").toLowerCase() === "administrator") {
        return true;
    }

    const managedTeamIds = toIdSet(currentUser?.managedTeamIds);
    const managedClubIds = toIdSet(currentUser?.clubIds);

    return (
        managedTeamIds.has(Number(proposal.team1Id))
        || managedTeamIds.has(Number(proposal.team2Id))
        || managedClubIds.has(Number(proposal.team1ClubId))
        || managedClubIds.has(Number(proposal.team2ClubId))
    );
}

function proposalIsPlayer(proposal, currentUser) {
    const playerTeamIds = toIdSet(currentUser?.playerTeamIds);
    return (
        playerTeamIds.has(Number(proposal.team1Id))
        || playerTeamIds.has(Number(proposal.team2Id))
    );
}

function proposalCanUpdate(proposal, currentUser) {
    if ((currentUser?.role || "").toLowerCase() === "administrator") {
        return true;
    }

    if (Number(currentUser?.id) === Number(proposal.proposedByUserId)) {
        return true;
    }

    return proposalIsManaged(proposal, currentUser) || proposalIsPlayer(proposal, currentUser);
}

function SectionHeader({ title, subtitle, count }) {
    return (
        <div className={styles.sectionHeader}>
            <div className={styles.sectionHeaderText}>
                <p className={styles.sectionTitle}>{title}</p>
                <p className={styles.sectionSubtitle}>{subtitle}</p>
            </div>
            <span className={panelStyles.panelCounter}>{count}</span>
        </div>
    );
}

export default function MatchProposalsTab() {
    const { lang } = useLangContext();
    const texts = usePageTexts("matches", lang);
    const dashboardTexts = usePageTexts("dashboard", lang);
    const { currentUser, loadingUser } = useCurrentUserContext();
    const [showArchived, setShowArchived] = useState(false);
    const [reportingMatchId, setReportingMatchId] = useState(null);
    const [scoreValues, setScoreValues] = useState({ team1: "", team2: "" });
    const [scoreSubmitting, setScoreSubmitting] = useState(false);
    const {
        proposals,
        loading,
        error,
        submitting,
        load,
        setProposalStatus,
    } = useMatchProposals({ archived: showArchived });

    const {
        teams: managedTeams,
        loading: managedLoading,
    } = useTeams({ endpoint: "/api/teams/my" });

    const managedProposals = useMemo(
        () => proposals.filter((proposal) => proposalIsManaged(proposal, currentUser)),
        [currentUser, proposals],
    );
    const playerProposals = useMemo(
        () => proposals.filter((proposal) => proposalIsPlayer(proposal, currentUser)),
        [currentUser, proposals],
    );
    const canUpdateProposal = (proposal) => proposalCanUpdate(proposal, currentUser);
    const roleLoading = loadingUser && !currentUser;

    function handleMatchCreated() {
        void load();
    }

    function openScoring(matchId) {
        setReportingMatchId(matchId);
        setScoreValues({ team1: "", team2: "" });
    }

    async function submitScore(event, matchId = reportingMatchId) {
        event.preventDefault();

        const scoreTeam1 = Number.parseInt(scoreValues.team1, 10);
        const scoreTeam2 = Number.parseInt(scoreValues.team2, 10);
        if (!Number.isInteger(scoreTeam1) || !Number.isInteger(scoreTeam2) || scoreTeam1 < 0 || scoreTeam2 < 0) {
            return;
        }

        setScoreSubmitting(true);
        try {
            const response = await fetch(`/api/matches/${matchId}/score`, {
                method: "POST",
                credentials: "include",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({
                    score_team1: scoreTeam1,
                    score_team2: scoreTeam2,
                }),
            });
            const payload = await response.json().catch(() => ({}));
            if (!response.ok) {
                throw new Error(payload?.message || "Could not submit score.");
            }
            setReportingMatchId(null);
            setScoreValues({ team1: "", team2: "" });
            await load();
        } finally {
            setScoreSubmitting(false);
        }
    }

    const topLabel = texts.title || "Weekly Match Proposals";
    const managedTitle = texts.managed_matches || "Managed matches";
    const managedSubtitle = texts.managed_matches_subtitle || "Matches for teams and clubs you manage.";
    const playerTitle = texts.player_matches || "Player matches";
    const playerSubtitle = texts.player_matches_subtitle || "Matches that involve teams you play on.";
    const refreshLabel = texts.refresh || "Refresh";
    const showArchivedLabel = texts.show_archived || "Show archived";
    const showActiveLabel = texts.show_active || "Show active";
    const loadingLabel = texts.loading || "Match proposals loading...";
    const managedEmptyLabel = texts.no_managed_matches || "No managed match proposals yet.";
    const playerEmptyLabel = texts.no_player_matches || "No player match proposals yet.";

    return (
        <article className={`${panelStyles.panel} ${styles.page} ${animationStyles.contentFade}`}>
            <div className={styles.toolbar}>
                <div className={styles.toolbarCopy}>
                    <h3 className={styles.toolbarTitle}>
                        {topLabel}
                        <span className={panelStyles.panelCounter}>{proposals.length}</span>
                    </h3>
                </div>

                <div className={styles.toolbarActions}>
                    <button
                        className={buttonStyles.primaryButton}
                        type="button"
                        onClick={load}
                        disabled={loading}
                    >
                        {refreshLabel}
                    </button>

                    <button
                        className={buttonStyles.primaryButton}
                        type="button"
                        onClick={() => setShowArchived((current) => !current)}
                        disabled={loading}
                    >
                        {showArchived ? showActiveLabel : showArchivedLabel}
                    </button>

                    {!managedLoading ? (
                        <CreateMatchButton
                            managedTeams={managedTeams}
                            onCreated={handleMatchCreated}
                        />
                    ) : null}
                </div>
            </div>

            {error ? (
                <div className={styles.errorBlock}>
                    <p className={styles.error}>{error}</p>
                    <button
                        className={buttonStyles.primaryButton}
                        type="button"
                        onClick={load}
                    >
                        {texts.retry || "Retry"}
                    </button>
                </div>
            ) : null}

            {loading || roleLoading ? (
                <p className={styles.loading}>{loadingLabel}</p>
            ) : null}

            {!loading && !roleLoading && !error ? (
                <div className={styles.sections}>
                    <section className={styles.section}>
                        <SectionHeader
                            title={managedTitle}
                            subtitle={managedSubtitle}
                            count={managedProposals.length}
                        />
                        <MatchProposalList
                            proposals={managedProposals}
                            loading={false}
                            submitting={submitting}
                            onReload={load}
                            onStatusChange={setProposalStatus}
                            onReportScore={openScoring}
                            reportingMatchId={reportingMatchId}
                            scoreValues={scoreValues}
                            onScoreChange={(field, value) =>
                                setScoreValues((current) => ({ ...current, [field]: value }))
                            }
                            onScoreSubmit={submitScore}
                            onCancelScore={() => setReportingMatchId(null)}
                            scoreSubmitting={scoreSubmitting}
                            canUpdateProposal={canUpdateProposal}
                            texts={texts}
                            statusTexts={dashboardTexts}
                            emptyText={managedEmptyLabel}
                        />
                    </section>

                    <section className={styles.section}>
                        <SectionHeader
                            title={playerTitle}
                            subtitle={playerSubtitle}
                            count={playerProposals.length}
                        />
                        <MatchProposalList
                            proposals={playerProposals}
                            loading={false}
                            submitting={submitting}
                            onReload={load}
                            onStatusChange={setProposalStatus}
                            onReportScore={openScoring}
                            reportingMatchId={reportingMatchId}
                            scoreValues={scoreValues}
                            onScoreChange={(field, value) =>
                                setScoreValues((current) => ({ ...current, [field]: value }))
                            }
                            onScoreSubmit={submitScore}
                            onCancelScore={() => setReportingMatchId(null)}
                            scoreSubmitting={scoreSubmitting}
                            canUpdateProposal={canUpdateProposal}
                            texts={texts}
                            statusTexts={dashboardTexts}
                            emptyText={playerEmptyLabel}
                        />
                    </section>
                </div>
            ) : null}
        </article>
    );
}
