import { useState } from "react"
import { useNavigate } from "react-router-dom"
import { Link } from "react-router-dom"

const Login = () => {
    const [email, setEmail] = useState("")
    const [password, setPassword] = useState("")
    const navigate = useNavigate()

    const handleSubmit = async (e) => {
        e.preventDefault()

        try {
            const response = await fetch("/api/login", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({
                    email: email.toLowerCase(),
                    password,
                }),
            })

            const data = await response.json()

            if (!response.ok) {
                throw new Error(data?.message || "Login failed")
            }
            navigate("/")
        } catch (err) {
            console.error(err.message || "Login failed")
        }
    }

    return (
        <div className="min-h-screen flex items-center justify-center px-4">
            <div className="w-full max-w-md p-8">
                <h1 className="text-3xl font-bold">Login</h1>

                <form className="mt-6 space-y-4" onSubmit={handleSubmit}>
                    <div className="space-y-2">
                        <label
                            htmlFor="login-email"
                            className="text-sm text-black"
                        >
                            Email
                        </label>
                        <input
                            id="login-email"
                            type="email"
                            placeholder="Enter your email"
                            value={email}
                            onChange={(e) => setEmail(e.target.value)}
                            className="w-full rounded-lg border px-3 py-2"
                        />
                    </div>

                    <div className="space-y-2">
                        <label
                            htmlFor="login-password"
                            className="text-sm text-black"
                        >
                            Password
                        </label>
                        <input
                            id="login-password"
                            type="password"
                            placeholder="Enter your password"
                            value={password}
                            onChange={(e) => setPassword(e.target.value)}
                            className="w-full rounded-lg border px-3 py-2"
                        />
                    </div>

                    <button
                        type="submit"
                        className="w-full rounded-lg bg-slate-500 px-4 py-2 font-semibold text-white hover:bg-slate-400"
                    >
                        Login
                    </button>
                </form>

                <p className="mt-4 text-sm">
                    Don't have an account?{" "}
                    <Link
                        to="/register"
                        className="text-blue-500 hover:text-blue-300"
                    >
                        Register
                    </Link>
                </p>
            </div>
        </div>
    )
}

export default Login
