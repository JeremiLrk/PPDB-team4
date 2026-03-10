import { Routes, Route } from "react-router-dom";
import Home from "@/pages/Home.jsx";
import Login from "@/pages/Login.jsx";
import Register from "@/pages/Register.jsx";
import Ladder from "@/pages/Ladder.jsx";
import NotFound from "@/pages/NotFound.jsx";

export default function AppRoutes({ currentUser, setUser }) {
    return (
        <Routes>
            <Route path="/" element={<Home currentUser={currentUser}/>} />
            <Route path="/login" element={<Login setUser={setUser}/>} />
            <Route path="/register" element={<Register setUser={setUser}/>} />
            <Route path="/ladder" element={<Ladder />} />
            <Route path="*" element={<NotFound />} />
        </Routes>
    );
}