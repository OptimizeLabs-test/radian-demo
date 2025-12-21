import { useState, useEffect, useRef, useCallback } from "react";
import { Card } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Mic, Send, Loader2, MessageCircle } from "lucide-react";
import { useToast } from "@/hooks/use-toast";
import { useStreamingText } from "@/hooks/useStreamingText";
import type { ChatMessage } from "@/lib/api";

interface ConversationalAgentProps {
  introMessage: string | null;
  onSendMessage: (message: string) => Promise<void>;
  messages: ChatMessage[];
  isLoading: boolean;
}

const quickQuestions = ["Show HbA1c trends", "Recent medications", "Cardiology notes", "Exercise & lifestyle"];

// Streaming message component for assistant responses
function StreamingMessage({
  content,
  isLatest,
  onStreamUpdate
}: {
  content: string;
  isLatest: boolean;
  onStreamUpdate?: () => void;
}) {
  const {
    displayedText,
    isStreaming
  } = useStreamingText(content, {
    speed: 12,
    enabled: isLatest
  });

  // Trigger scroll on each text update during streaming
  useEffect(() => {
    if (isLatest && isStreaming && onStreamUpdate) {
      onStreamUpdate();
    }
  }, [displayedText, isLatest, isStreaming, onStreamUpdate]);

  return (
    <span>
      {isLatest ? displayedText : content}
      {isStreaming && <span className="inline-block w-1 h-4 bg-secondary-foreground/50 ml-0.5 animate-pulse" />}
    </span>
  );
}

export function ConversationalAgent({
  introMessage,
  onSendMessage,
  messages,
  isLoading
}: ConversationalAgentProps) {
  const [input, setInput] = useState("");
  const { toast } = useToast();
  const scrollRef = useRef<HTMLDivElement>(null);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const [latestAssistantIdx, setLatestAssistantIdx] = useState<number>(-1);

  // Track the latest assistant message index
  useEffect(() => {
    const lastAssistantIdx = messages.reduce((lastIdx, msg, idx) => msg.role === "assistant" ? idx : lastIdx, -1);
    setLatestAssistantIdx(lastAssistantIdx);
  }, [messages]);

  // Scroll to bottom function - scrolls within the ScrollArea only, not the page
  const scrollToBottom = useCallback(() => {
    const viewport = scrollRef.current?.querySelector('[data-radix-scroll-area-viewport]');
    if (viewport) {
      viewport.scrollTo({ top: viewport.scrollHeight, behavior: 'smooth' });
    }
  }, []);

  // Auto-scroll when new messages arrive or loading state changes
  useEffect(() => {
    scrollToBottom();
  }, [messages, isLoading, scrollToBottom]);

  // Streaming intro message with scroll callback
  const {
    displayedText: streamedIntro,
    isStreaming: isStreamingIntro
  } = useStreamingText(introMessage, {
    speed: 12,
    enabled: true
  });

  // Scroll during intro streaming
  useEffect(() => {
    if (isStreamingIntro) {
      scrollToBottom();
    }
  }, [streamedIntro, isStreamingIntro, scrollToBottom]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!input.trim() || isLoading) return;
    const message = input;
    setInput("");
    await onSendMessage(message);
  };

  const handleQuickQuestion = async (question: string) => {
    if (isLoading) return;
    await onSendMessage(question);
  };

  const handleVoiceInput = () => {
    toast({
      title: "Voice input coming soon",
      description: "Speech-to-text functionality will be available in the prototype"
    });
  };

  return (
    <Card className="flex flex-col h-full p-3 sm:p-4 bg-card border border-border shadow-sm">
      {/* Header - compact */}
      <div className="flex items-center gap-1.5 mb-2 shrink-0">
        <div className="w-6 h-6 rounded-md bg-primary/10 flex items-center justify-center">
          <MessageCircle className="h-3 w-3 text-primary" />
        </div>
        <h3 className="text-xs font-semibold text-foreground">
          Clinical Assistant
        </h3>
      </div>

      {/* Chat messages - flexible height */}
      <ScrollArea className="h-[280px] sm:h-[320px] mb-2" ref={scrollRef}>
        <div className="space-y-2 pr-3">
          {introMessage && (
            <div className="flex justify-start">
              <div className="bg-teal-100 text-teal-800 text-sm rounded-md p-2 max-w-[85%]">
                {streamedIntro}
                {isStreamingIntro && <span className="inline-block w-0.5 h-3 bg-teal-600/50 ml-0.5 animate-pulse" />}
              </div>
            </div>
          )}
          
          {messages.map((msg, idx) => (
            <div key={idx} className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}>
              <div className={`text-sm rounded-md p-2 max-w-[85%] ${msg.role === 'user' ? 'bg-primary text-primary-foreground' : 'bg-teal-100 text-teal-800'}`}>
                {msg.role === 'assistant' ? (
                  <StreamingMessage 
                    content={msg.content} 
                    isLatest={idx === latestAssistantIdx}
                    onStreamUpdate={scrollToBottom}
                  />
                ) : msg.content}
              </div>
            </div>
          ))}
          
          {isLoading && (
            <div className="flex justify-start">
              <div className="bg-teal-100 text-teal-800 text-sm rounded-md p-2">
                <Loader2 className="h-3 w-3 animate-spin" />
              </div>
            </div>
          )}
          
          {/* Scroll anchor */}
          <div ref={messagesEndRef} />
        </div>
      </ScrollArea>

      {/* Input section - pinned at bottom */}
      <div className="space-y-2 shrink-0">
        <form onSubmit={handleSubmit} className="flex gap-1.5 items-center">
          <Input 
            value={input} 
            onChange={e => setInput(e.target.value)} 
            disabled={isLoading} 
            className="flex-1 h-8 text-xs" 
            placeholder="Ask a question..." 
          />
          <Button 
            type="button" 
            variant="outline" 
            size="icon" 
            onClick={handleVoiceInput} 
            disabled={isLoading} 
            className="h-8 w-8 shrink-0"
          >
            <Mic className="h-3.5 w-3.5" />
          </Button>
          <Button 
            type="submit" 
            size="icon" 
            disabled={isLoading || !input.trim()} 
            className="h-8 w-8 shrink-0 bg-teal-600 hover:bg-teal-700 text-white"
          >
            <Send className="h-3.5 w-3.5" />
          </Button>
        </form>

        {/* Quick questions */}
        <div className="flex gap-1.5 overflow-x-auto pb-0.5 -mx-1 px-1 scrollbar-hide">
          {quickQuestions.map((q, idx) => (
            <button 
              key={idx} 
              onClick={() => handleQuickQuestion(q)} 
              disabled={isLoading} 
              className="text-[10px] px-2 py-1 rounded-full bg-teal-100 text-teal-700 hover:bg-teal-200 transition-colors disabled:opacity-50 whitespace-nowrap shrink-0"
            >
              {q}
            </button>
          ))}
        </div>
        
        <p className="text-[10px] text-muted-foreground/60 italic text-center">
          Retrieves from the patient's vectorised record.
        </p>
      </div>
    </Card>
  );
}
