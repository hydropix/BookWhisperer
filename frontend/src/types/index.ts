// Book types
export interface Book {
  id: string;
  title: string;
  author: string;
  file_name: string;
  file_path: string;
  file_type: 'epub' | 'txt';
  total_chapters: number;
  status: 'pending' | 'parsing' | 'parsed' | 'formatting' | 'generating' | 'completed' | 'failed';
  error_message?: string;
  metadata?: Record<string, unknown>;
  created_at: string;
  updated_at: string;
}

// Chapter types
export interface Chapter {
  id: string;
  book_id: string;
  chapter_number: number;
  title: string;
  raw_text?: string;
  formatted_text?: string;
  word_count: number;
  character_count: number;
  status: 'pending' | 'formatting' | 'formatted' | 'generating' | 'completed' | 'failed';
  error_message?: string;
  created_at: string;
  updated_at: string;
}

// Audio file types
export interface AudioFile {
  id: string;
  chapter_id: string;
  file_path: string;
  file_size: number;
  duration_seconds: number;
  format: string;
  chunk_index: number;
  total_chunks: number;
  tts_model?: string;
  voice_id?: string;
  created_at: string;
}

// Processing job types
export type JobType = 'parse_book' | 'format_chapter' | 'generate_audio';
export type JobStatus = 'pending' | 'processing' | 'completed' | 'failed';

export interface ProcessingJob {
  id: string;
  book_id?: string;
  chapter_id?: string;
  job_type: JobType;
  celery_task_id: string;
  status: JobStatus;
  progress_percent: number;
  error_message?: string;
  retry_count: number;
  max_retries: number;
  metadata?: Record<string, unknown>;
  started_at?: string;
  completed_at?: string;
  created_at: string;
  updated_at: string;
}

// API Response types
export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  page: number;
  page_size: number;
  pages: number;
}

export interface BookListResponse extends PaginatedResponse<Book> {}

export interface ChapterListResponse {
  book_id: string;
  chapters: Chapter[];
  total: number;
}

export interface UploadBookResponse {
  book: Book;
  job: ProcessingJob;
}

export interface FormatChapterResponse {
  job: ProcessingJob;
}

export interface FormatAllChaptersResponse {
  message: string;
  book_id: string;
  task_id: string;
  chapters_count: number;
}

// Health check types
export interface HealthCheck {
  status: 'healthy' | 'unhealthy';
  service: string;
  details?: Record<string, unknown>;
}

export interface AllHealthChecks {
  api: HealthCheck;
  database: HealthCheck;
  redis: HealthCheck;
  ollama?: HealthCheck;
  chatterbox?: HealthCheck;
}
