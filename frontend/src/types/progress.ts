export interface ProgressItem {
  topic_id: string;
  topic_name: string;
  subject_id: string;
  subject_name: string;
  mastery_score: number;
  topics_completed: number;
  last_studied_at: string | null;
}
