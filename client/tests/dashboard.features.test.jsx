// Regression tests for dashboard.features.test.

import "@testing-library/jest-dom/vitest";
import React, { useState } from "react";
import { beforeEach, describe, expect, test, vi } from "vitest";
import { render, screen, waitFor, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { MemoryRouter } from "react-router-dom";

import Dashboard from "../src/pages/Dashboard.jsx";
import { LangContext } from "../src/context/useLangContext.jsx";
import CurrentUserContext from "../src/context/useCurrentUserContext.jsx";

const dashboardTextsState = vi.hoisted(() => ({
    dashboard: {
        tab_overview: "Overview",
        tab_profile: "My profile",
        tab_availability: "Availability",
        tab_search: "Search clubs",
        tab_requests: "My requests",
        tab_teams: "My teams",
        tab_matches: "Matches",
        tab_create_club: "Add your own club",
        tab_manage_club: "Manage your clubs",
        loading_dashboard: "Loading dashboard...",
        signed_in_as: "Signed in as",
        profile_title: "My Profile",
        profile_description: "Update your personal information.",
        first_name: "First name",
        last_name: "Last name",
        date_of_birth: "Date of birth",
        gender: "Gender",
        phone_number: "Phone number",
        save_changes: "Save changes",
        profile_updated_success: "Profile updated successfully.",
        change_password_title: "Change password",
        current_password: "Current password",
        new_password: "New password",
        repeat_password: "Repeat password",
        update_password: "Update password",
        password_updated_success: "Password updated successfully.",
        password_update_failed: "Password update failed.",
        availability_title: "My Availability",
        weekday: "Weekday",
        start_time: "Start time",
        end_time: "End time",
        select_weekday: "Choose a weekday",
        add_availability_block: "Add availability block",
        availability_added: "Availability saved.",
        availability_deleted: "Availability block deleted.",
        availability_blocks: "Your blocks",
        availability_block_detail: "Weekly recurring block",
        availability_upcoming_matches: "Upcoming matches",
        no_availability_blocks: "No availability blocks yet.",
        no_upcoming_matches: "No upcoming matches scheduled.",
        search_clubs: "Search Clubs",
        search_by_name: "Search by club name",
        request_to_join: "Request to Join",
        no_clubs_found: "No clubs found.",
        joined: "Joined",
        status_pending: "Pending",
        my_clubs: "My Clubs",
        no_clubs_yet: "You are not a member of any club yet.",
        open: "Open",
        player_invite: "Player invite",
        ladder_invite: "Ladder invite",
        club_invite: "Club invite",
        requests_i_sent: "Requests I sent",
        pending_join_requests: "Pending join requests",
        incoming_join_requests: "Incoming requests to review",
        quick_highlights: "Request Overview",
        my_join_requests: "My Join Requests",
        no_join_requests_yet: "No join requests yet.",
        requested_prefix: "Requested",
    },
}));

vi.mock("../src/hooks/common/usePageTexts.js", () => ({
    usePageTexts: (page) => dashboardTextsState[page] || {},
}));
// Shared test helper for arranging the scenario under test.

function jsonResponse(data, status = 200) {
    return {
        ok: status >= 200 && status < 300,
        status,
        json: async () => (data === undefined ? undefined : clone(data)),
    };
}

function clone(value) {
    return JSON.parse(JSON.stringify(value));
}

function getFetchCall(url, method) {
    return global.fetch.mock.calls.find(([callUrl, callInit]) => {
        if (callUrl !== url) return false;
        return (callInit?.method || "GET").toUpperCase() === method;
    });
}

function setupDashboardFetch({
    dashboardData,
    clubs,
    sportTypes,
    availability,
    me,
    joinRequests,
    clubInvitations,
    joinRequestStatus = 200,
    clubInvitationAcceptStatus = 200,
    clubInvitationAcceptDescription = "Team joined the club successfully.",
} = {}) {
    const state = {
        dashboardData: clone(
            dashboardData || {
                roles: ["user"],
                clubs: [],
                pending_requests: { my_requests: [], my_club_creation_requests: [] },
                upcoming_matches: [],
            },
        ),
        clubs: clone(
            clubs || [
                { id: 1, name: "NetRank Club", description: "Mock club", sport: "Padel", city: "Antwerp" },
                { id: 2, name: "Rally Rockets", description: "Another club", sport: "Padel", city: "Ghent" },
            ],
        ),
        sportTypes: clone(sportTypes || [{ id: 4, name: "Padel" }]),
        availability: clone(
            availability || [
                { id: 11, weekday: 0, start_time: "09:00", end_time: "11:00" },
            ],
        ),
        me: clone(
            me || {
                id: 7,
                email: "demo@netrank.com",
                firstName: "Demo",
                lastName: "User",
                dateOfBirth: "",
                gender: "male",
                phoneNumber: "0400000000",
            },
        ),
        joinRequests: clone(joinRequests || []),
        nextAvailabilityId: 12,
    };

    global.fetch = vi.fn(async (input, init = {}) => {
        const rawUrl = typeof input === "string" ? input : input.url;
        const method = (init.method || (typeof input === "string" ? "GET" : input.method) || "GET").toUpperCase();
        const url = new URL(rawUrl, "http://localhost");
        const path = url.pathname;
        const body = typeof init.body === "string" && init.body.length > 0 ? JSON.parse(init.body) : null;

        if (path === "/api/me") {
            if (method === "GET") {
                return state.me ? jsonResponse({ account: state.me }) : jsonResponse({ message: "Unauthorized" }, 401);
            }
            if (method === "PATCH") {
                state.me = { ...state.me, ...body };
                return jsonResponse({ account: state.me });
            }
        }

        if (path === "/api/me/password" && method === "PATCH") {
            return jsonResponse({ message: "Password updated." });
        }

        if (path === "/api/me/dashboard" && method === "GET") {
            return jsonResponse(state.dashboardData);
        }

        if (path === "/api/clubs" && method === "GET") {
            return jsonResponse({ clubs: state.clubs });
        }

        if (path === "/api/clubs" && method === "POST") {
            return jsonResponse({ club: { id: 99, ...body } });
        }

        if (path === "/api/teams/my-join-requests" && method === "GET") {
            return jsonResponse({ joinRequests: clone(state.joinRequests) });
        }

        if (path === "/api/teams/my-club-invitations" && method === "GET") {
            return jsonResponse({ clubInvitations: clone(clubInvitations || []) });
        }

        const clubInviteAcceptMatch = path.match(/^\/api\/teams\/(\d+)\/club-invitations\/(\d+)\/accept$/);
        if (clubInviteAcceptMatch && method === "POST") {
            return jsonResponse(
                clubInvitationAcceptStatus >= 200 && clubInvitationAcceptStatus < 300
                    ? { message: clubInvitationAcceptDescription }
                    : { description: clubInvitationAcceptDescription },
                clubInvitationAcceptStatus,
            );
        }

        if (path === "/api/sport-types" && method === "GET") {
            return jsonResponse({ sportTypes: state.sportTypes });
        }

        if (path === "/api/teams/my-all" || path === "/api/teams") {
            return jsonResponse({ total: 0, from: 0, to: 0, teams: [] });
        }

        if (path === "/api/club/join-request" && method === "GET") {
            return jsonResponse(
                { requests: state.joinRequests },
                joinRequestStatus,
            );
        }

        if (path === "/api/club/join-request" && method === "POST") {
            state.dashboardData = {
                ...state.dashboardData,
                pending_requests: {
                    ...(state.dashboardData.pending_requests || {}),
                    my_requests: [
                        ...(state.dashboardData.pending_requests?.my_requests || []),
                        {
                            id: 501,
                            club_id: body.club_id,
                            club_name: state.clubs.find((club) => club.id === body.club_id)?.name || `Club #${body.club_id}`,
                            status: "pending",
                        },
                    ],
                    my_club_creation_requests: [],
                },
            };
            return jsonResponse({ message: "Join request submitted." });
        }

        if (path === "/api/club/join-request/decide" && method === "POST") {
            state.joinRequests = state.joinRequests.filter(
                (request) => !(request.club_id === body.club_id && request.user_id === body.user_id),
            );
            return jsonResponse({ message: "Join request updated." });
        }

        if (path === "/api/me/availability" && method === "GET") {
            return jsonResponse({ availability: state.availability });
        }

        if (path === "/api/me/availability" && method === "POST") {
            const block = {
                id: state.nextAvailabilityId++,
                weekday: body.weekday,
                start_time: body.start_time,
                end_time: body.end_time,
            };
            state.availability.push(block);
            return jsonResponse({ block });
        }

        const deleteMatch = path.match(/^\/api\/me\/availability\/(\d+)$/);
        if (deleteMatch && method === "DELETE") {
            const id = Number(deleteMatch[1]);
            state.availability = state.availability.filter((block) => Number(block.id) !== id);
            return jsonResponse({ message: "Availability block deleted." });
        }

        if (path === "/api/logout" && method === "POST") {
            return jsonResponse({ message: "Successfully logged out." });
        }

        return jsonResponse({ message: `Unexpected fetch in test: ${path}` }, 404);
    });

    return state;
}

function renderDashboard({ lang = "en", currentUser = null, route = "/dashboard" } = {}) {
    const onCurrentUserChange = vi.fn();

    function Harness() {
        const [user, setUser] = useState(
            currentUser || {
                id: 7,
                email: "demo@netrank.com",
                firstName: "Demo",
                lastName: "User",
                dateOfBirth: "",
                gender: "male",
                phoneNumber: "0400000000",
            },
        );

        const updateUser = (nextUser) => {
            setUser(nextUser);
            onCurrentUserChange(nextUser);
        };

        return (
            <MemoryRouter initialEntries={[route]}>
                <LangContext.Provider value={{ lang, setLang: () => {} }}>
                    <CurrentUserContext.Provider
                        value={{
                            currentUser: user,
                            setCurrentUser: updateUser,
                            loadingUser: false,
                        }}
                    >
                        <Dashboard />
                    </CurrentUserContext.Provider>
                </LangContext.Provider>
            </MemoryRouter>
        );
    }

    return { ...render(<Harness />), onCurrentUserChange };
}

beforeEach(() => {
    localStorage.clear();
    setupDashboardFetch();
});
// End-to-end or flow coverage for the main user journey in this file.

describe("Dashboard frontend flows", () => {
    // Verifies the availability tab can create and remove a recurring block.
    test("availability tab can add and delete a weekly block", async () => {
        const user = userEvent.setup();

        renderDashboard();

        await screen.findByRole("button", { name: "Availability" });
        await user.click(screen.getByRole("button", { name: "Availability" }));

        expect(await screen.findByRole("heading", { name: "My Availability" })).toBeInTheDocument();
        expect(screen.getByText("Monday 09:00 - 11:00")).toBeInTheDocument();

        await user.selectOptions(screen.getByLabelText("Weekday"), "1");
        const startInput = screen.getByLabelText("Start time");
        const endInput = screen.getByLabelText("End time");
        await user.clear(startInput);
        await user.type(startInput, "12:00");
        await user.clear(endInput);
        await user.type(endInput, "14:00");

        await user.click(screen.getByRole("button", { name: "Add availability block" }));

        await waitFor(() => {
            expect(global.fetch).toHaveBeenCalledWith(
                "/api/me/availability",
                expect.objectContaining({ method: "POST" }),
            );
        });

        expect(screen.getByText("Tuesday 12:00 - 14:00")).toBeInTheDocument();
        expect(screen.getByText("Availability saved.")).toBeInTheDocument();

        const addedBlock = screen.getByText("Tuesday 12:00 - 14:00").closest("li");
        expect(addedBlock).toBeTruthy();
        await user.click(within(addedBlock).getByRole("button", { name: "Delete" }));

        await waitFor(() => {
            expect(global.fetch).toHaveBeenCalledWith(
                "/api/me/availability/12",
                expect.objectContaining({ method: "DELETE" }),
            );
        });

        expect(screen.queryByText("Tuesday 12:00 - 14:00")).not.toBeInTheDocument();
        expect(screen.getByText("Availability block deleted.")).toBeInTheDocument();
    });

    // Verifies the dashboard can open directly on the teams tab for the ladder shortcut.
    test("dashboard query tab opens the teams panel", async () => {
        renderDashboard({ route: "/dashboard?tab=teams" });

        expect(await screen.findByRole("button", { name: "New Team" })).toBeInTheDocument();
        expect(screen.getByRole("heading", { name: "My Teams" })).toBeInTheDocument();
    });

    // Verifies upcoming matches in the availability tab show a date-only recommendation.
    test("availability upcoming matches hide timestamps", async () => {
        setupDashboardFetch({
            dashboardData: {
                roles: ["user"],
                clubs: [],
                pending_requests: { my_requests: [], my_club_creation_requests: [] },
                upcoming_matches: [
                    {
                        id: 21,
                        team1Id: 11,
                        team2Id: 12,
                        team1Name: "NetRank Aces",
                        team2Name: "Rally Rockets",
                        status: "accepted",
                        weekStartDate: "2026-05-18",
                        proposedStartAt: "2026-05-21T10:00:00Z",
                        proposedEndAt: "2026-05-21T11:00:00Z",
                    },
                ],
            },
        });

        const user = userEvent.setup();
        renderDashboard();

        await screen.findByRole("button", { name: "Availability" });
        await user.click(screen.getByRole("button", { name: "Availability" }));

        expect(await screen.findByText("NetRank Aces vs Rally Rockets")).toBeInTheDocument();
        expect(screen.getByText("Week of 2026-05-18")).toBeInTheDocument();
        expect(screen.queryByText("10:00")).not.toBeInTheDocument();
        expect(screen.queryByText("11:00")).not.toBeInTheDocument();
    });

    // Verifies non-owner dashboards do not treat the owner join-request reload as a failure.
    test("join request reload ignores forbidden responses for non owners", async () => {
        const consoleErrorSpy = vi.spyOn(console, "error").mockImplementation(() => {});
        setupDashboardFetch({ joinRequestStatus: 403 });

        renderDashboard();

        await waitFor(() => {
            expect(consoleErrorSpy).not.toHaveBeenCalledWith(
                "Not an owner or fetch failed",
                expect.any(Error),
            );
        });

        consoleErrorSpy.mockRestore();
    });

    // Verifies club invitation acceptance succeeds and removes the row from the list.
    test("club invitation accept succeeds for a mismatched sport invitation", async () => {
        const user = userEvent.setup();
        setupDashboardFetch({
            joinRequests: [
                {
                    id: 12,
                    team_id: 88,
                    team_name: "Serve Squad",
                    club_name: "NetRank Club",
                    sport_name: "Padel",
                },
            ],
            clubInvitations: [
                {
                    id: 4,
                    teamId: 37,
                    teamName: "LrkSolo",
                    clubName: "Player Demo Club",
                    ladderName: "Player Demo Singles",
                    sportName: "Tennis",
                    ladderSportName: "Tennis",
                    sportMismatch: true,
                },
            ],
            clubInvitationAcceptStatus: 200,
            clubInvitationAcceptDescription: "Team joined the club successfully.",
        });

        renderDashboard();

        await screen.findByRole("button", { name: /My teams/i });
        await user.click(screen.getByRole("button", { name: /My teams/i }));

        expect(screen.getByText("Player invite")).toBeInTheDocument();
        expect(screen.getByText("Ladder invite")).toBeInTheDocument();
        expect(screen.getByText("Accepting this invite will change the team's sport to Tennis.")).toBeInTheDocument();
        const ladderInviteRow = screen.getByText("Ladder invite").closest("li");
        await user.click(within(ladderInviteRow).getByRole("button", { name: "Accept" }));

        await waitFor(() => {
            expect(screen.queryByText("LrkSolo")).not.toBeInTheDocument();
        });
    });

    // Verifies the profile form submits the edited personal details.
    test("profile tab submits updated personal information", async () => {
        const user = userEvent.setup();

        const { onCurrentUserChange } = renderDashboard();

        await screen.findByRole("button", { name: "My profile" });
        await user.click(screen.getByRole("button", { name: "My profile" }));

        await user.clear(screen.getByLabelText("First name"));
        await user.type(screen.getByLabelText("First name"), "Jordan");
        await user.clear(screen.getByLabelText("Last name"));
        await user.type(screen.getByLabelText("Last name"), "Smith");
        await user.clear(screen.getByLabelText("Date of birth"));
        await user.type(screen.getByLabelText("Date of birth"), "2000-05-14");
        await user.selectOptions(screen.getByLabelText("Gender"), "female");
        await user.clear(screen.getByLabelText("Phone number"));
        await user.type(screen.getByLabelText("Phone number"), "0499123456");

        await user.click(screen.getByRole("button", { name: "Save changes" }));

        await waitFor(() => {
            expect(global.fetch).toHaveBeenCalledWith(
                "/api/me",
                expect.objectContaining({ method: "PATCH" }),
            );
        });

        const profileCall = getFetchCall("/api/me", "PATCH");
        expect(profileCall).toBeDefined();
        expect(JSON.parse(profileCall[1].body)).toEqual({
            firstName: "Jordan",
            lastName: "Smith",
            dateOfBirth: "2000-05-14",
            gender: "female",
            phoneNumber: "0499123456",
        });
        expect(onCurrentUserChange).toHaveBeenCalledWith(
            expect.objectContaining({
                firstName: "Jordan",
                lastName: "Smith",
                gender: "female",
                phoneNumber: "0499123456",
            }),
        );
        expect(screen.getByText("Profile updated successfully.")).toBeInTheDocument();
    });

    // Verifies the password form sends the password change request.
    test("password form submits a password update request", async () => {
        const user = userEvent.setup();

        renderDashboard();

        await screen.findByRole("button", { name: "My profile" });
        await user.click(screen.getByRole("button", { name: "My profile" }));

        await user.clear(screen.getByLabelText("Current password"));
        await user.type(screen.getByLabelText("Current password"), "oldpass1");
        await user.clear(screen.getByLabelText("New password"));
        await user.type(screen.getByLabelText("New password"), "newpass1");
        await user.clear(screen.getByLabelText("Repeat password"));
        await user.type(screen.getByLabelText("Repeat password"), "newpass1");

        await user.click(screen.getByRole("button", { name: "Update password" }));

        await waitFor(() => {
            expect(global.fetch).toHaveBeenCalledWith(
                "/api/me/password",
                expect.objectContaining({ method: "PATCH" }),
            );
        });

        const passwordCall = getFetchCall("/api/me/password", "PATCH");
        expect(passwordCall).toBeDefined();
        expect(JSON.parse(passwordCall[1].body)).toEqual({
            currentPassword: "oldpass1",
            password: "newpass1",
            repeatPassword: "newpass1",
        });
        expect(screen.getByText("Password updated successfully.")).toBeInTheDocument();
    });

    // Verifies the club search tab can submit a join request for a club.
    test("search clubs tab can submit a join request", async () => {
        const user = userEvent.setup();

        renderDashboard({
            currentUser: {
                id: 7,
                email: "demo@netrank.com",
                firstName: "Demo",
                lastName: "User",
                gender: "male",
                phoneNumber: "0400000000",
            },
        });

        await screen.findByRole("button", { name: "Search clubs" });
        await user.click(screen.getByRole("button", { name: "Search clubs" }));

        expect(await screen.findByRole("heading", { name: "Search Clubs" })).toBeInTheDocument();
        expect(screen.getByPlaceholderText("Search by club name")).toBeInTheDocument();

        await user.type(screen.getByPlaceholderText("Search by club name"), "Rally");

        const joinButton = await screen.findByRole("button", { name: "Request to Join" });
        await user.click(joinButton);

        await waitFor(() => {
            expect(global.fetch).toHaveBeenCalledWith(
                "/api/club/join-request",
                expect.objectContaining({ method: "POST" }),
            );
        });

        const joinRequestCall = getFetchCall("/api/club/join-request", "POST");
        expect(JSON.parse(joinRequestCall[1].body)).toEqual({ club_id: 2 });
    });

    // Verifies a submitted club request appears in the requests tab without a page refresh.
    test("club join request appears in my requests after submitting", async () => {
        const user = userEvent.setup();

        renderDashboard({
            currentUser: {
                id: 7,
                email: "demo@netrank.com",
                firstName: "Demo",
                lastName: "User",
                gender: "male",
                phoneNumber: "0400000000",
            },
        });

        await screen.findByRole("button", { name: "Search clubs" });
        await user.click(screen.getByRole("button", { name: "Search clubs" }));
        await user.type(screen.getByPlaceholderText("Search by club name"), "Rally");

        await user.click(await screen.findByRole("button", { name: "Request to Join" }));

        await waitFor(() => {
            expect(screen.getByText("Request sent.")).toBeInTheDocument();
        });

        await user.click(screen.getByRole("button", { name: /My requests/i }));

        expect(await screen.findByRole("heading", { name: "My Join Requests" })).toBeInTheDocument();
        expect(screen.getByText("Rally Rockets")).toBeInTheDocument();
    });

    // Verifies club-owner decisions remove the request row without reloading the page.
    test("incoming join request disappears after approving it", async () => {
        const user = userEvent.setup();

        setupDashboardFetch({
            joinRequests: [
                {
                    club_id: 1,
                    user_id: 33,
                    user_name: "Alex",
                    club_name: "NetRank Club",
                    status: "pending",
                },
            ],
        });

        renderDashboard({
            currentUser: {
                id: 7,
                email: "owner@netrank.com",
                firstName: "Owner",
                lastName: "User",
                gender: "male",
                phoneNumber: "0400000000",
            },
        });

        await screen.findByRole("button", { name: /Manage your clubs/i });
        await user.click(screen.getByRole("button", { name: /Manage your clubs/i }));

        expect(await screen.findByText("Alex")).toBeInTheDocument();

        await user.click(screen.getByRole("button", { name: "Approve" }));

        await waitFor(() => {
            expect(screen.queryByText("Alex")).not.toBeInTheDocument();
        });
    });
});
