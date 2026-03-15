import React from "react"
import { Link } from "react-router-dom"
import {useLangContext} from "@/context/useLangContext.js";
import {usePageTexts} from "@/hooks/usePageTexts.js";

const NotFound = () => {
    const {lang, setLang } = useLangContext();
    const base_texts = usePageTexts("base", lang);
    const home_texts = usePageTexts("home", lang);

    return (
        <div className="min-h-screen flex flex-col items-center justify-center">
            <h1 className="text-3xl font-semibold">{base_texts.e404}</h1>

            <Link to="/" className="mt-6 text-indigo-400 hover:text-indigo-300 underline">
                {home_texts.home}
            </Link>
        </div>
    )
}

export default NotFound
