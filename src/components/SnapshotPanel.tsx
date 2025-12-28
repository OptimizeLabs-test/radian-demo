import { useState, useEffect } from "react";
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
  streamedContent?: string; // For streaming content
  isStreaming?: boolean; // For streaming state
}

function StreamingBulletPoint({
  text,
  index,
  isActive
}: {
  text: string;
  index: number;
  isActive: boolean;
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
  
  return <li className="flex items-start gap-2">
      <span className="text-primary mt-0.5">•</span>
      <span className="text-sm text-muted-foreground leading-relaxed">
        {displayedText}
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
  const [completedBullets, setCompletedBullets] = useState<string[]>([]);
  const [currentBullet, setCurrentBullet] = useState("");
  const [streamedHeadlineText, setStreamedHeadlineText] = useState("");

  // Handle streaming content - parse bullets sequentially
  useEffect(() => {
    if (streamedContent !== undefined && streamedContent) {
      setStreamedText(streamedContent);
      
      // Parse headline
      const headlineMatch = streamedContent.match(/HEADLINE:\s*(.+?)(?:\n|BULLETS:)/is);
      if (headlineMatch) {
        let headline = headlineMatch[1].trim();
        if (!headline.startsWith("Overall Status:")) {
          headline = `Overall Status: ${headline}`;
        }
        setStreamedHeadlineText(headline);
      }
      
      // Extract bullets section
      const bulletsMatch = streamedContent.match(/BULLETS:\s*(.+)/is);
      if (bulletsMatch) {
        const bulletsText = bulletsMatch[1];
        const lines = bulletsText.split('\n');
        const parsedBullets: string[] = [];
        let currentBulletLines: string[] = [];
        
        for (let i = 0; i < lines.length; i++) {
          const line = lines[i];
          const trimmedLine = line.trim();
          
          // Check if this line starts a new bullet (starts with "-", "•", or number)
          const isNewBullet = trimmedLine.match(/^[-•*]\s+/) || 
                             (trimmedLine.match(/^\d+\.\s+/) && currentBulletLines.length === 0);
          
          if (isNewBullet) {
            // If we had a current bullet, it's now complete
            if (currentBulletLines.length > 0) {
              const completedBullet = currentBulletLines.join(" ").trim();
              if (completedBullet) {
                parsedBullets.push(completedBullet);
              }
              currentBulletLines = [];
            }
            // Start new bullet (remove bullet marker)
            const bulletText = trimmedLine.replace(/^[-•*]\s+/, "").replace(/^\d+\.\s+/, "").trim();
            if (bulletText) {
              currentBulletLines.push(bulletText);
            }
          } else if (trimmedLine && currentBulletLines.length > 0) {
            // Continue current bullet (multi-line bullet)
            currentBulletLines.push(trimmedLine);
          } else if (trimmedLine && currentBulletLines.length === 0) {
            // Text without bullet marker at start - treat as new bullet
            currentBulletLines.push(trimmedLine);
          }
        }
        
        // Update completed bullets and current bullet
        setCompletedBullets(parsedBullets);
        const currentBulletText = currentBulletLines.join(" ").trim();
        setCurrentBullet(currentBulletText);
      } else {
        // Fallback: try to parse bullets without BULLETS: marker
        const lines = streamedContent.split('\n');
        const potentialBullets: string[] = [];
        let foundHeadline = false;
        
        for (const line of lines) {
          const trimmed = line.trim();
          if (trimmed.toUpperCase().startsWith('HEADLINE:')) {
            foundHeadline = true;
            continue;
          }
          if (foundHeadline && (trimmed.startsWith('-') || trimmed.startsWith('•'))) {
            const bulletText = trimmed.replace(/^[-•*]\s+/, "").trim();
            if (bulletText) {
              potentialBullets.push(bulletText);
            }
          }
        }
        
        if (potentialBullets.length > 0) {
          setCompletedBullets(potentialBullets.slice(0, -1));
          setCurrentBullet(potentialBullets[potentialBullets.length - 1] || "");
        }
      }
    }
  }, [streamedContent]);

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
  // If streaming, show completed bullets + current bullet
  // Otherwise, show summary bullets
  const displayBullets = (streamedText && (completedBullets.length > 0 || currentBullet))
    ? [...completedBullets, ...(currentBullet ? [currentBullet] : [])]
    : (summary?.content || []);
  
  const displayHeadline = streamedHeadlineText || streamedHeadline || summary?.headline;

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