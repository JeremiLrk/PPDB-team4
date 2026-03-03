import { useState } from "react"
import { useNavigate } from "react-router-dom"
import { Link } from "react-router-dom"

const Register = () => {
    const [email, setEmail] = useState("")
    const [password, setPassword] = useState("")
    const navigate = useNavigate()

    const handleSubmit = async (e) => {
        e.preventDefault()

        try {
            const response = await fetch("/api/signup", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({
                    email: email.toLowerCase(),
                    password,
                }),
            })

            const data = await response.json()

            if (!response.ok) {
                throw new Error(data?.message || "Registration failed")
            }

            navigate("/login")
        } catch (err) {
            console.error(err.message || "Registration failed")
        }
    }

    return (
        <div className="min-h-screen flex items-center justify-center px-4">
            <div className="w-full max-w-md p-8">
                <h1 className="text-3xl font-bold">Register</h1>

                <form className="mt-6 space-y-4" onSubmit={handleSubmit}>
                    <div className="space-y-2">
                        <label
                            htmlFor="register-email"
                            className="text-sm text-black"
                        >
                            Email
                        </label>
                        <input
                            id="register-email"
                            type="email"
                            placeholder="Enter your email"
                            value={email}
                            onChange={(e) => setEmail(e.target.value)}
                            className="w-full rounded-lg border px-3 py-2"
                        />
                    </div>

                    <div className="space-y-2">
                        <label
                            htmlFor="register-password"
                            className="text-sm text-black"
                        >
                            Password
                        </label>
                        <input
                            id="register-password"
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
                        Create account
                    </button>
                </form>

                <p className="mt-4 text-sm">
                    Already have an account?{" "}
                    <Link
                        to="/login"
                        className="text-blue-500 hover:text-blue-300"
                    >
                        Log in
                    </Link>
                </p>
            <Link to="/" className="text-1xl font-semibold mt-6 text-indigo-400 hover:text-indigo-300 underline">
                Continue as guest
            </Link>                
            </div>            
        </div>
    )
}

export default Register
