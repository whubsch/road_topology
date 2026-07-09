import { useState, useEffect } from "react";
import { ArrowLeft, ExternalLink } from "lucide-react";

function formatTimestamp(timestamp) {
  try {
    const date = new Date(timestamp);
    if (Number.isNaN(date.getTime())) return timestamp;
    return date.toLocaleDateString(undefined, {
      year: "2-digit",
      month: "short",
      day: "numeric",
    });
  } catch {
    return timestamp;
  }
}

export default function StateReport({ stateSlug, stateName, onBack }) {
  const [report, setReport] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    const fetchReport = async () => {
      try {
        setLoading(true);
        setError(null);
        const url = `${import.meta.env.BASE_URL}reports/${stateSlug}.json`;
        const response = await fetch(url);
        if (!response.ok) {
          throw new Error(`Failed to fetch report from ${url}`);
        }
        const data = await response.json();
        setReport(data);
      } catch (err) {
        setError(err.message);
      } finally {
        setLoading(false);
      }
    };

    fetchReport();
  }, [stateSlug]);

  const displayName = report?.state_name || stateName || stateSlug;

  return (
    <div className="space-y-8">
      <button
        type="button"
        onClick={onBack}
        className="-ml-3 inline-flex items-center gap-2 rounded-md px-3 py-2 text-sm font-medium text-slate-300 hover:bg-slate-800 hover:text-white transition-colors"
      >
        <ArrowLeft size={16} />
        Back to all states
      </button>

      {loading ? (
        <div className="flex flex-col items-center justify-center h-96 gap-4">
          <div className="h-10 w-10 animate-spin rounded-full border-4 border-slate-600 border-t-blue-500" />
          <p className="text-slate-300">Loading report…</p>
        </div>
      ) : error ? (
        <div className="max-w-2xl mx-auto rounded-lg border border-red-500/30 bg-red-500/10 p-4">
          <p className="font-semibold text-red-400">Failed to load report</p>
          <p className="text-sm text-red-300/90 mt-1">{error}</p>
        </div>
      ) : (
        <div className="space-y-8">
          <div>
            <h1 className="text-3xl font-bold text-white mb-3">
              🚗 OSM Highway Topology Errors — {displayName}
            </h1>
            <p className="text-slate-300 leading-relaxed">
              Generated {new Date(report.generated).toLocaleString()} ·{" "}
              {report.total_issues.toLocaleString()} issue
              {report.total_issues === 1 ? "" : "s"} found
            </p>
          </div>

          {report.flagged.length === 0 ? (
            <div className="rounded-lg border border-slate-700 bg-slate-800/60 text-center py-16">
              <p className="text-slate-300 text-lg">
                No topology errors found for {displayName} ✨
              </p>
            </div>
          ) : (
            <div className="overflow-x-auto rounded-lg border border-slate-700 shadow-lg">
              <table className="w-full bg-slate-800 text-sm">
                <thead>
                  <tr className="bg-slate-900 text-left text-slate-300 uppercase text-xs tracking-wide">
                    <th className="px-4 py-3.5">Way ID</th>
                    <th className="px-4 py-3.5">Name</th>
                    <th className="px-4 py-3.5">Highway</th>
                    <th className="px-4 py-3.5">Version</th>
                    <th className="px-4 py-3.5">Last Edited</th>
                    <th className="px-4 py-3.5">Issue</th>
                    <th className="px-4 py-3.5">Edit</th>
                  </tr>
                </thead>
                <tbody>
                  {report.flagged.map((fw) => (
                    <tr
                      key={fw.way_id}
                      className="border-t border-slate-700 hover:bg-slate-700/50"
                    >
                      <td className="px-4 py-3.5 font-mono">
                        <a
                          href={fw.osm_url}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="text-blue-400 hover:underline"
                        >
                          {fw.way_id}
                        </a>
                      </td>
                      <td className="px-4 py-3.5 text-slate-200">
                        {fw.name || ""}
                      </td>
                      <td className="px-4 py-3.5">
                        <span className="rounded bg-slate-700 px-2 py-0.5 text-xs text-slate-200">
                          {fw.highway}
                        </span>
                      </td>
                      <td className="px-4 py-3.5 text-slate-300">
                        {fw.version}
                      </td>
                      <td className="px-4 py-3.5 text-slate-400">
                        {formatTimestamp(fw.timestamp)}
                      </td>
                      <td className="px-4 py-3.5 text-orange-300">
                        Start: {fw.start_connecting_highways || "none"}; End:{" "}
                        {fw.end_connecting_highways || "none"}
                      </td>
                      <td className="px-4 py-3.5 whitespace-nowrap">
                        <div className="flex gap-2">
                          <a
                            href={fw.id_url}
                            target="_blank"
                            rel="noopener noreferrer"
                            className="text-xs font-bold px-2 py-1 rounded bg-blue-700 text-white hover:opacity-90"
                          >
                            iD
                          </a>
                          <a
                            href={fw.josm_url}
                            target="_blank"
                            rel="noopener noreferrer"
                            className="text-xs font-bold px-2 py-1 rounded bg-slate-600 text-white hover:opacity-90"
                          >
                            JOSM
                          </a>
                          <a
                            href={fw.level0_url}
                            target="_blank"
                            rel="noopener noreferrer"
                            className="text-xs font-bold px-2 py-1 rounded bg-green-700 text-white hover:opacity-90 inline-flex items-center gap-1"
                          >
                            L0 <ExternalLink size={10} />
                          </a>
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
