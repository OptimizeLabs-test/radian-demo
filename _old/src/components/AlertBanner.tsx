import { useState } from "react";
import { AlertTriangle, X } from "lucide-react";
import { Button } from "@/components/ui/button";
interface Alert {
  id: string;
  message: string;
  type: "warning" | "critical";
}
const alerts: Alert[] = [{
  id: "1",
  message: "HbA1c trending upward (7.2%) – dietary review recommended",
  type: "warning"
}];
export function AlertBanner() {
  const [dismissedAlerts, setDismissedAlerts] = useState<string[]>([]);
  const visibleAlerts = alerts.filter(a => !dismissedAlerts.includes(a.id));
  if (visibleAlerts.length === 0) return null;
  const dismissAlert = (id: string) => {
    setDismissedAlerts(prev => [...prev, id]);
  };
  return (
    <div className="space-y-2">
      {visibleAlerts.map(alert => (
        <div
          key={alert.id}
          className={`flex items-center justify-between p-3 rounded-lg ${
            alert.type === "critical" ? "bg-destructive/10 text-destructive" : "bg-yellow-500/10 text-yellow-700"
          }`}
        >
          <div className="flex items-center gap-2">
            <AlertTriangle className="h-4 w-4" />
            <span className="text-sm">{alert.message}</span>
          </div>
          <Button variant="ghost" size="sm" onClick={() => dismissAlert(alert.id)}>
            <X className="h-4 w-4" />
          </Button>
        </div>
      ))}
    </div>
  );
}