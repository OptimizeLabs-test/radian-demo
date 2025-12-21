import { useNavigate } from "react-router-dom";
import { useAuth } from "@/contexts/AuthContext";
import { useToast } from "@/hooks/use-toast";
import radiantDoor from "@/assets/radiant-door.png";
import radianLogo from "@/assets/radian-logo-new.png";
export default function HomeScreen() {
  const navigate = useNavigate();
  const {
    setIsAuthenticated
  } = useAuth();
  const {
    toast
  } = useToast();
  const handleDoctorLogin = () => {
    setIsAuthenticated(true);
    navigate("/patients");
  };
  const handlePatientLogin = () => {
    toast({
      title: "Coming Soon",
      description: "Patient login coming soon."
    });
  };
  return <div className="h-[100dvh] bg-gray-50 flex flex-col animate-fade-in overflow-hidden">
      {/* Logo with name at top */}
      <div className="pt-4 sm:pt-6 md:pt-8 flex justify-center">
        <img src={radianLogo} alt="Radian Logo" className="h-44 sm:h-24 md:h-32 w-auto object-contain" />
      </div>

      {/* Main content - centered */}
      <div className="flex-1 flex flex-col items-center justify-center">
        <img alt="Radiant" className="h-16 sm:h-20 md:h-24 w-auto object-contain drop-shadow-xl" src="/lovable-uploads/d3104b94-b190-44bc-a190-187b06dd785e.png" />
      </div>

      {/* Bottom section - Door, Enter Radiant, and Buttons */}
      <div className="pb-6 sm:pb-8 md:pb-12 flex-col flex items-center gap-3 sm:gap-4">
        {/* Door above Enter Radiant text */}
        <button onClick={handleDoctorLogin} className="flex flex-col items-center gap-1 text-muted-foreground hover:text-foreground transition-colors duration-200 group">
          <img src={radiantDoor} alt="Enter" className="h-10 sm:h-12 md:h-14 w-auto opacity-70 group-hover:opacity-100 transition-opacity duration-200" />
          <span className="text-xs sm:text-sm font-medium tracking-widest uppercase">
            Enter Radian
          </span>
        </button>

        {/* Floating rectangular buttons */}
        <div className="flex gap-3 sm:gap-4 mt-2 sm:mt-4">
          <button onClick={handlePatientLogin} className="sm:px-12 py-2 sm:py-2.5 bg-teal-600 text-white font-semibold sm:text-base tracking-wide rounded-md hover:bg-teal-700 transition-colors duration-200 shadow-md px-[40px] text-lg">
            Patient
          </button>
          <button onClick={handleDoctorLogin} className="sm:px-12 py-2 sm:py-2.5 bg-teal-600 text-white font-semibold sm:text-base tracking-wide rounded-md hover:bg-teal-700 transition-colors duration-200 shadow-md px-[40px] text-lg">
            Doctor
          </button>
        </div>
      </div>
    </div>;
}