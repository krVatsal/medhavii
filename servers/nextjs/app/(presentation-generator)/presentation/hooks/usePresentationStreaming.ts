import { useEffect, useRef } from "react";
import { useDispatch } from "react-redux";
import {
  clearPresentationData,
  setPresentationData,
  setStreaming,
} from "@/store/slices/presentationGeneration";
import { jsonrepair } from "jsonrepair";
import { toast } from "sonner";
import { MixpanelEvent, trackEvent } from "@/utils/mixpanel";
import { authenticatedFetch } from "@/lib/api-interceptor";

export const usePresentationStreaming = (
  presentationId: string,
  stream: string | null,
  setLoading: (loading: boolean) => void,
  setError: (error: boolean) => void,
  fetchUserSlides: () => void
) => {
  const dispatch = useDispatch();
  const previousSlidesLength = useRef(0);

  useEffect(() => {
    let abortController: AbortController;
    let accumulatedChunks = "";

    const initializeStream = async () => {
      dispatch(setStreaming(true));
      dispatch(clearPresentationData());

      trackEvent(MixpanelEvent.Presentation_Stream_API_Call);

      try {
        abortController = new AbortController();
        
        const response = await authenticatedFetch(
          `/api/v1/ppt/presentation/stream/${presentationId}`,
          {
            signal: abortController.signal,
          }
        );

        if (!response.ok) {
          throw new Error(`HTTP error! status: ${response.status}`);
        }

        const reader = response.body?.getReader();
        const decoder = new TextDecoder();

        if (!reader) {
          throw new Error("No response body");
        }

        while (true) {
          const { done, value } = await reader.read();

          if (done) break;

          const chunk = decoder.decode(value, { stream: true });
          const lines = chunk.split("\n");

          for (const line of lines) {
            if (line.startsWith("data: ")) {
              const dataStr = line.slice(6);
              if (dataStr.trim()) {
                try {
                  const data = JSON.parse(dataStr);

                  switch (data.type) {
                    case "chunk":
                      accumulatedChunks += data.chunk;
                      try {
                        const repairedJson = jsonrepair(accumulatedChunks);
                        const partialData = JSON.parse(repairedJson);

                        if (partialData.slides) {
                          if (
                            partialData.slides.length !== previousSlidesLength.current &&
                            partialData.slides.length > 0
                          ) {
                            dispatch(
                              setPresentationData({
                                ...partialData,
                                slides: partialData.slides,
                              })
                            );
                            previousSlidesLength.current = partialData.slides.length;
                            setLoading(false);
                          }
                        }
                      } catch (error) {
                        // JSON isn't complete yet, continue accumulating
                      }
                      break;

                    case "complete":
                      try {
                        dispatch(setPresentationData(data.presentation));
                        dispatch(setStreaming(false));
                        setLoading(false);

                        // Remove stream parameter from URL
                        const newUrl = new URL(window.location.href);
                        newUrl.searchParams.delete("stream");
                        window.history.replaceState({}, "", newUrl.toString());
                      } catch (error) {
                        console.error("Error parsing accumulated chunks:", error);
                      }
                      accumulatedChunks = "";
                      return; // Exit the loop

                    case "closing":
                      dispatch(setPresentationData(data.presentation));
                      setLoading(false);
                      dispatch(setStreaming(false));

                      // Remove stream parameter from URL
                      const newUrl = new URL(window.location.href);
                      newUrl.searchParams.delete("stream");
                      window.history.replaceState({}, "", newUrl.toString());
                      return; // Exit the loop

                    case "error":
                      toast.error("Error in outline streaming", {
                        description:
                          data.detail ||
                          "Failed to connect to the server. Please try again.",
                      });
                      setLoading(false);
                      dispatch(setStreaming(false));
                      setError(true);
                      return; // Exit the loop
                  }
                } catch (e) {
                  console.error("Error parsing SSE data:", e);
                }
              }
            }
          }
        }
      } catch (error: any) {
        if (error.name !== "AbortError") {
          console.error("Stream failed:", error);
          setLoading(false);
          dispatch(setStreaming(false));
          setError(true);
        }
      }
    };

    if (stream) {
      initializeStream();
    } else {
      fetchUserSlides();
    }

    return () => {
      if (abortController) {
        abortController.abort();
      }
    };
  }, [presentationId, stream, dispatch, setLoading, setError, fetchUserSlides]);
};
