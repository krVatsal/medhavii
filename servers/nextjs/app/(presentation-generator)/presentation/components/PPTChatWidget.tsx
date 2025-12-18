"use client";
import React, { useEffect, useMemo, useRef, useState } from "react";
import { MessageCircle, Send, X } from "lucide-react";
import { PresentationGenerationApi } from "../../services/api/presentation-generation";
import {
  PresentationChatMessage,
  PresentationChatResponse,
} from "../../services/api/types";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import { ScrollArea } from "@/components/ui/scroll-area";

interface PPTChatWidgetProps {
  presentationId: string;
}

interface ChatMessage extends PresentationChatMessage {
  id: string;
}

const WELCOME_MESSAGE =
  "Hi! I'm your cheerful presentation tutor. Ask me anything about these slides and I'll help explain.";

const PPTChatWidget: React.FC<PPTChatWidgetProps> = ({ presentationId }) => {
  const [isOpen, setIsOpen] = useState(false);
  const [messages, setMessages] = useState<ChatMessage[]>([
    { id: "assistant-0", role: "assistant", content: WELCOME_MESSAGE },
  ]);
  const [input, setInput] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const scrollRef = useRef<HTMLDivElement>(null);

  const historyForRequest = useMemo<PresentationChatMessage[]>(
    () => messages.map(({ role, content }) => ({ role, content })),
    [messages]
  );

  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [messages, isOpen]);

  const sendMessage = async () => {
    const trimmed = input.trim();
    if (!trimmed || isLoading) return;

    const userMessage: ChatMessage = {
      id: `user-${messages.length}`,
      role: "user",
      content: trimmed,
    };

    const nextMessages = [...messages, userMessage];
    setMessages(nextMessages);
    setInput("");
    setIsLoading(true);
    setError(null);

    try {
      const response: PresentationChatResponse =
        await PresentationGenerationApi.chatWithPresentation(
          presentationId,
          [...historyForRequest, { role: "user", content: trimmed }],
        );

      setMessages((prev) => [
        ...prev,
        {
          id: `assistant-${prev.length}`,
          role: "assistant",
          content: response.reply,
        },
      ]);
    } catch (err) {
      const message = err instanceof Error ? err.message : "Unable to chat right now.";
      setError(message);
      setMessages((prev) => prev);
    } finally {
      setIsLoading(false);
    }
  };

  const handleKeyDown = (event: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (event.key === "Enter" && !event.shiftKey) {
      event.preventDefault();
      sendMessage();
    }
  };

  const handleToggle = () => {
    setIsOpen((prev) => !prev);
    setError(null);
  };

  return (
    <>
      <button
        onClick={handleToggle}
        className="fixed bottom-6 right-6 z-50 flex h-12 w-12 items-center justify-center rounded-full bg-blue-600 text-white shadow-lg transition hover:bg-blue-700"
        aria-label="Open presentation chat"
      >
        {isOpen ? <X className="h-5 w-5" /> : <MessageCircle className="h-5 w-5" />}
      </button>

      <div
        className={`fixed bottom-24 right-6 z-50 w-full max-w-md transform transition-all duration-200 ${
          isOpen ? "opacity-100" : "pointer-events-none opacity-0"
        }`}
      >
        <div className="rounded-xl border border-gray-200 bg-white shadow-2xl">
          <div className="flex items-center justify-between border-b px-4 py-3">
            <div>
              <p className="text-sm font-semibold text-gray-900">Slide Tutor</p>
              <p className="text-xs text-gray-500">Friendly, jolly, and helpful</p>
            </div>
            <button
              onClick={handleToggle}
              className="rounded p-1 text-gray-500 transition hover:bg-gray-100"
              aria-label="Close chat"
            >
              <X className="h-4 w-4" />
            </button>
          </div>

          <div className="px-4 pt-3">
            <ScrollArea className="h-72" ref={scrollRef}>
              <div className="space-y-3 pb-3">
                {messages.map((message) => (
                  <div key={message.id} className="flex w-full flex-col gap-1">
                    <span className="text-xs font-semibold text-gray-500">
                      {message.role === "user" ? "You" : "Tutor"}
                    </span>
                    <div
                      className={`rounded-lg px-3 py-2 text-sm leading-relaxed shadow-sm ${
                        message.role === "user"
                          ? "bg-blue-50 text-gray-900"
                          : "bg-gray-50 text-gray-900"
                      }`}
                    >
                      {message.content}
                    </div>
                  </div>
                ))}
              </div>
            </ScrollArea>
          </div>

          {error && (
            <div className="px-4 pt-2 text-xs text-red-600">{error}</div>
          )}

          <div className="flex items-center gap-2 px-4 py-3">
            <Textarea
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={handleKeyDown}
              placeholder="Ask about any slide..."
              className="min-h-[44px] resize-none text-sm"
              disabled={isLoading}
            />
            <Button onClick={sendMessage} disabled={isLoading || !input.trim()}>
              {isLoading ? "..." : <Send className="h-4 w-4" />}
            </Button>
          </div>
        </div>
      </div>
    </>
  );
};

export default PPTChatWidget;
