# Retrieval Pipeline
RackSorter is an image-based fashion retrieval system that combines:

* Zero-shot image classification (FashionCLIP)
* Visual similarity retrieval (DINOv2)
* Interactive relevance feedback

The system intentionally separates semantic understanding from visual retrieval.

Different models are used for each task because they optimise for different objectives.


## Step 1 - understanding the initial upload

The retrieval system needs to understand an uploaded garment before constructing a marketplace query, such as
1. Category (hoodies, dresses, tops)
2. Colour
3. Characteristic attribute (ruched, sleeveless, cropped, etc etc)

General-purpose image classification models typically predict object classes but provide limited fashion-specific understanding.

Model: ```patrickjohncyh/fashion-clip ```

Selected because:
* It is trained on fashion datasets.
* It supports image-text similarity.
* It enables zero-shot classification.
* New attributes can be introduced without retraining.

The image is compared against every candidate tag and the highest scoring labels are returned.

This allows the system to generate structured fashion metadata without maintaining a custom classifier.

## Step 2 - understanding similarity between retrieved items

The request created in 1) is translated into marketplace-specific query parameters.

The scraper retrieves a candidate pool of listings.

At this stage the system prioritises recall rather than ranking quality.

The objective is to retrieve enough potentially relevant items for downstream reranking.

### Embedding Generation

For every image involved in retrieval, we have:
* User uploaded image
* Marketplace candidate images

Before the DINOv2 embedding is generated, images are converted to greyscale. This reduces the influence of colour during similarity retrieval and encourages the ranking model to focus on garment structure, silhouette and shape rather than exact colour matches.

The workflow is: ```Greyscale Image -> DINOv2 -> 768-dimensional vector```

Example: ```python [0.031, -0.284, 0.712, ...]```

Embeddings are normalised before comparison to ensure similarity calculations depend on vector direction rather than magnitude.

```embedding /= embedding.norm(...)```

DINOv2 performs strongly on these without requiring additional fine-tuning though this could be experimented with further.


### Initial ranking

The uploaded image acts as the anchor image.

For each candidate embedding, cosine similarity is calculated against the anchor embedding.

Candidates are then sorted by similarity score in descending order and the highest scoring items are returned to the frontend.


## Step 3 - receiving feedback

### General feedback - "More/less like this"
When a user selects "More Like This":

1. Retrieve the selected item's DINO embedding.
2. Build a new visual intent vector over raw DINO space.
3. Compare every candidate against that intent.
4. Sort by the resulting similarity.

The intent is the centre of mass of the positive examples, with negative examples pulled away:

```python
intent = mean(MORE embeddings)
if negative feedback:
    intent -= 0.3 * mean(LESS embeddings)
# If there are no positive examples, start from the anchor instead.
intent = intent / norm(intent)
```

Candidates are then scored by cosine similarity to `intent`. This promotes items that are visually closer to the listings the user liked and further from the ones they disliked. General feedback accumulates across taps; the trait path below is the one that supersedes contradictory choices.

The reranking system assumes:

> Similarity to a positively selected item is a useful proxy for user intent.

This is a simplification: "More like this" does not say *why* an item is preferred (style, fit, material, brand, colour). Trait feedback exists to express that "why".

### Trait-specific feedback

Trait feedback replaces the earlier free-text chips with a closed vocabulary:

| Key | Axis prompts (positive / negative) |
|---|---|
| `sleeves` | `"long sleeves"` / `"sleeveless garment"` |
| `neckline` | `"collared buttoned neckline"` / `"open low neckline"` |
| `length` | `"long maxi length garment"` / `"cropped short length garment"` |
| `pattern` | `"floral printed pattern"` / `"plain solid colour"` |
| `fit` | `"oversized loose fit"` / `"tight fitted silhouette"` |
| `material` | `"knitted textured fabric"` / `"smooth woven fabric"` (beta) |

Each trait is a 512-d FashionCLIP axis built once from its prompt pair:

