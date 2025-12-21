import { Card } from "@/components/ui/card";
import { Activity, Heart, TrendingUp, TrendingDown, Minus } from "lucide-react";

interface Vital {
  label: string;
  value: string;
  unit: string;
  status: "normal" | "warning" | "critical";
  trend: "up" | "down" | "stable";
}

const vitals: Vital[] = [
  { label: "Blood Pressure", value: "128/82", unit: "mmHg", status: "normal", trend: "stable" },
  { label: "Heart Rate", value: "72", unit: "bpm", status: "normal", trend: "stable" },
  { label: "HbA1c", value: "7.2", unit: "%", status: "warning", trend: "up" },
  { label: "Weight", value: "78", unit: "kg", status: "normal", trend: "down" },
  { label: "BMI", value: "26.2", unit: "", status: "warning", trend: "stable" },
];

const statusColors = {
  normal: "text-green-600 bg-green-50 dark:bg-green-950/30",
  warning: "text-amber-600 bg-amber-50 dark:bg-amber-950/30",
  critical: "text-red-600 bg-red-50 dark:bg-red-950/30",
};

const TrendIcon = ({ trend }: { trend: Vital["trend"] }) => {
  if (trend === "up") return <TrendingUp className="h-3 w-3 text-amber-500" />;
  if (trend === "down") return <TrendingDown className="h-3 w-3 text-green-500" />;
  return <Minus className="h-3 w-3 text-muted-foreground" />;
};

export function VitalsCard() {
  return (
    <Card className="p-5 bg-card border border-border shadow-sm h-full flex flex-col">
      <div className="flex items-center gap-2 mb-3">
        <div className="w-8 h-8 rounded-lg bg-destructive/10 flex items-center justify-center">
          <Heart className="h-4 w-4 text-destructive" />
        </div>
        <h3 className="text-sm font-semibold text-foreground">
          Current Vitals
        </h3>
      </div>

      <div className="flex-1 grid grid-cols-2 gap-3">
        {vitals.map((vital, idx) => (
          <div
            key={idx}
            className={`rounded-lg p-3 ${statusColors[vital.status]} ${
              idx === vitals.length - 1 && vitals.length % 2 !== 0 ? "col-span-2" : ""
            }`}
          >
            <div className="flex items-center justify-between mb-1">
              <span className="text-xs font-medium opacity-80">{vital.label}</span>
              <TrendIcon trend={vital.trend} />
            </div>
            <div className="flex items-baseline gap-1">
              <span className="text-lg font-bold">{vital.value}</span>
              <span className="text-xs opacity-70">{vital.unit}</span>
            </div>
          </div>
        ))}
      </div>

      <p className="text-[10px] text-muted-foreground/60 mt-3 italic">
        Last updated: Today, 9:15 AM
      </p>
    </Card>
  );
}
