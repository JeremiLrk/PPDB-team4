import { useNavigate, useParams } from "react-router-dom"
import { useLadders } from "../hooks/useLadders"

const Ladders = () => {
    const navigate = useNavigate()
    const { clubId } = useParams()
    const { ladders, loading } = useLadders(clubId)

    return (

        <div className="mx-auto max-w-6xl">

            {/* Header */}
            <div className="mb-12">
                <h1 className="text-4xl font-semibold tracking-tight">
                    Available Ladders
                </h1>
                {!loading && ladders.length === 0 && (
                    <p className="p-6 text-slate-400">No ladder available for this club.</p>
                )}
            </div>

            {/* Ladder Grid */}
            <div className="grid gap-8 md:grid-cols-2 lg:grid-cols-3">

                {loading && (
                    <p className="text-slate-400">Loading ladders...</p>
                )}

                {!loading && ladders.map((ladder) => (
                    <div
                        key={ladder.id}
                        className="rounded-3xl border border-white/10 bg-white/5 p-8 backdrop-blur hover:bg-white/10 transition cursor-pointer"
                        onClick={() => navigate(`/clubs/${clubId}/ladders/${ladder.id}`)}
                    >
                        <h2 className="text-xl font-semibold">
                            {ladder.name}
                        </h2>

                        <p className="mt-3 text-sm text-slate-400">
                            {ladder.description}
                        </p>
                    </div>
                ))}

            </div>

        </div>
    )
}

export default Ladders