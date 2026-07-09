import { ExternalLink } from "lucide-react";

export default function ResultsList({ results }) {
  if (!results || results.length === 0) {
    return (
      <div className="text-center py-12">
        <p className="text-slate-400 text-lg">No results found</p>
      </div>
    );
  }

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
      {results.map((state) => (
        <div
          key={state.name}
          className="flex flex-col rounded-lg border border-slate-700 bg-slate-800/60 overflow-hidden transition-colors hover:border-slate-600"
        >
          <div className="p-5 border-b border-slate-700 flex items-start justify-between gap-3">
            <h2 className="text-lg font-semibold text-white">{state.name}</h2>
            {state.success ? (
              <span className="shrink-0 rounded-full bg-green-500/15 px-2.5 py-1 text-xs font-medium text-green-400">
                ✓ Success
              </span>
            ) : (
              <span className="shrink-0 rounded-full bg-red-500/15 px-2.5 py-1 text-xs font-medium text-red-400">
                ✗ Failed
              </span>
            )}
          </div>

          <div className="p-5 flex-1">
            <p className="text-sm text-slate-400 mb-2">Issues Found</p>
            <p className="text-3xl font-bold text-orange-400">
              {state.issues || 0}
            </p>
          </div>

          <div className="p-5 border-t border-slate-700">
            <a
              href={`#/state/${state.state}`}
              className="flex w-full items-center justify-center gap-2 rounded-md bg-blue-600 px-4 py-2.5 text-sm font-medium text-white hover:bg-blue-500 transition-colors"
            >
              View Report
              <ExternalLink size={16} />
            </a>
          </div>
        </div>
      ))}
    </div>
  );
}
