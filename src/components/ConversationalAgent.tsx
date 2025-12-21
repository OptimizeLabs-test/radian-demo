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
interface ConversationalAgentProps {
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
export function ConversationalAgent({
  introMessage,
  onSendMessage,
  messages,
  isLoading
}: ConversationalAgentProps) {
  const [input, setInput] = useState("");
  const [pendingPredefinedKey, setPendingPredefinedKey] = useState<string | null>(null);
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
  const handleVoiceInput = () => {
    toast({
      title: "Voice input coming soon",
      description: "Speech-to-text functionality will be available in the prototype"
    });
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
          
          {messages.map((msg, idx) => <div key={idx} className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}>
              <div className={`text-sm rounded-md p-2 max-w-[85%] ${msg.role === 'user' ? 'bg-primary text-primary-foreground' : 'bg-teal-100 text-teal-800 prose prose-sm prose-teal max-w-none [&>p]:my-1 [&>ol]:my-1 [&>ul]:my-1 [&_strong]:text-teal-900 [&_li]:my-0.5 [&_table]:w-full [&_table]:text-xs [&_th]:text-left [&_th]:p-1 [&_th]:border-b [&_th]:border-teal-300 [&_td]:p-1 [&_td]:border-b [&_td]:border-teal-200'}`}>
                {msg.role === 'assistant' ? <ReactMarkdown remarkPlugins={[remarkGfm]}>{msg.content}</ReactMarkdown> : msg.content}
              </div>
            </div>)}
          
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
          <Button type="button" variant="outline" size="icon" onClick={handleVoiceInput} disabled={isLoading} className="h-8 w-8 shrink-0">
            <Mic className="h-3.5 w-3.5" />
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