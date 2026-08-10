export interface QuizSession {
  score: number;
  total: number;
  weakTopics: string[];
  completedAt: string;
  subject_id: string | null;
}

let quizSession: QuizSession | null = null;

let weakTopics: string[] = [];

export function getWeakTopics(): string[] {
  return weakTopics;
}

export function setWeakTopics(topics: string[]): void {
  weakTopics = topics;
}

export function getQuizSession(): QuizSession | null {
  return quizSession;
}

export function setQuizSession(
  score: number,
  total: number,
  weakTopicsList: string[],
  subjectId: string | null = null
): void {
  quizSession = {
    score,
    total,
    weakTopics: weakTopicsList,
    completedAt: new Date().toISOString(),
    subject_id: subjectId,
  };
  weakTopics = weakTopicsList;
}
