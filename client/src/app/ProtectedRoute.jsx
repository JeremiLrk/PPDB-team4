// Route guard for authenticated pages.

import { Navigate } from "react-router-dom";
import { useCurrentUserContext } from "@/context/useCurrentUserContext";

export default function ProtectedRoute({ children }) {
    /*
     Blocks access until the current user session is known.
    */
    const { currentUser, loadingUser } = useCurrentUserContext();

    if (loadingUser) return <div>Loading...</div>;

    if (!currentUser) return <Navigate to="/login" replace />;

    return children;
}
