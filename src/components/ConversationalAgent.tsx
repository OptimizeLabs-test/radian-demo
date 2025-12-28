import { useState, useEffect, useRef, useCallback } from "react";
import { Card } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Mic, Send, Loader2, MessageCircle } from "lucide-react";
import { useToast } from "@/hooks/use-toast";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import type { ChatMessage } from "@/lib/api";
import { transcribeAudio } from "@/lib/api/endpoints";

interface ConversationalAgentProps {
  patientId: string;
  introMessage: string | null;
  onSendMessage: (message: string, predefinedAnswer?: string) => Promise<void>;
  messages: ChatMessage[];
  isLoading: boolean;
}

// Pre-defined question-answer mapping
const questionAnswerMap: Record<string, {
  question: string;
}> = {
  "6-Month Summary": {
    question: "Radian summarize this patient's last 6 months of medical history in 5 lines"
  },
  "Last 4 IFE Readings": {
    question: "Radian Give me the patients last 4 IFE readings"
  },
  "30-Day Risk Score": {
    question: "Based on this patient's last 1 year of vitals, labs, and medications, calculate their risk of decompensation in the next 30 days and show me which variables contributed most to the risk."
  }
};
const quickQuestionLabels = Object.keys(questionAnswerMap);

// Component to render streaming chat message
function StreamingChatMessage({ 
  content, 
  messageIndex, 
  isLastMessage, 
  isLoading 
}: { 
  content: string; 
  messageIndex: number;
  isLastMessage: boolean;
  isLoading: boolean;
}) {
  // Show content directly - backend already streams in real-time
  // No need for additional animation as it would cause the message to re-appear
  const isActivelyStreaming = isLastMessage && isLoading;

  return (
    <>
      <ReactMarkdown remarkPlugins={[remarkGfm]}>{content}</ReactMarkdown>
      {isActivelyStreaming && content && <span className="inline-block w-1 h-4 bg-teal-900/50 ml-0.5 animate-pulse" />}
    </>
  );
}

