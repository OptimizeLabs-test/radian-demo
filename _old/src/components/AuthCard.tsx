import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { Shield } from "lucide-react";

interface AuthCardProps {
  onAuth: () => void;
  isAuthenticated: boolean;
}

export function AuthCard({ onAuth, isAuthenticated }: AuthCardProps) {
  return (
    <Card className="p-4 border-2 border-muted">
      <Button
        onClick={onAuth}
        disabled={isAuthenticated}
        className="w-full bg-auth-green hover:bg-auth-green/90 text-white font-semibold text-lg h-12 rounded-xl transition-all duration-200 hover:scale-105"
      >
        <Shield className="mr-2 h-5 w-5" />
        {isAuthenticated ? "Authenticated" : "Auth"}
      </Button>
    </Card>
  );
}
