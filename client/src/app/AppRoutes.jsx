import { Navigate, Route, Routes } from "react-router-dom";
import Landing from "@/pages/Landing.jsx";
import Clubs from "@/pages/Clubs.jsx";
import ClubHome from "@/pages/ClubHome.jsx";
import Login from "@/pages/Login.jsx";
import Register from "@/pages/Register.jsx";
import Ladders from "@/pages/Ladders.jsx";
import Ladder from "@/pages/Ladder.jsx";
import Dashboard from "@/pages/Dashboard.jsx";
import NotFound from "@/pages/NotFound.jsx";
import ForgotPassword from "@/pages/ForgotPassword.jsx";
import ResetPassword from "@/pages/ResetPassword.jsx";
import { useCurrentUserContext } from "@/context/useCurrentUserContext.js";
import ClubManage from "@/pages/ClubManage";

export default function AppRoutes() {
    const { currentUser, setCurrentUser } = useCurrentUserContext();

    return (
        <Routes>
            <Route path="/" element={<Landing />} />
            <Route path="/clubs" element={<Clubs />} />
            <Route path="/clubs/:clubId" element={<ClubHome />} />
            <Route path="/clubs/:clubId/ladders" element={<Ladders />} />
            <Route path="/clubs/:clubId/ladders/:ladderId" element={<Ladder />} />
            <Route path="/ladder" element={<Ladder />} />
            <Route path="/login" element={<Login setUser={setCurrentUser} />} />
            <Route path="/register" element={<Register setUser={setCurrentUser} />} />
            <Route path="/forgot-password" element={<ForgotPassword />} />
            <Route path="/reset-password/:token" element={<ResetPassword />} />
            <Route path="/clubs/:clubId/manage" element={<ClubManage />} />
            <Route
                path="/dashboard"
                element={
                    currentUser ? (
                        <Dashboard currentUser={currentUser} setUser={setCurrentUser} />
                    ) : (
                        <Navigate to="/login" replace />
                    )
                }
            />
            <Route path="*" element={<NotFound />} />
        </Routes>
    );
}
