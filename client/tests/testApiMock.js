import { vi } from "vitest";

const PAGE_TEXTS = {
    base: {
        en: { net_rank: "NetRank", pending: "Pending", e404: "404 - Page Not Found" },
        nl: { net_rank: "NetRank", pending: "In behandeling", e404: "404 - Pagina niet gevonden" },
    },
    authorization: {
        en: {
            log_in: "Log in",
            register: "Register",
            email: "Email",
            password: "Password",
            placeholder_email: "Enter your email",
            placeholder_password: "Enter your password",
            no_account: "Don't have an account?",
            has_account: "Already have an account?",
            as_guest: "Continue as guest",
            create_account: "Create account",
            forgot_password: "Forgot password?",
        },
        nl: {
            log_in: "Inloggen",
            register: "Registreren",
            email: "E-mail",
            password: "Wachtwoord",
            placeholder_email: "Vul je e-mailadres in",
            placeholder_password: "Vul je wachtwoord in",
            no_account: "Heb je nog geen account?",
            has_account: "Heb je al een account?",
            as_guest: "Doorgaan als gast",
            create_account: "Account aanmaken",
            forgot_password: "Wachtwoord vergeten?",
        },
    },
    home: {
        en: { home: "Home", net_rank: "NetRank" },
        nl: { home: "Thuis", net_rank: "NetRank" },
    },
    ladder: {
        en: { ladder: "Ladder", join_ladder: "Join the Ladder" },
        nl: { ladder: "Ladder", join_ladder: "Doe mee aan de ladder" },
    },
    score: {
        en: { top_players: "Top Players", top_matches: "Top Matches" },
        nl: { top_players: "Topspelers", top_matches: "Topwedstrijden" },
    },
    landing: {
        en: { how_it_works: "How NetRank works", explore_clubs: "Explore clubs", open_dashboard: "Open dashboard" },
        nl: { how_it_works: "Hoe NetRank werkt", explore_clubs: "Verken clubs", open_dashboard: "Open dashboard" },
    },
    dashboard: {
        en: {
            tab_overview: "Overview",
            tab_search: "Search Clubs",
            tab_requests: "My Requests",
            tab_create_club: "Add your own club",
            search_by_name: "Search by club name",
            signed_in_as: "Signed in as",
        },
        nl: {
            tab_overview: "Overzicht",
            tab_search: "Zoek clubs",
            tab_requests: "Mijn aanvragen",
            tab_create_club: "Voeg je eigen club toe",
            search_by_name: "Zoek op clubnaam",
            signed_in_as: "Ingelogd als",
        },
    },
    club_home: {
        en: { loading_ladders: "Loading ladders...", loading_club: "Loading club...", log_in: "Log in" },
        nl: { loading_ladders: "Ladders laden...", loading_club: "Club laden...", log_in: "Inloggen" },
    },
};

function jsonResponse(data, status = 200) {
    return {
        ok: status >= 200 && status < 300,
        status,
        json: async () => data,
    };
}

export function mockApi(options = {}) {
    const {
        me = null,
        dashboardData = { roles: ["user"], clubs: [], pending_requests: { my_requests: [], my_club_creation_requests: [] } },
        clubs = [{ id: 1, name: "NetRank Club", description: "Mock data club", sport: "Padel", city: "Antwerp" }],
        club = { id: 1, name: "NetRank Club", description: "Mock data club", sport: "Padel", city: "Antwerp" },
        ladders = [{ id: 11, name: "Men's Singles" }, { id: 12, name: "U14 Singles" }],
        topPlayers = [{ id: 1, name: "Thomas", rating: 1290 }],
        teams = [{ id: 201, name: "NetRank Aces", clubId: 1, sportTypeId: 4 }],
        players = [],
    } = options;

    globalThis.fetch = vi.fn(async (input) => {
        const rawUrl = typeof input === "string" ? input : input.url;
        const method = (typeof input === "string" ? "GET" : input.method || "GET").toUpperCase();
        const url = new URL(rawUrl, "http://localhost");
        const path = url.pathname;
        const lang = url.searchParams.get("lang") || "en";

        if (path === "/api/health") return jsonResponse({ db_connected: true });
        if (path === "/api/me") {
            if (!me) return jsonResponse({ message: "Unauthorized" }, 401);
            return jsonResponse({ account: me });
        }
        if (path === "/api/me/dashboard") return jsonResponse(dashboardData);
        if (path === "/api/clubs") return jsonResponse({ clubs });
        if (path === `/api/clubs/${club.id}`) return jsonResponse({ club });
        if (path === `/api/clubs/${club.id}/ladders`) return jsonResponse(ladders);
        if (path === `/api/clubs/${club.id}/top-players`) return jsonResponse(topPlayers);
        if (path === "/api/teams" || path === "/api/teams/my-all") {
            return jsonResponse({ total: teams.length, from: 0, to: teams.length, teams });
        }

        const teamMatch = path.match(/^\/api\/teams\/(\d+)$/);
        if (teamMatch) {
            const teamId = Number(teamMatch[1]);
            const team = teams.find((item) => Number(item.id) === teamId);
            if (!team) return jsonResponse({ message: "Team not found." }, 404);
            return jsonResponse({ team });
        }

        const teamPlayersMatch = path.match(/^\/api\/teams\/(\d+)\/players$/);
        if (teamPlayersMatch) {
            return jsonResponse({ total: players.length, players });
        }

        if (path === "/api/logout" && method === "POST") {
            return jsonResponse({ message: "Successfully logged out." });
        }

        const pageMatch = path.match(/^\/api\/texts\/page\/([^/]+)$/);
        if (pageMatch) {
            const page = pageMatch[1];
            const localized = PAGE_TEXTS[page]?.[lang] || PAGE_TEXTS[page]?.en || {};
            return jsonResponse(localized);
        }

        return jsonResponse({ message: `Unexpected fetch in test: ${path}` }, 404);
    });
}
