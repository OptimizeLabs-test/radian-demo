import { useState, useEffect } from "react";
import { useParams, useNavigate, Link } from "react-router-dom";
import { User, ArrowLeft } from "lucide-react";
import { Button } from "@/components/ui/button";
import { SnapshotPanel } from "@/components/SnapshotPanel";
import { SpecialtyPerspectives } from "@/components/SpecialtyPerspectives";
import { ConversationalAgent } from "@/components/ConversationalAgent";
import { QuickLinks } from "@/components/QuickLinks";
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
  fetchSpecialties,
  fetchIntroMessage,
  sendChatQuestion,
  type PatientSummary,
  type SpecialtyPerspective,
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
  const [perspectives, setPerspectives] = useState<SpecialtyPerspective[]>([]);
  const [introMessage, setIntroMessage] = useState<string | null>(null);
  const [messages, setMessages] = useState<ChatMessage[]>([]);

  // Loading states
  const [isLoadingSummary, setIsLoadingSummary] = useState(false);
  const [isLoadingPerspectives, setIsLoadingPerspectives] = useState(false);
  const [isLoadingChat, setIsLoadingChat] = useState(false);

  // Error states
  const [summaryError, setSummaryError] = useState<string | null>(null);
  const [perspectivesError, setPerspectivesError] = useState<string | null>(null);

  useEffect(() => {
    if (!patientId) return;

    const loadPatientData = async () => {
      setIsLoadingSummary(true);
      setIsLoadingPerspectives(true);
      setSummaryError(null);
      setPerspectivesError(null);

      try {
        const [summaryData, perspectivesData, introMsg] = await Promise.all([
          fetchSummary(patientId),
          fetchSpecialties(patientId),
          fetchIntroMessage(patientId),
        ]);

        setSummary(summaryData);
        setPerspectives(perspectivesData);
        setIntroMessage(introMsg);
      } catch (error) {
        const errorMsg = error instanceof Error ? error.message : "Failed to load patient data";
        setSummaryError(errorMsg);
        setPerspectivesError(errorMsg);
        toast({
          title: "Error loading patient data",
          description: errorMsg,
          variant: "destructive",
        });
      } finally {
        setIsLoadingSummary(false);
        setIsLoadingPerspectives(false);
      }
    };

    loadPatientData();
  }, [patientId, toast]);

  const handleSendMessage = async (message: string) => {
    if (!patientId) return;

    const userMessage: ChatMessage = { role: "user", content: message };
    setMessages(prev => [...prev, userMessage]);
    setIsLoadingChat(true);

    try {
      const response = await sendChatQuestion(
        patientId,
        message,
        [...messages, userMessage]
      );

      const assistantMessage: ChatMessage = { role: "assistant", content: response };
      setMessages(prev => [...prev, assistantMessage]);
    } catch (error) {
      const errorMsg = error instanceof Error ? error.message : "Failed to send message";
      toast({
        title: "Error",
        description: errorMsg,
        variant: "destructive",
      });
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
            <p className="text-sm text-muted-foreground">Clinical Dashboard</p>
          </div>
        </div>

        {/* Quick Links */}
        <QuickLinks />

        {/* Patient Summary */}
        <SnapshotPanel
          summary={summary}
          isLoading={isLoadingSummary}
          error={summaryError}
        />

        {/* Clinical Assistant */}
        <ConversationalAgent
          introMessage={introMessage}
          onSendMessage={handleSendMessage}
          messages={messages}
          isLoading={isLoadingChat}
        />

        {/* Specialty Perspectives (at bottom) */}
        <SpecialtyPerspectives
          perspectives={perspectives}
          isLoading={isLoadingPerspectives}
          error={perspectivesError}
        />
      </div>
    </Layout>
  );
}
