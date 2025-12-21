import { Card } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { User, Activity, ClipboardList, Pill, AlertCircle, ScanLine, Calendar, FileHeart } from "lucide-react";

const quickLinks = [
  { label: "Demographics", icon: User },
  { label: "Current Vitals", icon: Activity },
  { label: "Lab Results", icon: ClipboardList },
  { label: "Medications", icon: Pill },
  { label: "Allergies", icon: AlertCircle },
  { label: "Imaging", icon: ScanLine },
  { label: "Appointments", icon: Calendar },
  { label: "Care Plan", icon: FileHeart },
];

export function QuickLinks() {
  return (
    <Card className="p-4 bg-card border border-border shadow-sm">
      <h3 className="text-sm font-semibold text-foreground mb-3">Quick Links</h3>
      <div className="flex gap-2 overflow-x-auto pb-1 scrollbar-hide">
        {quickLinks.map((link) => (
          <Button
            key={link.label}
            variant="outline"
            size="sm"
            className="flex items-center gap-2 text-muted-foreground hover:text-foreground whitespace-nowrap shrink-0"
          >
            <link.icon className="h-4 w-4" />
            {link.label}
          </Button>
        ))}
      </div>
    </Card>
  );
}
