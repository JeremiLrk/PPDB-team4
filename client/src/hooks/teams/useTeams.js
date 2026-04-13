import {useState, useCallback, useEffect} from "react";

const DEFAULT_PAGE_SIZE = 12;

/**
 * @param {{
 *   pageSize?: number,
 *   sort?: "id"|"name",
 *   endpoint?: string,   // default: "/api/teams"
 * }} initialOptions
 */
export function useTeams({
                             pageSize: initialPageSize = DEFAULT_PAGE_SIZE,
                             sort: initialSort = "id",
                             endpoint = "/api/teams",
                         } = {}) {
    const [teams,    setTeams]    = useState([]);
    const [total,    setTotal]    = useState(null);
    const [loading,  setLoading]  = useState(false);
    const [error,    setError]    = useState(null);
    const [offset,   setOffset]   = useState(0);
    const [sort,     setSort]     = useState(initialSort);
    const [pageSize, setPageSize] = useState(initialPageSize);

    const fetchTeams = useCallback(async ({
                                              fromOffset = 0,
                                              currentSort = sort,
                                              currentPageSize = pageSize,
                                              append = false,
                                          } = {}) => {
        setLoading(true);
        setError(null);

        try {
            const to  = fromOffset + currentPageSize;
            const url = `${endpoint}?from=${fromOffset}&to=${to}&sort=${currentSort}`;
            const res = await fetch(url, { credentials: "include" });
            const data = await res.json();

            if (!res.ok) throw new Error(data?.message || "Failed to load teams.");

            setTotal(data.total);
            setOffset(fromOffset + data.teams.length);
            setTeams(prev => append ? [...prev, ...data.teams] : data.teams);
        } catch (err) {
            setError(err.message);
        } finally {
            setLoading(false);
        }
    }, [sort, pageSize, endpoint]);

    const load = useCallback(async (overrides = {}) => {
        const newSort     = overrides.sort     ?? sort;
        const newPageSize = overrides.pageSize ?? pageSize;

        if (overrides.sort     !== undefined) setSort(newSort);
        if (overrides.pageSize !== undefined) setPageSize(newPageSize);

        setOffset(0);
        setTeams([]);

        await fetchTeams({ fromOffset: 0, currentSort: newSort, currentPageSize: newPageSize, append: false });
    }, [sort, pageSize, fetchTeams]);

    const loadMore = useCallback(async () => {
        await fetchTeams({ fromOffset: offset, append: true });
    }, [offset, fetchTeams]);

    const hasMore = total === null ? true : offset < total;

    // Initial load on mount
    useEffect(() => {
        void fetchTeams({ fromOffset: 0, currentSort: sort, currentPageSize: pageSize, append: false });
        // eslint-disable-next-line react-hooks/exhaustive-deps
    }, []);
    
    return { teams, total, loading, error, sort, pageSize, hasMore, load, loadMore, setSort, setPageSize };
}