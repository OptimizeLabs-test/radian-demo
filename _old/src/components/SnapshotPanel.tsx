import { Card } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { ScrollArea } from "@/components/ui/scroll-area";
import { FileText } from "lucide-react";
import { useStreamingText } from "@/hooks/useStreamingText";
import type { PatientSummary } from "@/lib/api";

interface SnapshotPanelProps {
  summary: PatientSummary | null;
  isLoading: boolean;
  error: string | null;
}

function StreamingBulletPoint({ text, index }: { text: string; index: number }) {
  const { displayedText, isStreaming } = useStreamingText(text, { speed: 15, enabled: true });
  
  return (
    <li className="flex items-start gap-2">
      <span className="text-primary mt-0.5">•</span>
      <span>
        {displayedText}
        {isStreaming && <span className="inline-block w-1 h-3 bg-muted-foreground/50 ml-0.5 animate-pulse" />}
      </span>
    </li>
  );
}

export function SnapshotPanel({ summary, isLoading, error }: SnapshotPanelProps) {
  const { displayedText: streamedHeadline, isStreaming: isStreamingHeadline } = useStreamingText(
    summary?.headline || null,
    { speed: 20, enabled: true }
  );

  return (
    <Card className="p-5 bg-card border border-border shadow-sm h-full flex flex-col">
      <div className="flex items-center gap-2 mb-3">
        <div className="w-8 h-8 rounded-lg bg-primary/10 flex items-center justify-center">
          <FileText className="h-4 w-4 text-primary" />
        </div>
        <h3 className="text-sm font-semibold text-foreground">
          Patient Summary
        </h3>
      </div>
      
      <ScrollArea className="flex-1 min-h-0 max-h-[280px]">
        <div className="pr-4">
          {isLoading && (
            <div className="space-y-2">
              <Skeleton className="h-6 w-3/4" />
              <Skeleton className="h-4 w-full" />
              <Skeleton className="h-4 w-full" />
              <Skeleton className="h-4 w-5/6" />
            </div>
          )}
          
          {error && (
            <p className="text-sm text-destructive">{error}</p>
          )}
          
          {summary && !isLoading && (
            <div className="space-y-3">
              <h4 className="text-base font-semibold text-foreground">
                Overall Status: {streamedHeadline}
                {isStreamingHeadline && <span className="inline-block w-1 h-4 bg-foreground/50 ml-0.5 animate-pulse" />}
              </h4>
              <ul className="text-sm text-muted-foreground leading-relaxed space-y-1.5">
                {summary.content.map((point, idx) => (
                  <StreamingBulletPoint key={idx} text={point} index={idx} />
                ))}
              </ul>
              <p className="text-xs text-muted-foreground/70 italic mt-4 pt-2 border-t border-border">
                Generated using the full patient record from the TARA vector store.
              </p>
            </div>
          )}
        </div>
      </ScrollArea>
    </Card>
  );
}
