import React from "react";

interface VideoPlayerProps {
  src?: string;
  poster?: string;
  prompt?: string;
}

const isPlayableMp4 = (src?: string) => !!src && src.toLowerCase().endsWith(".mp4");

const VideoPlayer: React.FC<VideoPlayerProps> = ({ src, poster, prompt }) => {
  if (!src) {
    return (
      <div className="flex flex-col items-center justify-center text-gray-400 p-8 text-center w-full h-full">
        <div className="text-5xl mb-3">🎬</div>
        <p className="text-base font-semibold">Video is generating...</p>
        {prompt && <p className="text-xs mt-2 max-w-sm text-gray-500">{prompt}</p>}
      </div>
    );
  }

  if (!isPlayableMp4(src)) {
    return (
      <div className="flex flex-col items-center justify-center text-gray-500 p-6 text-center w-full h-full bg-gray-50">
        <div className="text-5xl mb-3">ℹ️</div>
        <p className="text-base font-semibold">Video not ready yet</p>
        <p className="text-xs mt-2 max-w-sm text-gray-500">
          Waiting for the MP4 to finish generating. Check back in a moment.
        </p>
      </div>
    );
  }

  return (
    <video
      src={src}
      controls
      playsInline
      muted
      className="max-w-full max-h-full w-auto h-auto"
      style={{ objectFit: "contain" }}
      poster={poster}
    />
  );
};

export default VideoPlayer;
