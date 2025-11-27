/**
 * API utilities for quiz generation
 */

export interface QuizQuestion {
  question: string;
  options: string[];
  correct_answer: string;
  explanation: string;
}

export interface QuizData {
  quiz: QuizQuestion[];
}

export interface GenerateQuizRequest {
  presentation_id: string;
  slide_start: number;
  slide_end?: number;
  num_questions?: number;
  difficulty?: "easy" | "medium" | "hard";
}

export interface QuizResponse {
  success: boolean;
  quiz_data?: QuizData;
  error?: string;
  slide_range: string;
  num_questions: number;
  difficulty: string;
}

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

/**
 * Generate quiz from presentation slides
 */
export async function generateQuiz(
  request: GenerateQuizRequest
): Promise<QuizResponse> {
  try {
    const response = await fetch(`${API_BASE_URL}/api/v1/ppt/quiz/generate`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        presentation_id: request.presentation_id,
        slide_start: request.slide_start,
        slide_end: request.slide_end || request.slide_start,
        num_questions: request.num_questions || 5,
        difficulty: request.difficulty || "medium",
      }),
    });

    if (!response.ok) {
      const errorData = await response.json();
      throw new Error(errorData.detail || "Failed to generate quiz");
    }

    const data: QuizResponse = await response.json();
    return data;
  } catch (error) {
    console.error("Error generating quiz:", error);
    throw error;
  }
}

/**
 * Check quiz service health
 */
export async function checkQuizServiceHealth(): Promise<boolean> {
  try {
    const response = await fetch(`${API_BASE_URL}/api/v1/ppt/quiz/health`);
    return response.ok;
  } catch (error) {
    console.error("Quiz service health check failed:", error);
    return false;
  }
}
