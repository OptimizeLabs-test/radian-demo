import { useNavigate } from "react-router-dom";
import { useAuth } from "@/contexts/AuthContext";
import { useToast } from "@/hooks/use-toast";
import radiantDoor from "@/assets/radiant-door.png";
import radianLogo from "@/assets/radian-logo.png";
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
      {/* Logo at top */}
      <div className="pt-2 sm:pt-4 md:pt-6 flex justify-center">
        <img src={radianLogo} alt="Radiant Logo" className="h-10 sm:h-12 md:h-16 w-auto object-contain" />
      </div>

      {/* Radiant Title */}
      <div className="flex justify-center py-2 sm:py-4 md:py-[40px]">
        <h1 className="text-lg sm:text-xl md:text-2xl font-serif tracking-widest text-teal-700 uppercase">
          Radiant
        </h1>
      </div>

      {/* Main content - centered */}
      <div className="flex-1 flex flex-col items-center justify-center">
        <img alt="Radiant" className="h-16 sm:h-20 md:h-24 w-auto object-contain drop-shadow-xl" src="/lovable-uploads/bc5682ae-e8cb-46b5-81e6-fc8138c5f368.png" />
      </div>

      {/* Bottom section - Door, Enter Radiant, and Buttons */}
      <div className="pb-6 sm:pb-8 md:pb-12 flex-col flex items-center gap-3 sm:gap-4">
        {/* Door above Enter Radiant text */}
        <button onClick={handleDoctorLogin} className="flex flex-col items-center gap-1 text-muted-foreground hover:text-foreground transition-colors duration-200 group">
          <img src={radiantDoor} alt="Enter" className="h-10 sm:h-12 md:h-14 w-auto opacity-70 group-hover:opacity-100 transition-opacity duration-200" />
          <span className="text-xs sm:text-sm font-medium tracking-widest uppercase">
            Enter Radiant
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