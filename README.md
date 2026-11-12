# Rack Sorter

## What Rack Sorter Does

Rack Sorter is a fashion discovery app that helps users find clothing listings visually similar to a reference image. A user uploads a photo, the app analyzes the image, and then it searches Vinted for items that match the visual style and selected filters. Results can be refined in place with "More/Less like this" or with per-trait controls (sleeves, neckline, length, pattern, fit, material).

## Features

- Image upload with automatic keyword, colour and category suggestions.
- Marketplace filters for size, category, colour, price and condition.
- Visual similarity ranking using a greyscale DINOv2 embedding, so matches follow shape and silhouette rather than exact colour.
- Relevance feedback:
  - **More / Less** steers the visual intent toward or away from a listing.
  - **⚙ Tune** applies a fixed trait (e.g. more sleeves, less pattern) relative to the uploaded photo.
- Each feedback request also fetches one more catalogue page, so refined searches can surface listings the first page did not contain.
- Optional debug view of the trait axes behind the `Tune` sheet.


## How Client and Server Work Together

The app is split into two main parts:

- The **client** is the browser interface. It handles image uploads, user inputs and filter selection, displays suggestions, and shows ranked results.
- The **server** is the backend engine. It performs the image analysis, collects listing data from Vinted, computes similarity to the uploaded image, and stores search history.

The two parts communicate over HTTP.

1. The user chooses an image and optionally edits the keyword.
2. The browser sends the image to the backend.
3. The backend analyzes the image and returns suggested tags, colours, and a simple category hint.
4. The browser shows those suggestions and lets the user refine the search.
5. When the user starts the search, the browser sends the selected filters and the image upload reference to the backend.
6. The backend queries Vinted, ranks listings based on visual similarity, and returns the best matches.
7. The browser renders those results in a responsive grid.
8. Feedback on a card re-ranks the pool, pulls one extra catalogue page, and returns the updated grid.

This flow ensures the frontend stays focused on user interaction and display, while the backend handles the heavier work of analysis, scraping, ranking, and storage.

## Refining Results

Every listing card has three actions:

- **＋ More** — treat this listing as a stronger example of what the user wants.
- **－ Less** — treat it as something to move away from.
- **⚙ Tune** — open the trait sheet. Traits are fixed (`sleeves`, `neckline`, `length`, `pattern`, `fit`, `material`) and are applied relative to the uploaded photo: with a sleeveless top selected, "more sleeves" moves toward sleeved items.

## Client Architecture

The client is a React application organized around three broad responsibilities:

- **User interface:** components for uploading images, entering keywords, showing suggestions, adjusting filters, and displaying results.
- **State management:** hooks manage the current image analysis, search filters, result list, and UI panels.
- **API communication:** a small layer sends requests to the backend and reads responses.

The app keeps the experience smooth by separating concerns:

- The image upload and keyword entry are handled in the main page.
- Filter state is maintained in a reusable state layer so the UI stays consistent.
- Search results are fetched and then rendered as cards that show both the product image and how well it matches the reference.

## Server Architecture

The server is a FastAPI application built around four main capabilities:

- **Image understanding:** it analyzes the uploaded photo and extracts visual signals such as likely garment type, colour family, and relevant descriptive tags.
- **Data collection:** it queries Vinted based on the user's selected search criteria and gathers the raw listing data.
- **Similarity ranking:** it compares the uploaded image against candidate listing images and ranks them by how closely they match.
- **Feedback steering:** it folds "More/Less" and trait feedback over that baseline, and can fetch another catalogue page so each round has fresh candidates.

It also keeps a lightweight local store of uploads, search attempts, scraped results and feedback so that the app can keep a record of what was searched and how it performed.

## Broad Module Roles

### Client-side Roles

- The UI layer displays the workflow and user controls.
- The state layer remembers what the user selected, what the image analysis produced, and what results were returned.
- The API layer is the bridge between browser actions and backend processing.

### Server-side Roles

- The analysis service interprets the uploaded image and turns it into search-friendly signals.
- The scraping service fetches candidate listings from Vinted.
- The ranking service evaluates how well each listing matches the reference image.
- The feedback services blend visual feedback, project trait axes, and page through more catalogue results.
- The persistence layer stores uploads, search history, candidate embeddings and feedback in a local database.

The backend exposes the pipeline over a small HTTP API: `/analyze`, `/fetch_initial`, `/rerank` and a read-only `/trait-profile` debug endpoint. `/compare` remains for debugging but is no longer used by the client.

## Why It’s Structured This Way

This architecture keeps responsibilities clean:

- The browser does not need to know about the scraping or ranking details.
- The backend can evolve its image analysis and ranking logic independently of the UI.
- The frontend can stay responsive while the backend does heavier processing.

## Running the App Locally

- Server:
  - `cd server`
  - `python -m venv .venv && source .venv/bin/activate`
  - `pip install -r requirements.txt`
  - `uvicorn main:app --reload --host 127.0.0.1 --port 8000`

- Client (in a second terminal):
  - `cd client`
  - `npm install`
  - `npm run dev`

`npm run dev` regenerates `client/src/types/api.d.ts` from the running server (`/openapi.json`) and then starts Vite on <http://localhost:3000>. The client proxies `/analyze`, `/fetch_initial`, `/rerank`, `/trait-profile` and `/compare` to the backend on port 8000.

## Tests

- Server: `cd server && .venv/bin/python -m pytest tests -q`
- Client: `cd client && npx tsc --noEmit` (there is no client test runner yet)
- Production build: `cd client && npm run build`

---

This README explains the architecture at a high level; implementation details live in the design docs and module docstrings.