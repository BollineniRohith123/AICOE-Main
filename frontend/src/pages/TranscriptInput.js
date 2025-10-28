import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { Textarea } from "@/components/ui/textarea";
import { Input } from "@/components/ui/input";
import { Loader2, Upload, ArrowRight } from "lucide-react";
import axios from "axios";
import { API_BASE_URL } from "@/const";

export default function TranscriptInput() {
  const navigate = useNavigate();
  const [projectName, setProjectName] = useState("");
  const [transcript, setTranscript] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState(null);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError(null);

    if (!projectName.trim()) {
      setError("Please enter a project name");
      return;
    }

    if (!transcript.trim()) {
      setError("Please paste a transcript");
      return;
    }

    setIsLoading(true);

    try {
      const response = await axios.post(`${API_BASE_URL}/api/process-transcript`, {
        project_name: projectName.trim(),
        transcript: transcript.trim(),
      });

      // Store result and navigate
      sessionStorage.setItem("lastResult", JSON.stringify(response.data));
      navigate("/results");
    } catch (err) {
      setError(err.response?.data?.detail || err.message || "Failed to process transcript");
      setIsLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-background">
      {/* Header */}
      <header className="border-b border-border bg-card">
        <div className="container py-6">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-3xl font-bold text-foreground">
                AICOE Automation Platform
              </h1>
              <p className="text-muted-foreground mt-1">
                Transform transcripts into structured deliverables
              </p>
            </div>
            <div className="text-right">
              <div className="inline-block px-4 py-2 bg-accent bg-opacity-10 text-accent rounded-lg">
                <span className="text-sm font-semibold">Multi-Agent v1.0</span>
              </div>
            </div>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="container py-12">
        <div className="max-w-3xl mx-auto">
          {/* Feature Overview */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-12">
            <Card className="p-6">
              <div className="flex items-center gap-3 mb-3">
                <div className="w-10 h-10 rounded-lg bg-primary bg-opacity-10 flex items-center justify-center">
                  <Upload className="w-5 h-5 text-primary" />
                </div>
                <h3 className="font-semibold text-foreground">Upload</h3>
              </div>
              <p className="text-sm text-muted-foreground">
                Paste your meeting transcript and project details
              </p>
            </Card>

            <Card className="p-6">
              <div className="flex items-center gap-3 mb-3">
                <div className="w-10 h-10 rounded-lg bg-accent bg-opacity-10 flex items-center justify-center">
                  <span className="text-lg font-bold text-accent">⚙️</span>
                </div>
                <h3 className="font-semibold text-foreground">Process</h3>
              </div>
              <p className="text-sm text-muted-foreground">
                AI agents generate PRD and mockups automatically
              </p>
            </Card>

            <Card className="p-6">
              <div className="flex items-center gap-3 mb-3">
                <div className="w-10 h-10 rounded-lg bg-primary bg-opacity-20 flex items-center justify-center">
                  <span className="text-lg font-bold text-primary">📦</span>
                </div>
                <h3 className="font-semibold text-foreground">Download</h3>
              </div>
              <p className="text-sm text-muted-foreground">
                Get structured PRD and interactive mockups
              </p>
            </Card>
          </div>

          {/* Form */}
          <Card className="p-8 border border-border">
            <form onSubmit={handleSubmit} className="space-y-6">
              <div>
                <label htmlFor="projectName" className="block text-sm font-semibold text-foreground mb-2">
                  Project Name
                </label>
                <Input
                  id="projectName"
                  type="text"
                  placeholder="e.g., Vendor Selection Platform"
                  value={projectName}
                  onChange={(e) => setProjectName(e.target.value)}
                  disabled={isLoading}
                  className="w-full"
                />
              </div>

              <div>
                <label htmlFor="transcript" className="block text-sm font-semibold text-foreground mb-2">
                  Meeting Transcript
                </label>
                <Textarea
                  id="transcript"
                  placeholder="Paste your meeting transcript here. Include attendees, objectives, discussion points, and key decisions..."
                  value={transcript}
                  onChange={(e) => setTranscript(e.target.value)}
                  disabled={isLoading}
                  className="w-full min-h-64 font-mono text-sm"
                />
                <p className="text-xs text-muted-foreground mt-2">
                  {transcript.length} characters
                </p>
              </div>

              {error && (
                <div className="p-4 bg-destructive bg-opacity-10 border border-destructive rounded-lg">
                  <p className="text-sm text-destructive font-medium">{error}</p>
                </div>
              )}

              <div className="flex gap-3 pt-4">
                <Button
                  type="submit"
                  disabled={isLoading || !projectName.trim() || !transcript.trim()}
                  className="flex-1 bg-primary hover:bg-primary/90 text-primary-foreground"
                >
                  {isLoading ? (
                    <>
                      <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                      Processing with AI Agents...
                    </>
                  ) : (
                    <>
                      Generate Deliverables
                      <ArrowRight className="w-4 h-4 ml-2" />
                    </>
                  )}
                </Button>
              </div>
            </form>
          </Card>

          {/* Info Section */}
          <div className="mt-12 p-6 bg-secondary bg-opacity-50 rounded-lg border border-border">
            <h3 className="font-semibold text-foreground mb-3">What happens next?</h3>
            <ul className="space-y-2 text-sm text-muted-foreground">
              <li className="flex gap-2">
                <span className="text-primary font-bold">1.</span>
                <span><strong>Transcript Agent</strong> extracts structured notes from your input</span>
              </li>
              <li className="flex gap-2">
                <span className="text-primary font-bold">2.</span>
                <span><strong>Requirements Agent</strong> generates detailed use cases and business requirements</span>
              </li>
              <li className="flex gap-2">
                <span className="text-primary font-bold">3.</span>
                <span><strong>PRD Agent</strong> assembles a comprehensive PRD document</span>
              </li>
              <li className="flex gap-2">
                <span className="text-primary font-bold">4.</span>
                <span><strong>Mockup Agent</strong> creates interactive Apple-style HTML mockups</span>
              </li>
            </ul>
          </div>
        </div>
      </main>
    </div>
  );
}
