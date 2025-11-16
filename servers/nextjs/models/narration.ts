/**
 * TypeScript models for voice narration feature
 */

export interface TeachingScript {
  slide_index: number;
  teaching_explanation: string;
  estimated_duration_seconds: number;
  key_concepts: string[];
}

export interface VoiceNarrationRequest {
  presentation_id: string;
  language_code: string;
  voice_gender: "male" | "female";
  include_regional_references: boolean;
  student_level: "beginner" | "intermediate" | "advanced";
}

export interface SlideNarration {
  slide_index: number;
  script: string;
  audio_url: string;
  duration_seconds: number;
  language: string;
}

export interface PresentationNarration {
  presentation_id: string;
  slides: SlideNarration[];
  total_duration_seconds: number;
  language: string;
  created_at?: string;
}

export interface RegenerateSlideNarrationRequest {
  presentation_id: string;
  slide_index: number;
  language_code: string;
  voice_gender: "male" | "female";
  student_level: "beginner" | "intermediate" | "advanced";
  include_regional_references: boolean;
}

export interface SupportedLanguage {
  code: string;
  name: string;
}
