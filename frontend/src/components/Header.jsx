export default function Header({ results }) {
  if (!results) return null;

  const totalStates = results.total_states || 0;
  const totalIssues = results.total_issues || 0;
  const successfulAnalyses = results.successful_analyses || 0;
  const lastUpdated = results.timestamp
    ? new Date(results.timestamp).toLocaleString()
    : "Unknown";

  const stats = [
    { label: "Total States", value: totalStates, className: "text-white" },
    {
      label: "Total Issues Found",
      value: totalIssues,
      className: "text-orange-400",
    },
    {
      label: "Successful Analyses",
      value: successfulAnalyses,
      className: "text-green-400",
    },
    {
      label: "Last Updated",
      value: lastUpdated,
      className: "text-white text-sm",
    },
  ];

  return (
    <div className="border-b border-slate-700 pb-10">
      <div className="mb-8">
        <h1 className="text-4xl font-bold text-white mb-3">
          🗺️ OSM Highway Topology Errors
        </h1>
        <p className="text-slate-300 leading-relaxed">
          Automated analysis of OpenStreetMap highway topology across US states
        </p>
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-5">
        {stats.map((stat) => (
          <div
            key={stat.label}
            className="rounded-lg border border-slate-700 bg-slate-800/60 p-5 transition-colors hover:border-slate-600"
          >
            <p className="text-sm text-slate-400 mb-2">{stat.label}</p>
            <p className={`text-3xl font-bold truncate ${stat.className}`}>
              {stat.value}
            </p>
          </div>
        ))}
      </div>
    </div>
  );
}
