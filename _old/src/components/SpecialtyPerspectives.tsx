import { Card } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Heart, Activity } from "lucide-react";
import { useStreamingText } from "@/hooks/useStreamingText";
import type { SpecialtyPerspective } from "@/lib/api";

interface SpecialtyPerspectivesProps {
  perspectives: SpecialtyPerspective[];
  isLoading: boolean;
  error: string | null;
}

function StreamingInsight({ text }: { text: string }) {
  const { displayedText, isStreaming } = useStreamingText(text, { speed: 8, enabled: true });
  
  return (
    <li className="text-xs leading-relaxed list-disc text-muted-foreground">
      {displayedText}
      {isStreaming && <span className="inline-block w-1 h-3 bg-muted-foreground/50 ml-0.5 animate-pulse" />}
    </li>
  );
}

export function SpecialtyPerspectives({
  perspectives,
  isLoading,
  error
}: SpecialtyPerspectivesProps) {
  return (
    <Card className="p-5 bg-secondary/10 border border-secondary/20 shadow-sm h-full flex flex-col">
      <div className="flex items-center gap-2 mb-3">
        <div className="w-8 h-8 rounded-lg bg-secondary/10 flex items-center justify-center">
          <Activity className="h-4 w-4 text-secondary" />
        </div>
        <h3 className="text-sm font-semibold text-foreground">
          Specialty Perspectives
        </h3>
      </div>
      
      <ScrollArea className="flex-1 max-h-[300px]">
        <div className="pr-4">
          {isLoading && (
            <div className="space-y-4">
              {[1, 2].map(i => (
                <div key={i} className="space-y-2">
                  <Skeleton className="h-5 w-32" />
                  <Skeleton className="h-4 w-full" />
                  <Skeleton className="h-4 w-5/6" />
                </div>
              ))}
            </div>
          )}
          
          {error && <p className="text-sm text-destructive">{error}</p>}
          
          {perspectives.length > 0 && !isLoading && (
            <div className="space-y-4">
              {perspectives.map((perspective, idx) => (
                <div key={idx} className="space-y-2">
                  <div className="flex items-center gap-2">
                    {perspective.specialty.includes("Cardiology") ? (
                      <Heart className="h-4 w-4 text-destructive" />
                    ) : (
                      <Activity className="h-4 w-4 text-secondary" />
                    )}
                    <h4 className="text-sm font-bold text-foreground">
                      {perspective.specialty}
                    </h4>
                  </div>
                  <ul className="space-y-1.5 ml-6">
                    {perspective.insights.map((insight, iIdx) => (
                      <StreamingInsight key={iIdx} text={insight} />
                    ))}
                  </ul>
                </div>
              ))}
              <p className="text-xs text-muted-foreground/70 italic mt-4 pt-2 border-t border-border">
                Each perspective is powered by specialty-specific agents using the same patient vector data.
              </p>
            </div>
          )}
        </div>
      </ScrollArea>
    </Card>
  );
}
