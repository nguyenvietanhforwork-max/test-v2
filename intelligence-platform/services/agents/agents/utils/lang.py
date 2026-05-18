"""Cheap language detector — Vietnamese vs English heuristic.

Avoids importing a heavy detector for this two-language case.
"""

VN_MARKERS = set("ăâđêôơưếềệìíòóôồộùúýỳờởẵẳẫậặếềễấầẩẫậắằẳ")


def detect_language(text: str) -> str:
    sample = text[:2000].lower()
    if any(c in VN_MARKERS for c in sample):
        return "vi"
    return "en"
