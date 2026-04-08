MIN_QUESTION_LENGTH = 10
MAX_QUESTION_LENGTH = 2000


def normalise_question(question: str) -> str:
    """Trim a question and reject values the desk should not store.

    Internal spacing is left alone. A research question may be more than one
    sentence, and collapsing it would change what the person wrote.
    """

    cleaned = question.strip()
    if len(cleaned) < MIN_QUESTION_LENGTH:
        raise ValueError(
            "Write at least 10 characters so the question is specific enough to research later."
        )
    if len(cleaned) > MAX_QUESTION_LENGTH:
        raise ValueError("Keep the question under 2000 characters.")
    return cleaned
