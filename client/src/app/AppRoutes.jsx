import { Routes, Route } from "react-router-dom";
import Home from "@/pages/Home.jsx";
import Login from "@/pages/Login.jsx";
import Register from "@/pages/Register.jsx";
import Ladder from "@/pages/Ladder.jsx";
import NotFound from "@/pages/NotFound.jsx";

export default function AppRoutes() {
    return (
        <Routes>
            <Route path="/" element={<Home />} />
            <Route path="/login" element={<Login />} />
            <Route path="/register" element={<Register />} />
            <Route path="/ladder" element={<Ladder />} />
            <Route path="*" element={<NotFound />} />
        </Routes>
    );
}