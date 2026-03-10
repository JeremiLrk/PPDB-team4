import { useEffect, useState } from "react"

export function useLadder(clubId, ladderId) {
    const [players, setPlayers] = useState([])
    const [loading, setLoading] = useState(true)
    const [error, setError] = useState(null)

    useEffect(() => {
        if (!clubId || !ladderId) return

        setLoading(true)

        fetch(`/api/clubs/${clubId}/ladders/${ladderId}`)
            .then(res => {
                if (!res.ok) {
                    throw new Error("Failed to fetch ladder")
                }
                return res.json()
            })
            .then(data => {
                setPlayers(data)
                setLoading(false)
            })
            .catch(err => {
                setError(err)
                setLoading(false)
            })

    }, [clubId, ladderId])

    return { players, loading, error }
}