/**
 * Narration controls component for presentation mode
 */

import React from "react";
import { Button } from "@/components/ui/button";
import { Slider } from "@/components/ui/slider";
import {
  Play,
  Pause,
  Volume2,
  VolumeX,
  RotateCcw,
  Settings,
} from "lucide-react";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { SlideNarration } from "@/models/narration";

interface NarrationControlsProps {
  isPlaying: boolean;
  isLoading: boolean;
  currentTime: number;
  duration: number;
  playbackRate: number;
  currentNarration: SlideNarration | undefined;
  onPlayPause: () => void;
  onSeek: (time: number) => void;
  onChangeSpeed: (rate: number) => void;
  autoAdvance: boolean;
  onToggleAutoAdvance: () => void;
}

const NarrationControls: React.FC<NarrationControlsProps> = ({
  isPlaying,
  isLoading,
  currentTime,
  duration,
  playbackRate,
  currentNarration,
  onPlayPause,
  onSeek,
  onChangeSpeed,
  autoAdvance,
  onToggleAutoAdvance,
}) => {
  const formatTime = (seconds: number) => {
    const mins = Math.floor(seconds / 60);
    const secs = Math.floor(seconds % 60);
    return `${mins}:${secs.toString().padStart(2, "0")}`;
  };

  if (!currentNarration) {
    return null;
  }

  return (
    <div className="narration-controls absolute bottom-20 left-1/2 -translate-x-1/2 bg-black/80 backdrop-blur-sm rounded-lg p-4 z-50 min-w-[500px]">
      <div className="flex flex-col gap-3">
        {/* Progress bar */}
        <div className="flex items-center gap-3">
          <span className="text-white text-sm min-w-[40px]">
            {formatTime(currentTime)}
          </span>
          <Slider
            value={[currentTime]}
            max={duration || 100}
            step={0.1}
            onValueChange={([value]) => onSeek(value)}
            className="flex-1"
          />
          <span className="text-white text-sm min-w-[40px]">
            {formatTime(duration)}
          </span>
        </div>

        {/* Control buttons */}
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            {/* Play/Pause button */}
            <Button
              variant="ghost"
              size="icon"
              onClick={onPlayPause}
              disabled={isLoading}
              className="text-white hover:bg-white/20"
            >
              {isLoading ? (
                <RotateCcw className="h-5 w-5 animate-spin" />
              ) : isPlaying ? (
                <Pause className="h-5 w-5" />
              ) : (
                <Play className="h-5 w-5" />
              )}
            </Button>

            {/* Speed control */}
            <Select
              value={playbackRate.toString()}
              onValueChange={(value) => onChangeSpeed(parseFloat(value))}
            >
              <SelectTrigger className="w-[100px] bg-white/10 text-white border-white/20">
                <SelectValue placeholder="Speed" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="0.5">0.5x</SelectItem>
                <SelectItem value="0.75">0.75x</SelectItem>
                <SelectItem value="1">1x</SelectItem>
                <SelectItem value="1.25">1.25x</SelectItem>
                <SelectItem value="1.5">1.5x</SelectItem>
                <SelectItem value="2">2x</SelectItem>
              </SelectContent>
            </Select>

            {/* Auto-advance toggle */}
            <Button
              variant={autoAdvance ? "default" : "ghost"}
              size="sm"
              onClick={onToggleAutoAdvance}
              className={autoAdvance ? "" : "text-white hover:bg-white/20"}
            >
              Auto-advance {autoAdvance ? "ON" : "OFF"}
            </Button>
          </div>

          {/* Narration info */}
          <div className="text-white text-sm">
            <span className="opacity-70">Language: </span>
            <span className="font-medium">{currentNarration.language}</span>
          </div>
        </div>

        {/* Narration script (optional, can be toggled) */}
        {currentNarration.script && (
          <details className="mt-2">
            <summary className="text-white text-sm cursor-pointer opacity-70 hover:opacity-100">
              View Script
            </summary>
            <div className="mt-2 p-3 bg-white/10 rounded text-white text-sm max-h-[150px] overflow-y-auto">
              {currentNarration.script}
            </div>
          </details>
        )}
      </div>
    </div>
  );
};

export default NarrationControls;
