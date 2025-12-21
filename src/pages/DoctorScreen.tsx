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

export default function DoctorScreen() {
  const { patientId } = useParams<{ patientId: string }>();
  const navigate = useNavigate();
  const { toast } = useToast();

  // Extract patient name from ID
  const patientName = patientId?.replace(/^P\d+-/, "").replace(/-/g, " ") || "Unknown Patient";

  // Data states
  const [summary, setSummary] = useState<PatientSummary | null>(null);
  const [introMessage, setIntroMessage] = useState<string | null>(null);
  const [messages, setMessages] = useState<ChatMessage[]>([]);

  // Loading states
  const [isLoadingSummary, setIsLoadingSummary] = useState(false);
  const [isLoadingChat, setIsLoadingChat] = useState(false);

  // Error states
  const [summaryError, setSummaryError] = useState<string | null>(null);

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

      try {
        // Fetch summary first
        const summaryData = await fetchSummary(patientId);
        setSummary(summaryData);
        
        // Old approach: Set intro message immediately (commented out)
        // setIntroMessage("Hello, Doctor. What would you like to know today?");
        
        // Old approach: Parallel API calls (commented out)
        // const [summaryData, introMsg] = await Promise.all([
        //   fetchSummary(patientId),
        //   fetchIntroMessage(patientId),
        // ]);
        // setSummary(summaryData);
        // setIntroMessage(introMsg);
      } catch (error) {
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
      let response: string;
      
      if (predefinedAnswer) {
        // Use the predefined answer instead of calling API
        response = predefinedAnswer;
      } else {
        response = await sendChatQuestion(
          patientId,
          message,
          [...messages, userMessage]
        );
      }

      const assistantMessage: ChatMessage = { role: "assistant", content: response };
      setMessages(prev => [...prev, assistantMessage]);
    } catch (error) {
      const errorMsg = error instanceof Error ? error.message : "Failed to send message";
      console.error('Error sending message:', error);
      toast({
        title: "Error",
        description: errorMsg,
        variant: "destructive",
      });
      // Remove the user message if the request failed
      setMessages(prev => prev.slice(0, -1));
    } finally {
      setIsLoadingChat(false);
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
        {!isLoadingSummary && (summary || summaryError) && (
          <SnapshotPanel
            summary={summary}
            isLoading={false}
            error={summaryError}
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
        {!isLoadingSummary && introMessage && (
          <ConversationalAgent
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
