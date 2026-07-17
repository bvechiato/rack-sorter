# Rack Sorter

## What Rack Sorter Does

Rack Sorter is a fashion discovery app that helps users find clothing listings visually similar to a reference image. A user uploads a photo, the app analyzes the image, and then it searches Vinted for items that match the visual style and selected filters.

![til](./assets/racksorter_wip.gif)


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

This flow ensures the frontend stays focused on user interaction and display, while the backend handles the heavier work of analysis, scraping, ranking, and storage.

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

The server is a FastAPI application built around three main capabilities:

- **Image understanding:** it analyzes the uploaded photo and extracts visual signals such as likely garment type, colour family, and relevant descriptive tags.
- **Data collection:** it queries Vinted based on the user's selected search criteria and gathers the raw listing data.
- **Similarity ranking:** it compares the uploaded image against candidate listing images and ranks them by how closely they match.

It also keeps a lightweight local store of uploads, search attempts, and scraped results so that the app can keep a record of what was searched and how it performed.

## Broad Module Roles

### Client-side Roles

- The UI layer displays the workflow and user controls.
- The state layer remembers what the user selected, what the image analysis produced, and what results were returned.
- The API layer is the bridge between browser actions and backend processing.

### Server-side Roles

- The analysis service interprets the uploaded image and turns it into search-friendly signals.
- The scraping service fetches candidate listings from Vinted.
- The ranking service evaluates how well each listing matches the reference image.
- The persistence layer stores uploads and search history in a local database.

## Why It’s Structured This Way

This architecture keeps responsibilities clean:

- The browser does not need to know about the scraping or ranking details.
- The backend can evolve its image analysis and ranking logic independently of the UI.
- The frontend can stay responsive while the backend does heavier processing.

## Running the App Locally

- Client:
  - `cd client`
  - `npm install`
  - `npm run dev`

- Server:
  - `cd server`
  - `pip install -r requirements.txt`
  - `uvicorn main:app --reload --host 127.0.0.1 --port 8000`

---

This README now explains the architecture at a higher level, avoiding implementation details and function names.