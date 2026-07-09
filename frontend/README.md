# Road Topology Frontend

React-based interactive dashboard for viewing OSM highway topology error analysis results.

## Features

- **Interactive Dashboard**: View all state analysis results with real-time search and filtering
- **Smart Sorting**: Sort by state name or issue count (ascending/descending)
- **Status Filtering**: Filter by successful analyses or failed runs
- **Live Statistics**: Dashboard displays total states, total issues, and success rate
- **Responsive Design**: Works on desktop, tablet, and mobile devices
- **State Reports**: Links to detailed HTML reports for each state
- **HeroUI Components**: Modern, accessible UI components with Tailwind CSS

## Development

### Prerequisites

- Node.js 18+ (recommended: 20)
- npm or yarn

### Installation

```bash
cd frontend
npm install
```

### Development Server

```bash
npm run dev
```

The app will be available at `http://localhost:5173/road_topology/`

### Building for Production

```bash
npm run build
```

Output is generated in `../gh-pages` for GitHub Pages deployment.

## Data Format

The frontend expects a `results.json` file with the following structure:

```json
{
  "timestamp": "2024-01-15T10:30:00Z",
  "total_states": 50,
  "total_issues": 1234,
  "successful_analyses": 48,
  "results": [
    {
      "state": "vermont",
      "name": "Vermont",
      "issues": 42,
      "success": true
    }
  ]
}
```

## Component Structure

- **App.jsx** - Main application component, handles data fetching and state management
- **Header.jsx** - Dashboard header with statistics cards
- **SearchAndFilter.jsx** - Search, sort, and filter controls
- **ResultsList.jsx** - Grid display of state results

## Environment

- Built with Vite for fast development and optimized production builds
- Uses React 18+ for modern component patterns
- HeroUI provides accessible, customizable components
- Tailwind CSS for styling
