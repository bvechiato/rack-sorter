# RackSorter - React Migration

This project has been successfully migrated from vanilla JavaScript to React with Vite.

## Project Structure

```
rack-sorter/
├── src/
│   ├── components/        # React components
│   ├── styles/           # CSS styles
│   ├── api.js            # API calls
│   ├── App.jsx           # Main App component
│   └── main.jsx          # React entry point
├── backend/              # Python FastAPI backend (unchanged)
├── dist/                 # Build output (generated)
├── package.json          # NPM dependencies
├── vite.config.js        # Vite configuration
├── index.html            # HTML template
└── main.py              # FastAPI server
```

## Development Setup

### Prerequisites
- Node.js 16+ and npm
- Python 3.8+ with dependencies from `requirements.txt`

### Installation

1. **Install frontend dependencies:**
   ```bash
   npm install
   ```

2. **Install backend dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

### Running the Application

#### Option 1: Development Mode (Recommended)
In one terminal, start the backend:
```bash
python -m uvicorn main:app --host 0.0.0.0 --port 8000
```

In another terminal, start the Vite dev server:
```bash
npm run dev
```

The app will be available at `http://localhost:3000` with hot reload enabled.

#### Option 2: Production Build
Build the React app:
```bash
npm run build
```

Then run the backend (which will serve the built app):
```bash
python -m uvicorn main:app --host 0.0.0.0 --port 8000
```

The app will be available at `http://localhost:8000`.

## What Changed

### Removed (old vanilla JS)
- `frontend/main.js` (now `src/App.jsx`)
- `frontend/chips.js` (functionality in React components)
- Inline DOM manipulation

### Added (React)
- Component-based architecture
- React hooks for state management (useState, useEffect)
- Vite for fast builds and HMR
- Modular component structure

### Functionality Preserved
✓ Image upload and analysis
✓ Keyword suggestions
✓ Filter options (size, price, category, color, condition)
✓ Search/scraping
✓ Vector weight sliders
✓ Product grid display
✓ LocalStorage persistence

### Styling
The original CSS has been preserved and moved to `src/styles/index.css`. All visual styling remains identical to the original.

## Build & Deploy

The application is built with Vite which produces optimized bundles in the `dist/` directory. The backend FastAPI server serves both the API endpoints and the static frontend assets.

### For Production
1. Run `npm run build` to generate optimized assets
2. Run the FastAPI server which will serve the built app
3. Access at `http://localhost:8000` (or your deployment URL)
