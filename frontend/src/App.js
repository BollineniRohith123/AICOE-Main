import "@/App.css";
import { BrowserRouter, Routes, Route } from "react-router-dom";
import Home from "@/pages/Home";
import TranscriptInput from "@/pages/TranscriptInput";
import ProcessingView from "@/pages/ProcessingView";
import Results from "@/pages/Results";
import ResultsNew from "@/pages/ResultsNew";

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
          <Route path="/" element={<Home />} />
          <Route path="/input" element={<TranscriptInput />} />
          <Route path="/processing" element={<ProcessingView />} />
          <Route path="/results" element={<ResultsNew />} />
          <Route path="/results-old" element={<Results />} />
        </Routes>
        <AICOELogo />
      </BrowserRouter>
    </div>
  );
}

export default App;
