"""
verse_parser.py

Utility to detect explicit verse references in user queries
(e.g. "12.34", "chapter 12 verse 5", "BG 2.47", "Gita 4:7").
Returns (chapter, verse) tuples or None if no reference is found.
"""
import re
from typing import Optional, Tuple


# Chapter → max verse count for all 18 chapters of Bhagavad Gita
CHAPTER_VERSE_COUNTS = {
    1: 47, 2: 72, 3: 43, 4: 42, 5: 29,
    6: 47, 7: 30, 8: 28, 9: 34, 10: 42,
    11: 55, 12: 20, 13: 35, 14: 27, 15: 20,
    16: 24, 17: 28, 18: 78
}


def parse_verse_reference(query: str) -> Optional[Tuple[int, int]]:
    """
    Parses a user query for an explicit Bhagavad Gita verse reference.

    Handles patterns like:
      - "12.34"  /  "12:34"
      - "chapter 12, verse 5"  /  "ch 12 v 5"
      - "BG 2.47"  /  "Gita 4:7"
      - "verse 2.47"

    Returns:
        (chapter, verse) tuple if a valid-format reference is found, else None.
        NOTE: the verse may still be out of range for the chapter.
    """
    q = query.strip()

    # Pattern 1: numeric dot/colon notation  e.g. "12.34" or "BG 12:34" or "Gita 12.34"
    pattern_dot = re.search(
        r'(?:BG|Gita|Geeta|Gita-|chapter)?\s*(\d{1,2})[.:](\d{1,3})',
        q, re.IGNORECASE
    )
    if pattern_dot:
        ch = int(pattern_dot.group(1))
        vs = int(pattern_dot.group(2))
        if 1 <= ch <= 18:
            return (ch, vs)

    # Pattern 2: "chapter X verse Y" / "ch X v Y"
    pattern_words = re.search(
        r'ch(?:apter)?\s*(\d{1,2})[,\s]+(?:verse|v|shloka|sloka)\s*(\d{1,3})',
        q, re.IGNORECASE
    )
    if pattern_words:
        ch = int(pattern_words.group(1))
        vs = int(pattern_words.group(2))
        if 1 <= ch <= 18:
            return (ch, vs)

    return None


def validate_verse(chapter: int, verse: int) -> Tuple[bool, str]:
    """
    Validates whether a (chapter, verse) combination exists in the Bhagavad Gita.

    Returns:
        (is_valid, error_message)
    """
    if chapter not in CHAPTER_VERSE_COUNTS:
        return False, f"Chapter {chapter} does not exist in the Bhagavad Gita (valid: 1–18)."

    max_verse = CHAPTER_VERSE_COUNTS[chapter]
    if verse < 1 or verse > max_verse:
        return False, (
            f"Chapter {chapter} of the Bhagavad Gita has only {max_verse} verses "
            f"(you asked for verse {verse}). Please check the reference."
        )

    return True, ""
