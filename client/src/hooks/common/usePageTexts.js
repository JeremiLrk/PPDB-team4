import { useEffect, useState } from "react";

export function usePageTexts(page, lang = "en") {
    const [texts, setTexts] = useState({});

    useEffect(() => {
        fetch(`/api/texts/page/${page}?lang=${lang}`)
            .then(res => {
                if (!res.ok) throw new Error(`HTTP ${res.status}`);  // Check status
                return res.json();
            })
            .then(setTexts)
            .catch(err => console.error("Failed to load texts:", err));
    }, [page, lang]);

    return texts;
}