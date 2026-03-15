import { Routes, Route } from "react-router-dom"
import Home from "@/pages/Home.jsx"
import Login from "@/pages/Login.jsx"
import Register from "@/pages/Register.jsx"
import ForgotPassword from "@/pages/ForgotPassword.jsx"
import Ladder from "@/pages/Ladder.jsx"
import NotFound from "@/pages/NotFound.jsx"
import ResetPassword from "@/pages/ResetPassword.jsx"
import { useCurrentUserContext } from "@/context/useCurrentUserContext.js"

export default function AppRoutes() {
    const { setCurrentUser } = useCurrentUserContext()

    return (
        <Routes>
            <Route path="/" element={<Home />} />
            <Route path="/login" element={<Login setUser={setCurrentUser} />} />
            <Route
                path="/register"
                element={<Register setUser={setCurrentUser} />}
            />
            <Route path="/forgot-password" element={<ForgotPassword />} />
            <Route path="/reset-password/:token" element={<ResetPassword />} />
            <Route path="/ladder" element={<Ladder />} />
            <Route path="*" element={<NotFound />} />
        </Routes>
    )
}
