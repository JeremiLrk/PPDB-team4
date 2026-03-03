
export default function Badge({ status }) {
    const badge =
        status.state === "loading"
        ? { text: "Checking…", cls: "border-white/10 bg-white/5 text-slate-200/80" }
        : status.state === "ok"
        ? { text: "Online", cls: "border-emerald-500/20 bg-emerald-500/10 text-emerald-200" }
        : { text: "Offline", cls: "border-red-500/20 bg-red-500/10 text-red-200" };

        return <span className={`rounded-lg border px-2 py-1 text-xs ${badge.cls}`}>{badge.text}</span>;
}