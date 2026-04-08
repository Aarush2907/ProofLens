export const MIN_QUESTION_LENGTH = 10;
export const MAX_QUESTION_LENGTH = 2000;

export function validateQuestion(value: string): string | null {
  const cleaned = value.trim();
  if (cleaned.length < MIN_QUESTION_LENGTH) {
    return "Write at least 10 characters so the question is specific enough to research later.";
  }
  if (cleaned.length > MAX_QUESTION_LENGTH) {
    return "Keep the question under 2000 characters.";
  }
  return null;
}
