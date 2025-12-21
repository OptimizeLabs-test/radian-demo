import { Card } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { User } from "lucide-react";

interface PatientRosterProps {
  onSelectPatient: (patientId: string) => void;
  selectedPatient: string | null;
  isAuthenticated: boolean;
}

export function PatientRoster({ onSelectPatient, selectedPatient, isAuthenticated }: PatientRosterProps) {
  return (
    <Card className={`p-6 border-2 ${isAuthenticated ? 'border-muted' : 'border-muted opacity-50'}`}>
      <h2 className="text-xl font-bold mb-4 text-foreground">Patient Roster</h2>
      
      <Button
        onClick={() => onSelectPatient("P1-Sanjeev")}
        disabled={!isAuthenticated}
        className={`w-full h-14 rounded-xl font-medium text-base transition-all duration-200 ${
          selectedPatient === "P1-Sanjeev"
            ? "bg-patient-pill text-white hover:bg-patient-pill/90 ring-2 ring-accent"
            : "bg-patient-pill text-white hover:bg-patient-pill/90"
        }`}
      >
        <User className="mr-2 h-5 w-5" />
        P1 – Sanjeev Malhotra
      </Button>
      
      {!isAuthenticated && (
        <p className="text-xs text-muted-foreground mt-3 text-center">
          Please authenticate to access patient records
        </p>
      )}
    </Card>
  );
}
