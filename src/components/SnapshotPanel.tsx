import { useState, useEffect } from "react";
import { Card } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { ScrollArea } from "@/components/ui/scroll-area";
import { FileText } from "lucide-react";
import { useStreamingText } from "@/hooks/useStreamingText";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import type { PatientSummary } from "@/lib/api";
import { parseStreamingSummary } from "@/utils/summaryParser";

interface SnapshotPanelProps {
  summary: PatientSummary | null;
  isLoading: boolean;
  error: string | null;
  streamedContent?: string; // For streaming content
  isStreaming?: boolean; // For streaming state
}

function StreamingBulletPoint({
  text,
  index,
  isActive,
  onComplete
}: {
  text: string;
  index: number;
  isActive: boolean;
  onComplete?: () => void;
}) {
  // All bullets stream with slow character-by-character animation
  const {
    displayedText,
    isStreaming
  } = useStreamingText(text, {
    speed: 30, // Character-by-character streaming speed (ms per character) - slower
    enabled: true, // Stream all bullets with slow animation
    mode: "character", // Stream character-by-character
  });
  
  // Notify parent when streaming completes
  useEffect(() => {
    if (!isStreaming && onComplete) {
      onComplete();
    }
  }, [isStreaming, onComplete]);
  
  return <li className="flex items-start gap-2">
      <span className="text-primary mt-0.5">•</span>
      <span className="text-sm text-muted-foreground leading-relaxed prose prose-sm max-w-none prose-p:m-0 prose-strong:text-foreground prose-strong:font-semibold">
        <ReactMarkdown remarkPlugins={[remarkGfm]}>{displayedText}</ReactMarkdown>
        {isStreaming && <span className="inline-block w-1 h-3 bg-muted-foreground/50 ml-0.5 animate-pulse" />}
      </span>
    </li>;
}

export function SnapshotPanel({
  summary,
  isLoading,
  error,
  streamedContent,
  isStreaming
}: SnapshotPanelProps) {
  const [streamedText, setStreamedText] = useState("");
  const [streamedHeadlineText, setStreamedHeadlineText] = useState("");
  const [parsedBullets, setParsedBullets] = useState<string[]>([]);
  const [currentBullet, setCurrentBullet] = useState("");
  const [visibleCount, setVisibleCount] = useState(0);
  const [lastProcessedLength, setLastProcessedLength] = useState(0);

  // Handle streaming content - parse bullets incrementally for sequential display
  useEffect(() => {
    if (streamedContent !== undefined && streamedContent) {
      setStreamedText(streamedContent);
      
      // Only re-parse if content has grown significantly to avoid constant re-renders
      const contentGrowth = streamedContent.length - lastProcessedLength;
      if (contentGrowth > 10 || !isStreaming) {
        const { headline, parsedBullets: bullets, currentBullet: current } = parseStreamingSummary(streamedContent);
        
        setStreamedHeadlineText(headline);
        
        // Only update bullets if we have new complete bullets
        if (bullets.length > parsedBullets.length) {
          setParsedBullets(bullets);
        }
        
        // Update current bullet being streamed (filter out empty lines)
        const cleanCurrent = current.trim().replace(/\n\s*\n/g, '\n').trim();
        if (cleanCurrent !== currentBullet) {
          setCurrentBullet(cleanCurrent);
        }
        
        setLastProcessedLength(streamedContent.length);
      }
    }
  }, [streamedContent, isStreaming, lastProcessedLength]);
  
  // Start showing first bullet when parsing begins
  useEffect(() => {
    if (parsedBullets.length > 0 && visibleCount === 0) {
      setVisibleCount(1);
    }
  }, [parsedBullets.length, visibleCount]);

  // Use streamed headline if available, otherwise use summary headline
  const headlineToDisplay = streamedHeadlineText || summary?.headline || null;
  
  const {
    displayedText: streamedHeadline,
    isStreaming: isStreamingHeadline
  } = useStreamingText(headlineToDisplay, {
    speed: 30, // Slower character-by-character streaming
    enabled: !streamedHeadlineText, // Only use animation if not streaming
    mode: "character", // Stream character-by-character
  });

  // Determine which bullets to display
  // Sequential streaming: show only visible bullets + current bullet if still streaming
  let displayBullets: string[];
  if (streamedText && parsedBullets.length > 0) {
    // Show completed bullets up to visibleCount
    const visibleCompleted = parsedBullets.slice(0, visibleCount);
    // Add current bullet if we're still streaming and have shown all completed ones
    if (currentBullet && visibleCount >= parsedBullets.length) {
      displayBullets = [...visibleCompleted, currentBullet];
    } else {
      displayBullets = visibleCompleted;
    }
  } else {
    // Use summary bullets if not streaming
    displayBullets = summary?.content || [];
  }
  
  const displayHeadline = streamedHeadlineText || streamedHeadline || summary?.headline;
  
  // Callback when a bullet finishes streaming
  const handleBulletComplete = () => {
    // Show next bullet when current one completes
    if (visibleCount < parsedBullets.length) {
      setTimeout(() => setVisibleCount(prev => prev + 1), 100);
    }
  };

  return <Card className="p-5 bg-card border border-border shadow-sm h-full flex flex-col">
      <div className="flex items-center gap-2 mb-3">
        <div className="w-8 h-8 rounded-lg bg-primary/10 flex items-center justify-center">
          <FileText className="h-4 w-4 text-primary" />
        </div>
        <h3 className="text-sm font-semibold text-foreground">
          Patient Summary - Upto Date      
        </h3>
      </div>
      
      <div className="relative flex-1 min-h-0">
        <ScrollArea className="h-full max-h-[200px] sm:max-h-[280px] overflow-y-auto">
          <div className="pr-4 pb-4">
            {error && <p className="text-sm text-destructive">{error}</p>}
            
            {(summary || streamedText || isLoading) && <div className="space-y-3">
                <h4 className="text-base font-semibold text-foreground">
                  {displayHeadline ? (
                    <>
                      {displayHeadline.startsWith("Overall Status:") ? displayHeadline : `Overall Status: ${displayHeadline}`}
                      {(isStreamingHeadline || (isStreaming && !streamedHeadlineText)) && <span className="inline-block w-1 h-4 bg-foreground/50 ml-0.5 animate-pulse" />}
                    </>
                  ) : (
                    "Overall Status: Loading..."
                  )}
                </h4>
                
                {displayBullets.length > 0 ? (
                  <ul className="text-sm text-muted-foreground leading-relaxed space-y-1.5">
                    {displayBullets.map((bullet, idx) => (
                      <StreamingBulletPoint
                        key={idx}
                        text={bullet}
                        index={idx}
                        isActive={idx === displayBullets.length - 1 && (isStreaming || !!currentBullet)}
                        onComplete={idx === visibleCount - 1 ? handleBulletComplete : undefined}
                      />
                    ))}
                  </ul>
                ) : isLoading ? (
                  <div className="space-y-2">
                    <Skeleton className="h-4 w-full" />
                    <Skeleton className="h-4 w-5/6" />
                    <Skeleton className="h-4 w-full" />
                  </div>
                ) : null}
                
                {(summary || displayBullets.length > 0) && (
                  <p className="text-xs text-muted-foreground/70 italic mt-4 pt-2 border-t border-border">
                    Generated from patient-provided information. AI may make errors, please verify all critical details.
                  </p>
                )}
              </div>}
          </div>
        </ScrollArea>
        <div className="absolute bottom-0 left-0 right-4 h-6 bg-gradient-to-t from-card to-transparent pointer-events-none" />
      </div>
    </Card>;
}