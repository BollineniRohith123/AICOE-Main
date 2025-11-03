import "@/App.css";
import { BrowserRouter, Routes, Route } from "react-router-dom";
import HomeEnhanced from "@/pages/HomeEnhanced";
import TranscriptInputEnhanced from "@/pages/TranscriptInputEnhanced";
import ProcessingViewEnhanced from "@/pages/ProcessingViewEnhanced";
import Results from "@/pages/Results";

// AICOE Logo Component
const AICOELogo = () => {
  return (
    <div className="aicoe-logo">
      <div className="logo-content">
        <span className="logo-text">AICOE</span>
        <span className="logo-subtitle">AI-Powered Solutions</span>
      </div>
    </div>
  );
};

function App() {
  return (
    <div className="App">
      <BrowserRouter>
        <Routes>
          <Route path="/" element={<HomeEnhanced />} />
          <Route path="/input" element={<TranscriptInputEnhanced />} />
          <Route path="/processing" element={<ProcessingViewEnhanced />} />
          <Route path="/results" element={<Results />} />
        </Routes>
        <AICOELogo />
      </BrowserRouter>
    </div>
  );
}

export default App;
