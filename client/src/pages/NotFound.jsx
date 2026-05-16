import React from "react"
import { Link } from "react-router-dom"
import {useLangContext} from "@/context/useLangContext.jsx";
import {usePageTexts} from "@/hooks/common/usePageTexts.js";

const NotFound = () => {
    const {lang} = useLangContext();
    const base_texts = usePageTexts("base", lang);
    const home_texts = usePageTexts("home", lang);

    return (
        <div className="flex-1 flex flex-col items-center justify-center">
            <h1 className="text-3xl font-semibold">{base_texts.e404}</h1>

            <Link to="/" className="mt-6 underline" style={{ color: "#38bdf8" }}>
                {home_texts.home}
            </Link>
        </div>
    )
}

export default NotFound
