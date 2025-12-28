import { useNavigate } from "react-router-dom";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import { User, Search, Lock } from "lucide-react";
import { useAuth } from "@/contexts/AuthContext";
import { Layout } from "@/components/Layout";

interface Patient {
  id: string;
  name: string;
  filesUploaded: number;
  available: boolean;
}

const patients: Patient[] = [
  { id: "Sanjeev", name: "Sanjeev Malhotra", filesUploaded: 12, available: true },
  { id: "Priya", name: "Priya Sharma", filesUploaded: 8, available: false },
  { id: "Amit", name: "Amit Patel", filesUploaded: 15, available: false },
  { id: "Lakshmi", name: "Lakshmi Nair", filesUploaded: 6, available: false },
];

export default function PatientRosterScreen() {
  const navigate = useNavigate();
  const { setSelectedPatientId } = useAuth();

  const handleSelectPatient = (patient: Patient) => {
    if (!patient.available) return;
    setSelectedPatientId(patient.id);
    navigate(`/doctor/${patient.id}`);
  };

  return (
    <Layout>
      <div className="flex flex-col items-center justify-center min-h-[calc(100vh-200px)] px-4">
        <Card className="p-4 sm:p-6 border border-border shadow-lg max-w-lg w-full">
          <h2 className="text-xl sm:text-2xl font-bold mb-2 text-foreground text-center">
            Patient Roster
          </h2>
          <p className="text-xs sm:text-sm text-muted-foreground mb-4 sm:mb-6 text-center">
            Select a patient to view their clinical profile
          </p>

          {/* Search bar placeholder */}
          <div className="relative mb-4">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
            <Input
              placeholder="Search patients..."
              className="pl-10"
              disabled
            />
          </div>

          {/* Patient list */}
          <div className="space-y-2">
            {patients.map((patient) => (
              <Button
                key={patient.id}
                onClick={() => handleSelectPatient(patient)}
                disabled={!patient.available}
                variant={patient.available ? "default" : "outline"}
                className={`w-full h-auto py-3 px-3 sm:px-4 rounded-xl font-medium transition-all duration-200 ${
                  patient.available
                    ? "bg-primary text-primary-foreground hover:bg-primary/90"
                    : "bg-muted/50 text-muted-foreground border-muted cursor-not-allowed"
                }`}
              >
                <div className="flex items-center justify-between w-full gap-2">
                  <div className="flex items-center gap-2 sm:gap-3 min-w-0 flex-1">
                    <div className={`w-8 h-8 sm:w-10 sm:h-10 rounded-full flex items-center justify-center shrink-0 ${
                      patient.available ? "bg-white/20" : "bg-muted"
                    }`}>
                      {patient.available ? (
                        <User className="h-4 w-4 sm:h-5 sm:w-5" />
                      ) : (
                        <Lock className="h-3 w-3 sm:h-4 sm:w-4" />
                      )}
                    </div>
                    <div className="text-left min-w-0 flex-1">
                      <div className="font-semibold text-sm sm:text-base truncate">{patient.name}</div>
                      <div className={`text-xs truncate ${patient.available ? "text-white/70" : "text-muted-foreground"}`}>
                        ({patient.filesUploaded} files)
                      </div>
                    </div>
                  </div>
                  {patient.available ? (
                    <Badge className="bg-white/20 text-white hover:bg-white/30 border-0 text-xs shrink-0 hidden sm:flex">
                      Available
                    </Badge>
                  ) : (
                    <Badge variant="outline" className="text-muted-foreground border-muted-foreground/30 text-xs shrink-0 hidden sm:flex">
                      Coming Soon
                    </Badge>
                  )}
                </div>
              </Button>
            ))}
          </div>

          <p className="text-xs text-muted-foreground mt-4 sm:mt-6 text-center">
            This demo showcases a single patient whose records are indexed in the TARA backend.
          </p>
        </Card>
      </div>
    </Layout>
  );
}
