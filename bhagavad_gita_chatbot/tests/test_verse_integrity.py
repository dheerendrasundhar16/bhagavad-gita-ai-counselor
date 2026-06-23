"""
test_verse_integrity.py
========================
Automated tests to verify Verse of the Day data integrity.

Run:
    cd bhagavad_gita_chatbot
    python -m pytest tests/test_verse_integrity.py -v

Requirements verified:
  - Ch4V7  → transliteration always contains 'yada yada hi dharmasya'
  - Ch12V13 → transliteration always contains 'adveshta sarva bhutanam'
  - Chapter number, verse number, sanskrit, transliteration, and translation
    are always fetched from the SAME atomic verse record.
  - No cross-verse field mixing is ever rendered.
"""

import sys
import os
import pytest

# Allow importing from parent package
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from vectorstore.database import GitaDatabase


# ── Fixtures ────────────────────────────────────────────────────────────────

@pytest.fixture(scope="module")
def db():
    """Shared database instance across all tests."""
    return GitaDatabase()


# ── Chapter 4 Verse 7 tests ─────────────────────────────────────────────────

class TestChapter4Verse7:
    """Ch4V7: Yada Yada Hi Dharmasya — Descent of God to re-establish Dharma."""

    TARGET_CH, TARGET_V = 4, 7
    EXPECTED_TRANSLIT_FRAGMENT = "yada yada hi"

    def test_verse_exists(self, db):
        """Ch4V7 must be present in the local verse cache."""
        verse = db.get_verse_by_reference(self.TARGET_CH, self.TARGET_V)
        assert verse is not None, f"Chapter {self.TARGET_CH} Verse {self.TARGET_V} not found in dataset"

    def test_chapter_number_matches(self, db):
        """Stored chapter_number must equal 4."""
        verse = db.get_verse_by_reference(self.TARGET_CH, self.TARGET_V)
        assert verse["chapter_number"] == self.TARGET_CH, (
            f"Expected chapter_number=4, got {verse['chapter_number']}"
        )

    def test_verse_number_matches(self, db):
        """Stored verse_number must equal 7."""
        verse = db.get_verse_by_reference(self.TARGET_CH, self.TARGET_V)
        assert verse["verse_number"] == self.TARGET_V, (
            f"Expected verse_number=7, got {verse['verse_number']}"
        )

    def test_transliteration_contains_yada_yada(self, db):
        """Transliteration MUST contain 'yada yada hi' (case-insensitive)."""
        verse = db.get_verse_by_reference(self.TARGET_CH, self.TARGET_V)
        translit = verse.get("transliteration", "").lower()
        assert self.EXPECTED_TRANSLIT_FRAGMENT in translit, (
            f"Ch4V7 transliteration should contain '{self.EXPECTED_TRANSLIT_FRAGMENT}'. "
            f"Got: '{translit[:80]}'"
        )

    def test_no_cross_verse_mixing(self, db):
        """Full verse record fields must ALL belong to Ch4V7 — no mixing."""
        full = db.get_full_verse_with_translations(self.TARGET_CH, self.TARGET_V)
        assert full is not None, "Full verse record with translations not found"

        stored_ch = full.get("chapter_number")
        stored_v  = full.get("verse_number")
        translit  = full.get("transliteration", "").lower()

        assert stored_ch == self.TARGET_CH, f"chapter_number mismatch: {stored_ch} != {self.TARGET_CH}"
        assert stored_v  == self.TARGET_V,  f"verse_number mismatch: {stored_v} != {self.TARGET_V}"
        assert self.EXPECTED_TRANSLIT_FRAGMENT in translit, (
            f"Cross-verse mixing detected: Ch{stored_ch}V{stored_v} "
            f"but transliteration is: '{translit[:80]}'"
        )

    def test_sanskrit_text_not_empty(self, db):
        """Sanskrit text must be present."""
        verse = db.get_verse_by_reference(self.TARGET_CH, self.TARGET_V)
        assert verse.get("text"), "Sanskrit text (text field) is empty for Ch4V7"

    def test_translation_available(self, db):
        """At least one translation must be available."""
        full = db.get_full_verse_with_translations(self.TARGET_CH, self.TARGET_V)
        translation = (
            full.get("sivananda")
            or full.get("gambirananda")
            or full.get("purohit")
            or full.get("adidevananda")
            or full.get("sankaranarayan")
        )
        assert translation, "No translation found for Ch4V7"


# ── Chapter 12 Verse 13 tests ────────────────────────────────────────────────

