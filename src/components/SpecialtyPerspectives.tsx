import { Card } from "@/components/ui/card";
import { Activity } from "lucide-react";

export function SpecialtyPerspectives() {
  return (
    <Card className="p-4 bg-secondary/10 border border-secondary/20 shadow-sm">
      <div className="flex items-center gap-2">
        <div className="w-8 h-8 rounded-lg bg-secondary/10 flex items-center justify-center">
          <Activity className="h-4 w-4 text-secondary" />
        </div>
        <div>
          <h3 className="text-sm font-semibold text-foreground">
            Specialty Perspectives
          </h3>
          <p className="text-xs text-muted-foreground">Coming soon</p>
        </div>
      </div>
    </Card>
  );
}
