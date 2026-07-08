from types import SimpleNamespace

import service.identifier as identifier


class FakeImage:
    def convert(self, _mode):
        return self


class FakeProcessor:
    def __call__(self, **kwargs):
        return {"text": kwargs["text"], "images": kwargs["images"]}


class FakeLogits:
    def __init__(self, values):
        self.values = values

    def softmax(self, dim=-1):
        return FakeProbabilities(self.values)


class FakeProbabilities:
    def __init__(self, values):
        self.values = values

    def numpy(self):
        return [self.values]


class FakeModel:
    def __init__(self, values):
        self.values = values

    def __call__(self, **kwargs):
        return SimpleNamespace(logits_per_image=FakeLogits(self.values))


def test_zero_shot_classification_filters_below_threshold(monkeypatch):
    monkeypatch.setattr(identifier, "processor", FakeProcessor())
    monkeypatch.setattr(identifier, "model", FakeModel([0.6, 0.2, 0.1, 0.1]))

    result = identifier.zero_shot_classification(FakeImage(), ["shirt", "pants", "jacket", "coat"], limit=3)

    assert result["archetype"] == "shirt"
    assert result["classified_tags"] == ["shirt", "pants", "jacket"]


def test_extract_tags_from_image_builds_expected_payload(monkeypatch):
    monkeypatch.setattr(identifier.Image, "open", lambda _image: FakeImage())

    def fake_zero_shot_classification(image, candidate_tags, limit=5):
        if candidate_tags == list(identifier.CATEGORY_HIERARCHY.keys()):
            return {"archetype": "Outerwear", "classified_tags": ["Outerwear"]}
        if candidate_tags == ["All clothes"]:
            return {"archetype": "Coat", "classified_tags": ["Coat"]}
        if candidate_tags == identifier.CANDIDATE_TAGS:
            return {"archetype": "shirt", "classified_tags": ["shirt"]}
        return {"archetype": "blue", "classified_tags": ["blue"]}

    monkeypatch.setattr(identifier, "zero_shot_classification", fake_zero_shot_classification)

    payload = identifier.extract_tags_from_image(b"fake-bytes")

    assert payload["archetype"] == "shirt"
    assert payload["category_archetype"] == "Coat"
    assert payload["colour_archetype"] == "blue"