class TestChapter12Verse13:
    """Ch12V13: Adveshta Sarva Bhutanam — Qualities of a true devotee."""

    TARGET_CH, TARGET_V = 12, 13
    EXPECTED_TRANSLIT_FRAGMENT = "adveshta"

    def test_verse_exists(self, db):
        """Ch12V13 must be present in the local verse cache."""
        verse = db.get_verse_by_reference(self.TARGET_CH, self.TARGET_V)
        assert verse is not None, f"Chapter {self.TARGET_CH} Verse {self.TARGET_V} not found in dataset"

    def test_chapter_number_matches(self, db):
        """Stored chapter_number must equal 12."""
        verse = db.get_verse_by_reference(self.TARGET_CH, self.TARGET_V)
        assert verse["chapter_number"] == self.TARGET_CH, (
            f"Expected chapter_number=12, got {verse['chapter_number']}"
        )

    def test_verse_number_matches(self, db):
        """Stored verse_number must equal 13."""
        verse = db.get_verse_by_reference(self.TARGET_CH, self.TARGET_V)
        assert verse["verse_number"] == self.TARGET_V, (
            f"Expected verse_number=13, got {verse['verse_number']}"
        )

    def test_transliteration_contains_adveshta(self, db):
        """Transliteration MUST contain 'adveshta' (case-insensitive)."""
        verse = db.get_verse_by_reference(self.TARGET_CH, self.TARGET_V)
        translit = verse.get("transliteration", "").lower()
        assert self.EXPECTED_TRANSLIT_FRAGMENT in translit, (
            f"Ch12V13 transliteration should contain '{self.EXPECTED_TRANSLIT_FRAGMENT}'. "
            f"Got: '{translit[:80]}'"
        )

    def test_not_same_as_ch4v7(self, db):
        """
        Critical: Ch12V13 and Ch4V7 must have DIFFERENT transliterations.
        This directly catches the original bug (Yada Yada Hi being shown for Ch12V13).
        """
        v4_7  = db.get_verse_by_reference(4, 7)
        v12_13 = db.get_verse_by_reference(12, 13)
        assert v4_7 is not None and v12_13 is not None, "One of the verses is missing"

        t4_7   = v4_7.get("transliteration",  "").lower()
        t12_13 = v12_13.get("transliteration", "").lower()

        assert t4_7 != t12_13, (
            "BUG DETECTED: Ch4V7 and Ch12V13 have identical transliterations — "
            "verse data is being mixed!"
        )
        # More specific: Ch12V13 must NOT start with 'yada yada'
        assert not t12_13.startswith("yada"), (
            f"BUG DETECTED: Ch12V13 transliteration starts with 'yada' — "
            f"it's displaying Ch4V7's text: '{t12_13[:80]}'"
        )

    def test_no_cross_verse_mixing(self, db):
        """Full verse record fields must ALL belong to Ch12V13 — no mixing."""
        full = db.get_full_verse_with_translations(self.TARGET_CH, self.TARGET_V)
        assert full is not None, "Full verse record with translations not found"

        stored_ch = full.get("chapter_number")
        stored_v  = full.get("verse_number")
        translit  = full.get("transliteration", "").lower()

        assert stored_ch == self.TARGET_CH, f"chapter_number mismatch: {stored_ch} != {self.TARGET_CH}"
        assert stored_v  == self.TARGET_V,  f"verse_number mismatch: {stored_v} != {self.TARGET_V}"
        assert self.EXPECTED_TRANSLIT_FRAGMENT in translit, (
            f"Cross-verse mixing detected: Ch{stored_ch}V{stored_v} "
            f"but transliteration is: '{translit[:80]}'"
        )

    def test_sanskrit_text_not_empty(self, db):
        """Sanskrit text must be present."""
        verse = db.get_verse_by_reference(self.TARGET_CH, self.TARGET_V)
        assert verse.get("text"), "Sanskrit text (text field) is empty for Ch12V13"

    def test_translation_available(self, db):
        """At least one translation must be available."""
        full = db.get_full_verse_with_translations(self.TARGET_CH, self.TARGET_V)
        translation = (
            full.get("sivananda")
            or full.get("gambirananda")
            or full.get("purohit")
            or full.get("adidevananda")
            or full.get("sankaranarayan")
        )
        assert translation, "No translation found for Ch12V13"


# ── API Response Structure tests ─────────────────────────────────────────────

class TestVerseOfTheDayStructure:
    """Verify the recommended verse data structure from get_full_verse_with_translations."""

    REQUIRED_FIELDS = [
        "id", "chapter_number", "verse_number",
        "text",           # sanskrit
        "transliteration",
    ]
    OPTIONAL_TRANSLATION_FIELDS = [
        "sivananda", "gambirananda", "purohit", "adidevananda", "sankaranarayan"
    ]

    @pytest.mark.parametrize("ch,v", [
        (2, 47), (4, 7), (6, 5), (9, 22), (12, 13), (18, 66)
    ])
    def test_required_fields_present(self, db, ch, v):
        """Each popular verse must contain all required fields."""
        full = db.get_full_verse_with_translations(ch, v)
        assert full is not None, f"Verse Ch{ch}V{v} not found"
        for field in self.REQUIRED_FIELDS:
            assert field in full and full[field], (
                f"Ch{ch}V{v} missing required field '{field}'"
            )

    @pytest.mark.parametrize("ch,v", [
        (2, 47), (4, 7), (6, 5), (9, 22), (12, 13), (18, 66)
    ])
    def test_at_least_one_translation(self, db, ch, v):
        """Each popular verse must have at least one translation author."""
        full = db.get_full_verse_with_translations(ch, v)
        assert full is not None, f"Verse Ch{ch}V{v} not found"
        has_translation = any(
            full.get(f) for f in self.OPTIONAL_TRANSLATION_FIELDS
        )
        assert has_translation, f"Ch{ch}V{v} has no translation from any known author"

    @pytest.mark.parametrize("ch,v", [
        (2, 47), (4, 7), (6, 5), (9, 22), (12, 13), (18, 66)
    ])
    def test_chapter_verse_numbers_match_request(self, db, ch, v):
        """
        Fetching Ch{ch}V{v} must return a record with matching
        chapter_number and verse_number — no off-by-one or index drift.
        """
        full = db.get_full_verse_with_translations(ch, v)
        assert full is not None, f"Verse Ch{ch}V{v} not found"
        assert full["chapter_number"] == ch, (
            f"Requested Ch{ch} but got chapter_number={full['chapter_number']}"
        )
        assert full["verse_number"] == v, (
            f"Requested V{v} but got verse_number={full['verse_number']}"
        )
