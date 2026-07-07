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

Before the DINOv2 embedding is generated generation, images are converted to greyscale. This reduces the influence of colour during similarity retrieval and encourages the ranking model to focus on garment structure, silhouette and shape rather than exact colour matches.

The workflow is: ```Greyscale Image -> DINOv2 -> 768-dimensional vector```

Example: ```python [0.031, -0.284, 0.712, ...]```

Embeddings are normalised before comparison to ensure similarity calculations depend on vector direction rather than magnitude.

```embedding /= embedding.norm(...)```

In particular, DINOv2 performs strongly on these without requiring additional fine-tuning.


### Initial ranking

The uploaded image acts as the anchor image.

For each candidate embedding, cosine similarity is calculated against the anchor embedding.

Candidates are then sorted by similarity score in descending order and the highest scoring items are returned to the frontend.


## Step 3 - receiving feedback

When a user selects "More Like This":

1. Retrieve the selected item's embedding.
2. Compare it against all other candidate embeddings.
3. Calculate a feedback similarity score.
4. Blend the original retrieval score with the feedback score.

Current formula, if user selects
- More like this: ```0.7 × Original Similarity + 0.3 × Feedback Similarity```
- Less like this: ```0.8 × Original Similarity -
0.2 × Feedback Similarity```

This promotes items that are visually more/less similar to both:
* the uploaded image
* the selected item


The reranking system assumes:

> Similarity to a positively selected item is a useful proxy for user intent.

This is a simplification.

The system does not currently distinguish whether the user prefers an item because of:

* Style
* Fit
* Material
* Colour
* Brand

All feedback is treated as general visual preference.
