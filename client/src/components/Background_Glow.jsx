export default function Background_Glow() {
    return (
        <div className="pointer-events-none fixed inset-0 opacity-35">
            <div className="absolute -top-40 left-1/2 h-72 w-2xl -translate-x-1/2 rounded-full bg-indigo-500 blur-3xl" />
            <div className="absolute top-20 left-1/2 h-72 w-2xl -translate-x-1/2 rounded-full bg-cyan-500 blur-3xl" />
        </div>
    );
}