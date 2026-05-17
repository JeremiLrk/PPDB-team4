// Shared hook for useTopPlayers.

import { useEffect, useState } from "react"

export function useTopPlayers(clubId) {
    /*
     Loads the top-player list for one club.
    */
    const [players, setPlayers] = useState([])
    const [loading, setLoading] = useState(true)

    useEffect(() => {
        if (!clubId) return

        /*
         Fetches the ranking rows used on the club home page.
        */
        fetch(`/api/clubs/${clubId}/top-players`)
            .then(res => res.json())
            .then(data => {
                setPlayers(data.players)
                setLoading(false)
            })
    }, [clubId])

    return { players, loading }
}
