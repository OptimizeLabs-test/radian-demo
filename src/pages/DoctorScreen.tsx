import { useState, useEffect } from "react";
import { useParams, useNavigate, Link } from "react-router-dom";
import { User, ArrowLeft } from "lucide-react";
import { Button } from "@/components/ui/button";
import { SnapshotPanel } from "@/components/SnapshotPanel";
import { SpecialtyPerspectives } from "@/components/SpecialtyPerspectives";
import { ConversationalAgent } from "@/components/ConversationalAgent";

import { Layout } from "@/components/Layout";
import { useToast } from "@/hooks/use-toast";
import {
  Breadcrumb,
  BreadcrumbItem,
  BreadcrumbLink,
  BreadcrumbList,
  BreadcrumbPage,
  BreadcrumbSeparator,
} from "@/components/ui/breadcrumb";
import {
  fetchSummary,
  // fetchIntroMessage, // Removed - intro message is now set directly without API call
  sendChatQuestion,
  type PatientSummary,
  type ChatMessage,
} from "@/lib/api";
import { streamSummary, streamChatResponse } from "@/lib/api/streaming";

export default function DoctorScreen() {
  const { patientId } = useParams<{ patientId: string }>();
  const navigate = useNavigate();
  const { toast } = useToast();

  // Patient ID is now just the first name (e.g., "Sanjeev")
  const patientName = patientId || "Unknown Patient";

  // Data states
  const [summary, setSummary] = useState<PatientSummary | null>(null);
  const [introMessage, setIntroMessage] = useState<string | null>(null);
  const [messages, setMessages] = useState<ChatMessage[]>([]);

  // Loading states
  const [isLoadingSummary, setIsLoadingSummary] = useState(false);
  const [isLoadingChat, setIsLoadingChat] = useState(false);

  // Error states
  const [summaryError, setSummaryError] = useState<string | null>(null);

  // Streaming states
  const [streamedSummaryText, setStreamedSummaryText] = useState("");
  const [isStreamingSummary, setIsStreamingSummary] = useState(false);

  useEffect(() => {
    if (!patientId) return;

    // Reset states when patient changes
    setSummary(null);
    setIntroMessage(null);
    setMessages([]);
    setSummaryError(null);

    const loadPatientData = async () => {
      setIsLoadingSummary(true);
      setSummaryError(null);
      setStreamedSummaryText("");
      setIsStreamingSummary(true);

      try {
        // Stream summary
        let fullText = "";
        let headline = "";
        const bullets: string[] = [];
        
        await streamSummary(
          patientId,
          (chunk) => {
            fullText += chunk;
            setStreamedSummaryText(fullText);
            
            // Parse headline as it streams
            const headlineMatch = fullText.match(/HEADLINE:\s*(.+?)(?:\n|BULLETS:)/i);
            if (headlineMatch) {
              headline = headlineMatch[1].trim();
              if (!headline.startsWith("Overall Status:")) {
                headline = `Overall Status: ${headline}`;
              }
            }
          },
          () => {
            setIsStreamingSummary(false);
            
            // Parse final bullets from full text
            const bulletsMatch = fullText.match(/BULLETS:\s*(.+)/is);
            if (bulletsMatch) {
              const bulletsText = bulletsMatch[1];
              const lines = bulletsText.split('\n');
              for (const line of lines) {
                const trimmed = line.trim();
                if (trimmed.match(/^[-•*]\s+/)) {
                  const bulletText = trimmed.replace(/^[-•*]\s+/, "").trim();
                  if (bulletText) {
                    bullets.push(bulletText);
                  }
                }
              }
            }
            
            // Finalize summary
            if (headline || bullets.length > 0) {
              setSummary({
                headline: headline || "Overall Status: Clinical Update",
                content: bullets.length > 0 ? bullets : [fullText.trim()]
              });
            } else {
              // Fallback: use full text
              setSummary({
                headline: "Overall Status: Clinical Update",
                content: [fullText.trim() || "Summary unavailable"]
              });
            }
            setStreamedSummaryText("");
          },
          (error) => {
            setIsStreamingSummary(false);
            setStreamedSummaryText("");
            const errorMsg = error.message || "Failed to load patient data";
            setSummaryError(errorMsg);
            toast({
              title: "Error loading patient data",
              description: errorMsg,
              variant: "destructive",
            });
          }
        );
      } catch (error) {
        setIsStreamingSummary(false);
        setStreamedSummaryText("");
        const errorMsg = error instanceof Error ? error.message : "Failed to load patient data";
        setSummaryError(errorMsg);
        toast({
          title: "Error loading patient data",
          description: errorMsg,
          variant: "destructive",
        });
      } finally {
        setIsLoadingSummary(false);
        // Set intro message after loading completes (whether success or error)
        // This ensures everything appears together
        setIntroMessage("Hello, Doctor. What would you like to know today?");
      }
    };

    loadPatientData();
  }, [patientId, toast]);

  const handleSendMessage = async (message: string, predefinedAnswer?: string) => {
    if (!patientId) return;

    const userMessage: ChatMessage = { role: "user", content: message };
    setMessages(prev => [...prev, userMessage]);
    setIsLoadingChat(true);

    try {
      if (predefinedAnswer) {
        // Use the predefined answer instead of calling API
        const assistantMessage: ChatMessage = { role: "assistant", content: predefinedAnswer };
        setMessages(prev => [...prev, assistantMessage]);
        setIsLoadingChat(false);
      } else {
        // Stream chat response - real-time streaming as chunks arrive
        let streamedContent = "";
        const messageAddedRef = { current: false };
        
        await streamChatResponse(
          patientId,
          message,
          [...messages, userMessage],
          (chunk) => {
            streamedContent += chunk;
            
            // Add message on first chunk (when we have content to show)
            if (!messageAddedRef.current && streamedContent.trim()) {
              messageAddedRef.current = true;
              setMessages(prev => [...prev, { role: "assistant", content: streamedContent }]);
            } else if (messageAddedRef.current) {
              // Update the last message with new content as chunks arrive (real-time)
              setMessages(prev => {
                const updated = [...prev];
                updated[updated.length - 1] = { role: "assistant", content: streamedContent };
                return updated;
              });
            }
          },
          () => {
            setIsLoadingChat(false);
          },
          (error) => {
            setIsLoadingChat(false);
            const errorMsg = error.message || "Failed to send message";
            console.error('Error sending message:', error);
            toast({
              title: "Error",
              description: errorMsg,
              variant: "destructive",
            });
            // Remove user message and assistant message (if it was added) if the request failed
            setMessages(prev => {
              const newMessages = [...prev];
              newMessages.pop(); // Remove user message
              if (messageAddedRef.current) {
                newMessages.pop(); // Remove assistant message if it was added
              }
              return newMessages;
            });
          }
        );
      }
    } catch (error) {
      setIsLoadingChat(false);
      const errorMsg = error instanceof Error ? error.message : "Failed to send message";
      console.error('Error sending message:', error);
      toast({
        title: "Error",
        description: errorMsg,
        variant: "destructive",
      });
      // Remove the user message if the request failed
      setMessages(prev => prev.slice(0, -1));
    }
  };

  return (
    <Layout>
      <div className="space-y-4">
        {/* Breadcrumb Navigation with Back Button */}
        <div className="flex items-center justify-between">
          <Breadcrumb>
            <BreadcrumbList>
              <BreadcrumbItem>
                <BreadcrumbLink asChild>
                  <Link to="/patients">Patients</Link>
                </BreadcrumbLink>
              </BreadcrumbItem>
              <BreadcrumbSeparator />
              <BreadcrumbItem>
                <BreadcrumbPage>{patientName}</BreadcrumbPage>
              </BreadcrumbItem>
            </BreadcrumbList>
          </Breadcrumb>
          <Button
            variant="ghost"
            size="sm"
            onClick={() => navigate("/patients")}
            className="text-muted-foreground hover:text-foreground"
          >
            <ArrowLeft className="h-4 w-4 mr-1" />
            Back
          </Button>
        </div>

        {/* Patient Header */}
        <div className="flex items-center gap-3">
          <div className="w-12 h-12 rounded-full bg-primary flex items-center justify-center">
            <User className="h-6 w-6 text-primary-foreground" />
          </div>
          <div>
            <h2 className="text-xl font-bold text-foreground">{patientName}</h2>
            <p className="text-sm text-muted-foreground">Clinical Dashboard • 12 files</p>
          </div>
        </div>

        {/* Patient Summary - Only show when data is ready */}
        {/* Old approach: Always show with loading state (commented out) */}
        {/* <SnapshotPanel
          summary={summary}
          isLoading={isLoadingSummary}
          error={summaryError}
        /> */}
        {(summary || streamedSummaryText || summaryError || isLoadingSummary) && (
          <SnapshotPanel
            summary={summary}
            isLoading={isLoadingSummary}
            error={summaryError}
            streamedContent={streamedSummaryText}
            isStreaming={isStreamingSummary}
          />
        )}

        {/* Clinical Assistant - Only show when loading is complete and intro message is ready */}
        {/* Old approach: Always show (commented out) */}
        {/* <ConversationalAgent
          introMessage={introMessage}
          onSendMessage={handleSendMessage}
          messages={messages}
          isLoading={isLoadingChat}
        /> */}
        {!isLoadingSummary && introMessage && patientId && (
          <ConversationalAgent
            patientId={patientId}
            introMessage={introMessage}
            onSendMessage={handleSendMessage}
            messages={messages}
            isLoading={isLoadingChat}
          />
        )}

        {/* Specialty Perspectives (at bottom) - Only show when data is ready */}
        {/* Old approach: Always show (commented out) */}
        {/* <SpecialtyPerspectives /> */}
        {!isLoadingSummary && summary && (
          <SpecialtyPerspectives />
        )}
      </div>
    </Layout>
  );
}
