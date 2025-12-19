import React, { useState, useEffect } from 'react';
import { Download, X, Video as VideoIcon } from 'lucide-react';

interface VideoInfo {
  video_id: string;
  slide_index: number;
  prompt: string;
  video_url: string;
  created_at: string;
  completed_at: string | null;
}

interface VideoGalleryProps {
  presentationId: string;
  isOpen: boolean;
  onClose: () => void;
}

export function VideoGallery({ presentationId, isOpen, onClose }: VideoGalleryProps) {
  const [videos, setVideos] = useState<VideoInfo[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (isOpen && presentationId) {
      fetchVideos();
    }
  }, [isOpen, presentationId]);

  const fetchVideos = async () => {
    setLoading(true);
    setError(null);
    try {
      const response = await fetch(`/api/v1/ppt/presentation/${presentationId}/videos`);
      if (!response.ok) {
        throw new Error('Failed to fetch videos');
      }
      const data = await response.json();
      setVideos(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load videos');
    } finally {
      setLoading(false);
    }
  };

  const handleDownload = async (videoUrl: string, slideIndex: number) => {
    try {
      const response = await fetch(videoUrl);
      const blob = await response.blob();
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `slide-${slideIndex}-video.mp4`;
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(url);
      document.body.removeChild(a);
    } catch (err) {
      console.error('Download failed:', err);
    }
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black bg-opacity-50 p-4">
      <div className="bg-white rounded-lg shadow-xl max-w-6xl w-full max-h-[90vh] flex flex-col">
        {/* Header */}
        <div className="flex items-center justify-between p-6 border-b">
          <div className="flex items-center gap-3">
            <VideoIcon className="w-6 h-6 text-blue-600" />
            <h2 className="text-2xl font-bold text-gray-800">Generated Videos</h2>
          </div>
          <button
            onClick={onClose}
            className="p-2 hover:bg-gray-100 rounded-full transition-colors"
            aria-label="Close"
          >
            <X className="w-6 h-6" />
          </button>
        </div>

        {/* Content */}
        <div className="flex-1 overflow-y-auto p-6">
          {loading && (
            <div className="flex items-center justify-center py-12">
              <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
            </div>
          )}

          {error && (
            <div className="bg-red-50 border border-red-200 rounded-lg p-4 text-red-800">
              {error}
            </div>
          )}

          {!loading && !error && videos.length === 0 && (
            <div className="text-center py-12">
              <VideoIcon className="w-16 h-16 mx-auto text-gray-300 mb-4" />
              <p className="text-gray-600 text-lg">No videos generated yet</p>
              <p className="text-gray-400 text-sm mt-2">
                Videos will appear here once they're generated
              </p>
            </div>
          )}

          {!loading && !error && videos.length > 0 && (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
              {videos.map((video) => (
                <div
                  key={video.video_id}
                  className="border rounded-lg overflow-hidden shadow-sm hover:shadow-md transition-shadow bg-white"
                >
                  {/* Video Player */}
                  <div className="relative bg-black aspect-video">
                    <video
                      src={video.video_url}
                      controls
                      className="w-full h-full"
                      preload="metadata"
                    >
                      Your browser does not support the video tag.
                    </video>
                  </div>

                  {/* Video Info */}
                  <div className="p-4">
                    <div className="flex items-center justify-between mb-2">
                      <span className="text-sm font-semibold text-gray-700">
                        Slide {video.slide_index + 1}
                      </span>
                      <button
                        onClick={() => handleDownload(video.video_url, video.slide_index)}
                        className="flex items-center gap-1 px-3 py-1 bg-blue-600 text-white rounded-md hover:bg-blue-700 transition-colors text-sm"
                        title="Download video"
                      >
                        <Download className="w-4 h-4" />
                        Download
                      </button>
                    </div>

                    <p className="text-sm text-gray-600 line-clamp-3" title={video.prompt}>
                      {video.prompt}
                    </p>

                    {video.completed_at && (
                      <p className="text-xs text-gray-400 mt-2">
                        Generated: {new Date(video.completed_at).toLocaleString()}
                      </p>
                    )}
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Footer */}
        {!loading && !error && videos.length > 0 && (
          <div className="border-t px-6 py-4 bg-gray-50">
            <p className="text-sm text-gray-600">
              Total videos: <span className="font-semibold">{videos.length}</span>
            </p>
          </div>
        )}
      </div>
    </div>
  );
}
