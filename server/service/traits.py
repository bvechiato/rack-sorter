"""Fixed trait vocabulary and FashionCLIP axis construction.

A trait is a signed direction in CLIP image space, built once from a prompt pair:

    axis = normalise(embed(text_positive) - embed(text_negative))

Candidates are then scored by their projection onto that axis. See
`docs/design/trait-aspect-feedback.md`.
"""

from typing import Dict, Literal, Optional

import numpy as np

# Closed vocabulary. The client mirrors this list in `client/src/static/constants.ts`;
# unknown values are rejected at the API edge so legacy free-text chips never reach
# the scorer again.
Trait = Literal["sleeves", "neckline", "length", "pattern", "fit", "material"]

TRAIT_KEYS: tuple[str, ...] = ("sleeves", "neckline", "length", "pattern", "fit", "material")

# (positive prompt, negative prompt) per trait. Prompts describe the *positive* end
# of the axis; `s_i` therefore grows toward the positive pole.
TRAIT_PROMPTS: Dict[str, tuple[str, str]] = {
    "sleeves": ("long sleeves", "sleeveless garment"),
    "neckline": ("collared buttoned neckline", "open low neckline"),
    "length": ("long maxi length garment", "cropped short length garment"),
    "pattern": ("floral printed pattern", "plain solid colour"),
    "fit": ("oversized loose fit", "tight fitted silhouette"),
    # Beta: weakest axis, kept behind the vocabulary flag until eval justifies it.
    "material": ("knitted textured fabric", "smooth woven fabric"),
}

W_MORE = 0.45
W_LESS = 0.60
# Below this the clicked item is "the same" as the anchor on the trait, so the event
# is skipped instead of being applied with an arbitrary sign.
TRAIT_DEADBAND = 0.02
# Candidate projections are standardised against the *current pool* before weighting:
# CLIP axes have wildly different spreads (length std ≈ 0.04, pattern ≈ 0.08), so raw
# projections made feedback ~10× weaker than intended and trait-dependent. One standard
# deviation of the pool is now worth one weight unit.
TRAIT_Z_LIMIT = 3.0
# A pool whose projection spread is below this is flat on that axis (e.g. a pool of one
# image, or a degenerate axis); the event is skipped and logged rather than applied.
MIN_TRAIT_SPREAD = 1e-3
# Clamp on the *total* trait contribution per item, applied after the whole history
# is folded, so event order cannot change the result.
MAX_TRAIT_ADJUSTMENT = 0.8

_axes: Dict[str, np.ndarray] = {}


def get_trait_axes() -> Dict[str, np.ndarray]:
    """Build (and cache) the unit axis for every trait.

    The CLIP model is imported lazily so importing this module (e.g. from tests or
    the DTO layer) never loads torch.
    """
    if _axes:
        return _axes

    from service.identifier import get_text_embeddings

    prompts = []
    for key in TRAIT_KEYS:
        positive, negative = TRAIT_PROMPTS[key]
        prompts.extend([positive, negative])

    embeddings = get_text_embeddings(prompts)

    for index, key in enumerate(TRAIT_KEYS):
        positive = embeddings[index * 2]
        negative = embeddings[index * 2 + 1]
        axis = positive - negative
        norm = np.linalg.norm(axis)
        if norm == 0:
            raise ValueError(f"Degenerate trait axis for '{key}': prompts embed identically")
        _axes[key] = axis / norm

    return _axes


def is_trait(value: Optional[str]) -> bool:
    return value in TRAIT_PROMPTS
