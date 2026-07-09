import { useState, useEffect } from "react";
import Header from "./components/Header";
import SearchAndFilter from "./components/SearchAndFilter";
import ResultsList from "./components/ResultsList";
import StateReport from "./components/StateReport";

function parseStateHash(hash) {
  const match = hash.match(/^#\/state\/([^/]+)$/);
  return match ? match[1] : null;
}

export default function App() {
  const [results, setResults] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [searchQuery, setSearchQuery] = useState("");
  const [sortBy, setSortBy] = useState("name");
  const [filterStatus, setFilterStatus] = useState("all");
  const [activeState, setActiveState] = useState(() =>
    parseStateHash(window.location.hash),
  );

  useEffect(() => {
    const onHashChange = () =>
      setActiveState(parseStateHash(window.location.hash));
    window.addEventListener("hashchange", onHashChange);
    return () => window.removeEventListener("hashchange", onHashChange);
  }, []);

  useEffect(() => {
    const fetchResults = async () => {
      try {
        setLoading(true);
        const url = `${import.meta.env.BASE_URL}results.json`;
        const response = await fetch(url);
        if (!response.ok) {
          throw new Error(`Failed to fetch results from ${url}`);
        }
        const data = await response.json();
        setResults(data);
      } catch (err) {
        setError(err.message);
      } finally {
        setLoading(false);
      }
    };

    fetchResults();
  }, []);

  const getFilteredAndSortedResults = () => {
    if (!results || !results.results) return [];

    let filtered = results.results.filter((state) => {
      const matchesSearch = state.name
        .toLowerCase()
        .includes(searchQuery.toLowerCase());

      if (filterStatus === "success") {
        return matchesSearch && state.success;
      } else if (filterStatus === "failed") {
        return matchesSearch && !state.success;
      }

      return matchesSearch;
    });

    filtered.sort((a, b) => {
      switch (sortBy) {
        case "name":
          return a.name.localeCompare(b.name);
        case "issues-asc":
          return (a.issues || 0) - (b.issues || 0);
        case "issues-desc":
          return (b.issues || 0) - (a.issues || 0);
        default:
          return 0;
      }
    });

    return filtered;
  };

  const filteredResults = getFilteredAndSortedResults();

  const activeStateInfo = activeState
    ? results?.results?.find((s) => s.state === activeState)
    : null;

  return (
    <div className="min-h-screen bg-linear-to-br from-slate-900 via-slate-800 to-slate-900">
      <div className="container mx-auto px-6 py-10 sm:px-8 lg:px-12">
        {activeState ? (
          <StateReport
            stateSlug={activeState}
            stateName={activeStateInfo?.name}
            onBack={() => {
              window.location.hash = "";
              setActiveState(null);
            }}
          />
        ) : loading ? (
          <div className="flex flex-col items-center justify-center h-screen gap-4">
            <div className="h-10 w-10 animate-spin rounded-full border-4 border-slate-600 border-t-blue-500" />
            <p className="text-slate-300">Loading results…</p>
          </div>
        ) : error ? (
          <div className="max-w-2xl mx-auto rounded-lg border border-red-500/30 bg-red-500/10 p-5">
            <p className="font-semibold text-red-400">Failed to load results</p>
            <p className="text-sm text-red-300/90 mt-1">{error}</p>
          </div>
        ) : (
          <div className="space-y-10">
            <Header results={results} />
            <SearchAndFilter
              searchQuery={searchQuery}
              onSearchChange={setSearchQuery}
              sortBy={sortBy}
              onSortChange={setSortBy}
              filterStatus={filterStatus}
              onFilterChange={setFilterStatus}
            />
            <ResultsList results={filteredResults} />
          </div>
        )}
      </div>
    </div>
  );
}
