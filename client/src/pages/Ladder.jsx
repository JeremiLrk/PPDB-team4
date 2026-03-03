import React from "react"
import {useNavigate, Link } from "react-router-dom"

const Ladder = () => {
    const navigate = useNavigate()

    // Temporary mock data
    const ladders = [
        {
        name: "Men's Tennis",
        description: "Competitive men's singles ladder.",
        players: 24,
        },
        {
        name: "Women's Tennis",
        description: "Women's competitive ranking ladder.",
        players: 18,
        },
        {
        name: "Padel",
        description: "Club padel ranking system.",
        players: 32,
        },
        {
        name: "Juniors",
        description: "Under 18 development ladder.",
        players: 12,
        },
    ]

    return (
        <div className="min-h-screen bg-slate-950 text-slate-100 px-6 py-16">
        <div className="mx-auto max-w-6xl">

            {/* Header */}
            <div className="mb-12">
            <h1 className="text-4xl font-semibold tracking-tight">
                Available Ladders
            </h1>
            <p className="mt-2 text-slate-400 text-sm">
                Choose a ladder and start competing.
            </p>
            </div>

            {/* Ladder Grid */}
            <div className="grid gap-8 md:grid-cols-2 lg:grid-cols-3">
            {ladders.map((ladder) => (
                <div
                key={ladder.name}
                className="rounded-3xl border border-white/10 bg-white/5 p-8 backdrop-blur hover:bg-white/10 transition cursor-pointer"
                onClick={() => navigate(`/ladders/${ladder.name.toLowerCase().replace(/\s+/g, "-")}`)}>
                <h2 className="text-xl font-semibold">
                    {ladder.name}
                </h2>

                <p className="mt-3 text-sm text-slate-400">
                    {ladder.description}
                </p>

                <div className="mt-6 text-xs text-slate-500">
                    {ladder.players} players
                </div>
                </div>
            ))}
            </div>

        </div>
        </div>
    )
}

export default Ladder