export function ConversationalAgent({
  patientId,
  introMessage,
  onSendMessage,
  messages,
  isLoading
}: ConversationalAgentProps) {
  const [input, setInput] = useState("");
  const [pendingPredefinedKey, setPendingPredefinedKey] = useState<string | null>(null);
  const [isRecording, setIsRecording] = useState(false);
  const [isTranscribing, setIsTranscribing] = useState(false);
  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const audioChunksRef = useRef<Blob[]>([]);
  const {
    toast
  } = useToast();
  const scrollRef = useRef<HTMLDivElement>(null);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  // Scroll to bottom function - scrolls within the ScrollArea only, not the page
  const scrollToBottom = useCallback(() => {
    const viewport = scrollRef.current?.querySelector('[data-radix-scroll-area-viewport]');
    if (viewport) {
      viewport.scrollTo({
        top: viewport.scrollHeight,
        behavior: 'smooth'
      });
    }
  }, []);

  // Auto-scroll when new messages arrive or loading state changes
  useEffect(() => {
    scrollToBottom();
  }, [messages, isLoading, scrollToBottom]);
  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!input.trim() || isLoading) return;
    const message = input;
    setInput("");
    setPendingPredefinedKey(null);
    
    // Always call the API, no predefined answers
    await onSendMessage(message);
  };
  const handleQuickQuestion = (label: string) => {
    if (isLoading) return;
    const mapping = questionAnswerMap[label];
    if (mapping) {
      setInput(mapping.question);
      setPendingPredefinedKey(label);
    }
  };
  const handleVoiceInput = async () => {
    if (isLoading || isTranscribing) return;

    if (isRecording) {
      // Stop recording
      if (mediaRecorderRef.current && mediaRecorderRef.current.state !== "inactive") {
        mediaRecorderRef.current.stop();
      }
      setIsRecording(false);
      return;
    }

    // Start recording
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      
      // Try to find a supported mimeType
      let mimeType = 'audio/webm;codecs=opus';
      if (!MediaRecorder.isTypeSupported(mimeType)) {
        // Fallback to other formats
        if (MediaRecorder.isTypeSupported('audio/webm')) {
          mimeType = 'audio/webm';
        } else if (MediaRecorder.isTypeSupported('audio/mp4')) {
          mimeType = 'audio/mp4';
        } else {
          mimeType = ''; // Use browser default
        }
      }
      
      const mediaRecorder = new MediaRecorder(stream, mimeType ? { mimeType } : undefined);
      
      mediaRecorderRef.current = mediaRecorder;
      audioChunksRef.current = [];

      mediaRecorder.ondataavailable = (event) => {
        if (event.data.size > 0) {
          audioChunksRef.current.push(event.data);
        }
      };

      mediaRecorder.onstop = async () => {
        // Stop all tracks to release microphone
        stream.getTracks().forEach(track => track.stop());
        
        // Create audio file from chunks
        const mimeType = mediaRecorderRef.current?.mimeType || 'audio/webm';
        const extension = mimeType.includes('mp4') ? 'mp4' : 'webm';
        const audioBlob = new Blob(audioChunksRef.current, { type: mimeType });
        const audioFile = new File([audioBlob], `recording.${extension}`, { type: mimeType });
        
        // Transcribe audio
        setIsTranscribing(true);
        try {
          const transcription = await transcribeAudio(patientId, audioFile);
          
          if (transcription && !transcription.startsWith("[Transcription error")) {
            setInput(transcription);
            // Optionally auto-send the transcribed message
            // await onSendMessage(transcription);
          } else {
            const errorMsg = transcription.startsWith("[Transcription error") 
              ? transcription.replace("[Transcription error: ", "").replace("]", "")
              : "Could not transcribe audio. Please try again.";
            toast({
              title: "Transcription failed",
              description: errorMsg,
              variant: "destructive",
            });
          }
        } catch (error) {
          const errorMsg = error instanceof Error ? error.message : "Failed to transcribe audio";
          // Check if it's a network error
          if (errorMsg.includes("fetch") || errorMsg.includes("network") || errorMsg.includes("Failed to fetch")) {
            toast({
              title: "Connection error",
              description: "Could not connect to the server. Please check if the backend is running.",
              variant: "destructive",
            });
          } else {
            toast({
              title: "Error",
              description: errorMsg,
              variant: "destructive",
            });
          }
        } finally {
          setIsTranscribing(false);
        }
      };

      mediaRecorder.start();
      setIsRecording(true);
      
      toast({
        title: "Recording started",
        description: "Click the microphone again to stop recording",
      });
    } catch (error) {
      toast({
        title: "Microphone access denied",
        description: "Please allow microphone access to use voice input",
        variant: "destructive",
      });
    }
  };
  return <Card className="flex flex-col h-full p-3 sm:p-4 bg-card border border-border shadow-sm">
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
          {introMessage && <div className="flex justify-start">
              <div className="bg-teal-100 text-teal-800 text-sm rounded-md p-2 max-w-[85%] prose prose-sm prose-teal [&>p]:my-1 [&_strong]:text-teal-900 [&_table]:w-full [&_table]:text-xs [&_th]:text-left [&_th]:p-1 [&_th]:border-b [&_th]:border-teal-300 [&_td]:p-1 [&_td]:border-b [&_td]:border-teal-200">
                <ReactMarkdown remarkPlugins={[remarkGfm]}>{introMessage}</ReactMarkdown>
              </div>
            </div>}
          
          {messages.map((msg, idx) => {
            const isLastMessage = idx === messages.length - 1;
            const isLastAssistantMessage = msg.role === 'assistant' && isLastMessage;
            return <div key={idx} className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}>
              <div className={`text-sm rounded-md p-2 max-w-[85%] ${msg.role === 'user' ? 'bg-primary text-primary-foreground' : 'bg-teal-100 text-teal-800 prose prose-sm prose-teal max-w-none [&>p]:my-1 [&>ol]:my-1 [&>ul]:my-1 [&_strong]:text-teal-900 [&_li]:my-0.5 [&_table]:w-full [&_table]:text-xs [&_th]:text-left [&_th]:p-1 [&_th]:border-b [&_th]:border-teal-300 [&_td]:p-1 [&_td]:border-b [&_td]:border-teal-200'}`}>
                {msg.role === 'assistant' ? (
                  <StreamingChatMessage 
                    content={msg.content} 
                    messageIndex={idx}
                    isLastMessage={isLastAssistantMessage}
                    isLoading={isLoading && isLastAssistantMessage}
                  />
                ) : (
                  msg.content
                )}
              </div>
            </div>;
          })}
          
          {isLoading && <div className="flex justify-start">
              <div className="bg-teal-100 text-teal-800 text-sm rounded-md p-2">
                <Loader2 className="h-3 w-3 animate-spin" />
              </div>
            </div>}
          
          {/* Scroll anchor */}
          <div ref={messagesEndRef} />
        </div>
      </ScrollArea>

      {/* Input section - pinned at bottom */}
      <div className="space-y-2 shrink-0">
        <form onSubmit={handleSubmit} className="flex gap-1.5 items-center">
          <Input value={input} onChange={e => setInput(e.target.value)} disabled={isLoading} className="flex-1 h-8 text-xs" placeholder="Ask a question..." />
          <Button 
            type="button" 
            variant={isRecording ? "destructive" : "outline"} 
            size="icon" 
            onClick={handleVoiceInput} 
            disabled={isLoading || isTranscribing} 
            className="h-8 w-8 shrink-0"
          >
            {isTranscribing ? (
              <Loader2 className="h-3.5 w-3.5 animate-spin" />
            ) : (
              <Mic className={`h-3.5 w-3.5 ${isRecording ? 'animate-pulse' : ''}`} />
            )}
          </Button>
          <Button type="submit" size="icon" disabled={isLoading || !input.trim()} className="h-8 w-8 shrink-0 bg-teal-600 hover:bg-teal-700 text-white">
            <Send className="h-3.5 w-3.5" />
          </Button>
        </form>

        {/* Quick questions */}
        <div className="flex gap-1.5 overflow-x-auto pb-0.5 -mx-1 px-1 scrollbar-hide">
          {quickQuestionLabels.map((label, idx) => <button key={idx} onClick={() => handleQuickQuestion(label)} disabled={isLoading} className="text-[10px] px-2 py-1 rounded-full bg-teal-100 text-teal-700 hover:bg-teal-200 transition-colors disabled:opacity-50 whitespace-nowrap shrink-0">
              {label}
            </button>)}
        </div>
        
        <p className="text-[10px] text-muted-foreground/60 italic text-center">
          Generated from patient-provided information. AI may make errors, please verify all critical details.               
        </p>
      </div>
    </Card>;
}