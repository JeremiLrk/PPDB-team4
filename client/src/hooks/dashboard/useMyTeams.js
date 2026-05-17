// Dashboard data hook for useMyTeams.

import { useTeams } from "@/hooks/teams/useTeams.js";

const MY_TEAMS_DEFAULTS = {
    pageSize: 12,
    sort: "name",
    endpoint: "/api/teams/my-all",
};

/**
 * Hook for the current user's command page/tab.
 *
 * Encapsulates the query configuration and provides a convenient single interface,
 * so that the command page does not depend on the details of useDashboardWorkspace.
 *
 * @param {object} [options]
 * @param {number} [options.pageSize=12]   — number of commands per page
 * @param {string} [options.sort="name"]   — sort field
 * @param {string} [options.endpoint]      — API endpoint (if needed to be overridden)
 *
 * @returns {{
 *   teams: Array,
 *   total: number,
 *   loading: boolean,
 *   error: string|null,
 *   sort: string,
 *   pageSize: number,
 *   hasMore: boolean,
 *   load: () => void,
 *   loadMore: () => void,
 * }}
 */
export function useMyTeams({
    pageSize = MY_TEAMS_DEFAULTS.pageSize,
    sort = MY_TEAMS_DEFAULTS.sort,
    endpoint = MY_TEAMS_DEFAULTS.endpoint,
} = {}) {
    const {
        teams,
        total,
        loading,
        error,
        sort: activeSort,
        pageSize: activePageSize,
        hasMore,
        load,
        loadMore,
    } = useTeams({ pageSize, sort, endpoint });

    return {
        teams,
        total,
        loading,
        error,
        sort: activeSort,
        pageSize: activePageSize,
        hasMore,
        load,
        loadMore,
    };
}
