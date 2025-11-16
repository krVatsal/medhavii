/**
 * Hook for managing voice narration in presentation mode
 */

import { useState, useEffect, useRef, useCallback } from "react";
import { PresentationNarration, SlideNarration } from "@/models/narration";

interface UseNarrationProps {
  narrationData: PresentationNarration | null;
  currentSlide: number;
  onSlideChange: (slideNumber: number) => void;
  autoAdvance: boolean;
}

export function useNarration({
  narrationData,
  currentSlide,
  onSlideChange,
  autoAdvance,
}: UseNarrationProps) {
  const audioRef = useRef<HTMLAudioElement>(null);
  const [isPlaying, setIsPlaying] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [currentTime, setCurrentTime] = useState(0);
  const [duration, setDuration] = useState(0);
  const [playbackRate, setPlaybackRate] = useState(1.0);

  // Get current slide narration
  const currentNarration: SlideNarration | undefined = narrationData?.slides.find(
    (n) => n.slide_index === currentSlide
  );

  // Load audio for current slide
  useEffect(() => {
    if (!audioRef.current || !currentNarration) return;

    const audio = audioRef.current;
    setIsLoading(true);
    setIsPlaying(false);
    setCurrentTime(0);

    // Set new audio source
    audio.src = currentNarration.audio_url;
    audio.playbackRate = playbackRate;

    const handleCanPlay = () => {
      setIsLoading(false);
      setDuration(audio.duration);
    };

    const handleTimeUpdate = () => {
      setCurrentTime(audio.currentTime);
    };

    const handleEnded = () => {
      setIsPlaying(false);
      setCurrentTime(0);

      // Auto-advance to next slide if enabled
      if (autoAdvance && narrationData) {
        const nextSlide = currentSlide + 1;
        if (nextSlide < narrationData.slides.length) {
          onSlideChange(nextSlide);
        }
      }
    };

    const handleError = () => {
      setIsLoading(false);
      console.error("Error loading audio:", currentNarration.audio_url);
    };

    audio.addEventListener("canplay", handleCanPlay);
    audio.addEventListener("timeupdate", handleTimeUpdate);
    audio.addEventListener("ended", handleEnded);
    audio.addEventListener("error", handleError);

    // Load the audio
    audio.load();

    return () => {
      audio.removeEventListener("canplay", handleCanPlay);
      audio.removeEventListener("timeupdate", handleTimeUpdate);
      audio.removeEventListener("ended", handleEnded);
      audio.removeEventListener("error", handleError);
    };
  }, [currentNarration, currentSlide, narrationData, onSlideChange, autoAdvance, playbackRate]);

  // Play audio
  const play = useCallback(async () => {
    if (!audioRef.current || isLoading) return;
    
    try {
      await audioRef.current.play();
      setIsPlaying(true);
    } catch (error) {
      console.error("Error playing audio:", error);
    }
  }, [isLoading]);

  // Pause audio
  const pause = useCallback(() => {
    if (!audioRef.current) return;
    
    audioRef.current.pause();
    setIsPlaying(false);
  }, []);

  // Toggle play/pause
  const togglePlayPause = useCallback(() => {
    if (isPlaying) {
      pause();
    } else {
      play();
    }
  }, [isPlaying, play, pause]);

  // Seek to specific time
  const seek = useCallback((time: number) => {
    if (!audioRef.current) return;
    
    audioRef.current.currentTime = time;
    setCurrentTime(time);
  }, []);

  // Change playback speed
  const changePlaybackRate = useCallback((rate: number) => {
    if (!audioRef.current) return;
    
    audioRef.current.playbackRate = rate;
    setPlaybackRate(rate);
  }, []);

  // Auto-play when slide changes (if enabled)
  useEffect(() => {
    if (autoAdvance && currentNarration && !isLoading) {
      // Small delay to ensure audio is loaded
      const timer = setTimeout(() => {
        play();
      }, 300);
      
      return () => clearTimeout(timer);
    }
  }, [currentSlide, currentNarration, autoAdvance, isLoading, play]);

  return {
    audioRef,
    isPlaying,
    isLoading,
    currentTime,
    duration,
    playbackRate,
    currentNarration,
    play,
    pause,
    togglePlayPause,
    seek,
    changePlaybackRate,
  };
}
