import { ReactNode } from "react";
import { useLocation, useNavigate } from "react-router-dom";
import { Button } from "@/components/ui/button";
import { useAuth } from "@/contexts/AuthContext";
import { LogOut, Activity } from "lucide-react";
interface LayoutProps {
  children: ReactNode;
}
export function Layout({
  children
}: LayoutProps) {
  const location = useLocation();
  const navigate = useNavigate();
  const {
    isAuthenticated,
    setIsAuthenticated,
    setSelectedPatientId
  } = useAuth();
  const handleLogout = () => {
    setIsAuthenticated(false);
    setSelectedPatientId(null);
    navigate("/");
  };
  const getPageTitle = () => {
    if (location.pathname === "/patients") {
      return "Patients";
    } else if (location.pathname.startsWith("/doctor/")) {
      return "Clinical Dashboard";
    }
    return "";
  };
  return <div className="min-h-screen bg-background">
      {/* Header */}
      <header className="border-b border-border bg-card sticky top-0 z-50">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between h-16">
            {/* Logo */}
            <div className="flex items-center gap-3">
              <img alt="Radiant Logo" src="/lovable-uploads/31370a3b-5c4f-4580-8203-70d58d16841a.png" className="w-10 h-10 object-contain" />
              <div>
                <h1 className="text-lg font-bold text-foreground">RADIAN</h1>
                <p className="text-xs text-muted-foreground">Doctor Dashboard</p>
              </div>
            </div>

            {/* Page title - center */}
            <div className="hidden md:block">
              <span className="text-sm font-medium text-muted-foreground">
                {getPageTitle()}
              </span>
            </div>

            {/* Actions */}
            <div className="flex items-center gap-4">
              {isAuthenticated && <Button variant="ghost" size="sm" onClick={handleLogout} className="text-muted-foreground hover:text-foreground">
                  <LogOut className="h-4 w-4 mr-2" />
                  Sign Out
                </Button>}
            </div>
          </div>
        </div>
      </header>

      {/* Main content */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {children}
      </main>
    </div>;
}