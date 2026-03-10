import React from "react"
import { Link } from "react-router-dom"

const NotFound = () => {
    return (
        <div className="min-h-screen flex flex-col items-center justify-center">
            <h1 className="text-3xl font-semibold">404 - Page Not Found</h1>

            <Link to="/" className="mt-6 text-indigo-400 hover:text-indigo-300 underline">
                Home
            </Link>
        </div>
    )
}

export default NotFound