```python
axis = normalize(embed(text_pos) - embed(text_neg))
```

Candidates already carry a FashionCLIP image vector, recorded at ingest while the image bytes are in memory. The score is the candidate's projection on the axis:

```python
s = dot(normalize(clip_item), axis)
```

The **clicked listing supplies the direction**, and `MORE`/`LESS` supplies the polarity, so the feedback is relative to the uploaded photo. If the user clicks a sleeveless top, `LESS sleeves` means "toward sleeved", not "toward sleeveless". If the clicked listing is within `0.02` of the anchor on that axis, the event is skipped and counted rather than applied with an arbitrary sign.

#### Pool-relative standardisation

Raw CLIP projections have different spreads per axis (roughly `0.04` for `length`, `0.08` for `pattern` on the tracked data), which made the same tap feel much weaker on some traits. Before weighting, every candidate projection is standardised against the current pool:

```python
z = clip((s - mean_pool) / std_pool, -3.0, 3.0)
```

So one weight unit means one standard deviation of *this* pool. The weights and cap are:

- `MORE`: `+0.45 * direction * z`
- `LESS`: `-0.60 * direction * z`
- total trait contribution per listing clamped to `[-0.8, +0.8]`, applied after the whole feedback history is folded.

A pool whose spread on an axis is flat (`std < 1e-3`) cannot be standardised; the event is skipped and reported as `skipped_degenerate`.

#### Anchoring and history

- The anchor is the uploaded image's FashionCLIP vector, computed once per upload and cached.
- Only the last choice per `(item_url, concept)` is folded, so `MORE sleeves` then `LESS sleeves` reflects the final intent instead of partially cancelling.
- The full history is replayed on every request, so reranking is deterministic and idempotent.
- Legacy rows without a CLIP vector are encoded lazily, under a per-upload lock; items that still fail contribute `0` and are counted in the log.

#### Fetching more candidates

A tap only reorders what is already in the pool, so `/rerank` first pulls one more Vinted catalogue page:

- the stored query parameters from `/fetch_initial` are reused with `&page=N`;
- the cursor starts at page 2 and is capped at page 8 per upload;
- new listings are deduped by URL and merged into the same query;
- `/fetch_initial` resets the cursor for a new search;
- the response returns `new_items` so the UI can say `+N new items from a wider search`;
- a blocked or slow page is logged and the rerank proceeds on the existing pool. Feedback is persisted before the scrape, so it is never lost.

#### Observability

Trait scoring logs a stats line for every rerank: applied/superseded events, deadband skips, flat-axis skips, missing clicked vectors, candidates missing embeddings and clamp hits. A no-op is always visible in the log rather than silently returning the previous order.

`GET /trait-profile?upload_id=&item_url=` returns the raw projections for the anchor, the pool mean/std and the mean of the visible top N. The client uses it to draw the collapsible **Trait axes** debug diagram in the `Tune` sheet, and refetches it after every feedback event. This endpoint is read-only and is not part of the ranking path.

The full design, verification notes and trade-offs are in [`docs/design/trait-aspect-feedback.md`](../docs/design/trait-aspect-feedback.md).

## API surface

| Endpoint | Purpose |
|---|---|
| `POST /analyze` | Upload the anchor image; returns an upload id, tags, colour and category hints. |
| `POST /fetch_initial` | Scrape the first catalogue page, embed candidates, return the ranked pool. |
| `POST /rerank` | Persist feedback, fetch one extra page, replay the feedback history and return the updated pool plus `new_items`. |
| `GET /trait-profile` | Debug payload for the axes diagram. |
| `POST /compare` | Legacy item comparison; no longer called by the UI. |

## Running the server

```bash
cd server
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
uvicorn main:app --reload --host 127.0.0.1 --port 8000
```

Run the tests with:

```bash
cd server
.venv/bin/python -m pytest tests -q
```

The suite injects synthetic axis/candidate vectors, so the scoring assertions never call CLIP or DINO.


