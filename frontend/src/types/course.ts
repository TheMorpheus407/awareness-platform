export interface Course {
  id: number;
  title: string;
  description: string;
  duration_minutes: number;
  difficulty_level: 'beginner' | 'intermediate' | 'advanced';
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

export interface CourseProgress {
  id: number;
  user_id: number;
  course_id: number;
  status: 'not_started' | 'in_progress' | 'completed';
  progress_percentage: number;
  completed_at?: string;
  created_at: string;
  updated_at: string;
}