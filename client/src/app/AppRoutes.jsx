// Route map for public and private pages.

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
import ClubSettings from "@/pages/ClubSettings.jsx";
import ClubDisputedMatchesPage from "@/pages/ClubDisputedMatchesPage.jsx";
import { useCurrentUserContext } from "@/context/useCurrentUserContext";
import ProtectedRoute from "./ProtectedRoute";
import Teams from "@/pages/Teams.jsx";
import TeamDetail from "@/pages/TeamDetail.jsx";
import TeamSettings from "@/pages/TeamSettings.jsx";
import VerifyEmail from "@/pages/VerifyEmail.jsx";

export default function AppRoutes() {
    const { currentUser, setCurrentUser } = useCurrentUserContext()
    /*
     Declares the full client-side route map.
    */

    return (
        <Routes>
            <Route path="/" element={<Landing />} />
            <Route path="/clubs" element={<Clubs />} />
            <Route path="/clubs/:clubId" element={<ClubHome />} />
            <Route path="/clubs/:clubId/ladders" element={<Ladders />} />
            <Route
                path="/clubs/:clubId/ladders/:ladderId"
                element={<Ladder />}
            />
            <Route path="/ladder" element={<Ladder />} />
            <Route path="/login" element={<Login setUser={setCurrentUser} />} />
            <Route
                path="/register"
                element={<Register setUser={setCurrentUser} />}
            />
            <Route path="/forgot-password" element={<ForgotPassword />} />
            <Route path="/reset-password/:token" element={<ResetPassword />} />
            <Route path="/teams" element={<Teams />} />
            <Route path="/teams/:teamId" element={<TeamDetail />} />
            <Route path="/teams/:teamId/settings" element={<TeamSettings />} />
            <Route path="/dashboard" element={
                    <ProtectedRoute>
                        <Dashboard />
                    </ProtectedRoute>
                }/>
            <Route path="/clubs/:clubId/settings" element={
                    <ProtectedRoute>
                        <ClubSettings />
                    </ProtectedRoute>
                }/>
            <Route path="/clubs/:clubId/settings/disputed" element={
                    <ProtectedRoute>
                        <ClubDisputedMatchesPage />
                    </ProtectedRoute>
                }/>
            <Route path="/verify-email/:token" element={<VerifyEmail />} />
            <Route path="*" element={<NotFound />} />
        </Routes>
    );
}
