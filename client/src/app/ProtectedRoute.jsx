import { Navigate } from "react-router-dom";
import { useCurrentUserContext } from "@/context/useCurrentUserContext";

export default function ProtectedRoute({ children }) {
    const { currentUser, loadingUser } = useCurrentUserContext();

    if (loadingUser) return <div>Loading...</div>;

    if (!currentUser) return <Navigate to="/login" replace />;

    return children;
}