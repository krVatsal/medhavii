/**
 * API service for voice narration endpoints
 */

import { 
  VoiceNarrationRequest, 
  PresentationNarration,
  SlideNarration,
  RegenerateSlideNarrationRequest,
  SupportedLanguage
} from "@/models/narration";
import { ApiResponseHandler } from "./api-error-handler";

export class NarrationApi {
  
  /**
   * Generate complete voice narration for a presentation
   */
  static async generatePresentationNarration(
    request: VoiceNarrationRequest
  ): Promise<PresentationNarration> {
    // Create AbortController with 5-minute timeout for TTS generation
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), 300000); // 5 minutes
    
    try {
      const response = await fetch("/api/v1/ppt/narration/generate", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify(request),
        signal: controller.signal,
      });

      clearTimeout(timeoutId);
      return ApiResponseHandler.handleResponse(
        response,
        "Failed to generate narration"
      );
    } catch (error) {
      clearTimeout(timeoutId);
      if (error instanceof Error && error.name === 'AbortError') {
        throw new Error("Narration generation timed out after 5 minutes");
      }
      throw error;
    }
  }

  /**
   * Regenerate narration for a single slide
   */
  static async regenerateSlideNarration(
    request: RegenerateSlideNarrationRequest
  ): Promise<SlideNarration> {
    const response = await fetch("/api/v1/ppt/narration/regenerate-slide", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify(request),
    });

    return ApiResponseHandler.handleResponse(
      response,
      "Failed to regenerate slide narration"
    );
  }

  /**
   * Get list of supported languages
   */
  static async getSupportedLanguages(): Promise<Record<string, string>> {
    const response = await fetch("/api/v1/ppt/narration/supported-languages");
    
    const data = await ApiResponseHandler.handleResponse(
      response,
      "Failed to fetch supported languages"
    );
    
    return data.languages;
  }
}
