import pytest

from app.services.questions import normalise_question


def test_strips_surrounding_whitespace():
    assert normalise_question("  How does this evidence hold up?  ") == "How does this evidence hold up?"


def test_keeps_internal_spacing():
    question = "First sentence.  Second sentence stays as written."
    assert normalise_question(question) == question


def test_rejects_a_blank_question():
    with pytest.raises(ValueError):
        normalise_question("   ")
