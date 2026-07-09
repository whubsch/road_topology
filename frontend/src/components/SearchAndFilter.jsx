import { Search, X } from "lucide-react";

export default function SearchAndFilter({
  searchQuery,
  onSearchChange,
  sortBy,
  onSortChange,
  filterStatus,
  onFilterChange,
}) {
  return (
    <div className="rounded-lg border border-slate-700 bg-slate-800/60 p-5">
      <div className="flex flex-col gap-5 md:flex-row md:items-end">
        <div className="flex-1">
          <label
            htmlFor="search"
            className="mb-1 block text-xs font-medium text-slate-400"
          >
            Search
          </label>
          <div className="relative">
            <Search
              size={16}
              className="pointer-events-none absolute left-3 top-1/2 -translate-y-1/2 text-slate-400"
            />
            <input
              id="search"
              type="text"
              value={searchQuery}
              onChange={(e) => onSearchChange(e.target.value)}
              placeholder="Search states…"
              className="w-full rounded-md border border-slate-600 bg-slate-900 py-2 pl-9 pr-9 text-sm text-white placeholder:text-slate-400 focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
            {searchQuery && (
              <button
                type="button"
                onClick={() => onSearchChange("")}
                aria-label="Clear search"
                className="absolute right-2 top-1/2 -translate-y-1/2 text-slate-400 hover:text-slate-200"
              >
                <X size={16} />
              </button>
            )}
          </div>
        </div>

        <div className="md:w-48">
          <label
            htmlFor="sort"
            className="mb-1 block text-xs font-medium text-slate-400"
          >
            Sort
          </label>
          <select
            id="sort"
            value={sortBy}
            onChange={(e) => onSortChange(e.target.value)}
            className="w-full rounded-md border border-slate-600 bg-slate-900 py-2 px-3 text-sm text-white focus:outline-none focus:ring-2 focus:ring-blue-500"
          >
            <option value="name">Name (A–Z)</option>
            <option value="issues-asc">Issues (Low to High)</option>
            <option value="issues-desc">Issues (High to Low)</option>
          </select>
        </div>

        <div className="md:w-48">
          <label
            htmlFor="filter"
            className="mb-1 block text-xs font-medium text-slate-400"
          >
            Filter
          </label>
          <select
            id="filter"
            value={filterStatus}
            onChange={(e) => onFilterChange(e.target.value)}
            className="w-full rounded-md border border-slate-600 bg-slate-900 py-2 px-3 text-sm text-white focus:outline-none focus:ring-2 focus:ring-blue-500"
          >
            <option value="all">All Results</option>
            <option value="success">Successful Only</option>
            <option value="failed">Failed Only</option>
          </select>
        </div>
      </div>
    </div>
  );
}
