// Reusable component for Badge.

import { useLangContext } from "@/context/useLangContext.jsx";
import { usePageTexts } from "@/hooks/common/usePageTexts.js";

export default function Badge({ status }) {
    /*
     Renders the small backend status badge in the header.
    */
    const { lang } = useLangContext();
    const baseTexts = usePageTexts("base", lang);

    const badge =
        status.state === "loading"
        ? { text: baseTexts.checking || "Checking…", cls: "border-white/10 bg-white/5 text-slate-200/80" }
        : status.state === "ok"
        ? { text: baseTexts.online || "Online", cls: "border-emerald-500/20 bg-emerald-500/10 text-emerald-200" }
        : { text: baseTexts.offline || "Offline", cls: "border-red-500/20 bg-red-500/10 text-red-200" };

        return <span className={`rounded-lg border px-2 py-1 text-xs ${badge.cls}`}>{badge.text}</span>;
}
