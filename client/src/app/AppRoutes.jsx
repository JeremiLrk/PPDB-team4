import { Routes, Route } from "react-router-dom";
import Home from "@/pages/Home.jsx";
import Login from "@/pages/Login.jsx";
import Register from "@/pages/Register.jsx";
import Ladders from "@/pages/Ladders.jsx";
import Ladder from "@/pages/Ladder.jsx";
import NotFound from "@/pages/NotFound.jsx";

export default function AppRoutes({ currentUser, setUser }) {
    return (
        <Routes>
            <Route path="/login" element={<Login setUser={setUser}/>} />
            <Route path="/register" element={<Register setUser={setUser}/>} />
            <Route path="/clubs/:clubId/ladders" element={<Ladders />} />
            <Route path="/clubs/:clubId/ladders/:ladderId" element={<Ladder />} />
            <Route path="/clubs/:clubId" element={<Home currentUser={currentUser}/>} />
            <Route path="*" element={<NotFound />} />
        </Routes>
    );
}