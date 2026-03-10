import { Navigate, Routes, Route } from "react-router-dom";
import Landing from "@/pages/Landing.jsx";
import Clubs from "@/pages/Clubs.jsx";
import ClubHome from "@/pages/ClubHome.jsx";
import Login from "@/pages/Login.jsx";
import Register from "@/pages/Register.jsx";
import Ladder from "@/pages/Ladder.jsx";
import Dashboard from "@/pages/Dashboard.jsx";
import NotFound from "@/pages/NotFound.jsx";

export default function AppRoutes({ currentUser, setUser }) {
    return (
        <Routes>
            <Route path="/" element={<Landing />} />
            <Route path="/clubs" element={<Clubs />} />
            <Route path="/clubs/:clubId" element={<ClubHome />} />
            <Route path="/login" element={<Login setUser={setUser}/>} />
            <Route path="/register" element={<Register setUser={setUser}/>} />
            <Route path="/ladder" element={<Ladder />} />
            <Route
                path="/dashboard"
                element={currentUser ? <Dashboard currentUser={currentUser} /> : <Navigate to="/login" replace />}
            />
            <Route path="*" element={<NotFound />} />
        </Routes>
    );
}
