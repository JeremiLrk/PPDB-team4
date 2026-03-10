import { useEffect, useState } from "react"

export function useTopPlayers(clubId) {
    const [players, setPlayers] = useState([])
    const [loading, setLoading] = useState(true)

    useEffect(() => {
        if (!clubId) return

        fetch(`/api/clubs/${clubId}/top-players`)
            .then(res => res.json())
            .then(data => {
                setPlayers(data)
                setLoading(false)
            })
    }, [clubId])

    return { players, loading }
}