import { useNavigate } from "react-router-dom";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { ArrowRight, Zap, FileText, Palette, Workflow } from "lucide-react";
import { APP_LOGO, APP_TITLE } from "@/const";

export default function Home() {
  const navigate = useNavigate();

  return (
    <div className="min-h-screen bg-background">
      {/* Navigation */}
      <nav className="border-b border-border bg-card sticky top-0 z-50">
        <div className="container py-4 flex items-center justify-between">
          <div className="flex items-center gap-3">
            {APP_LOGO && (
              <img src={APP_LOGO} alt="Logo" className="w-8 h-8 rounded" />
            )}
            <h1 className="text-xl font-bold text-foreground">{APP_TITLE}</h1>
          </div>
          <Button
            onClick={() => navigate("/input")}
            className="bg-primary hover:bg-primary/90 text-primary-foreground gap-2"
          >
            Get Started
            <ArrowRight className="w-4 h-4" />
          </Button>
        </div>
      </nav>

      {/* Hero Section */}
      <section className="container py-20 md:py-32">
        <div className="max-w-3xl mx-auto text-center space-y-6">
          <div className="inline-block px-4 py-2 bg-accent bg-opacity-10 text-accent rounded-full text-sm font-semibold">
            Multi-Agent Platform v1.0
          </div>
          <h1 className="text-5xl md:text-6xl font-bold text-foreground leading-tight">
            Transform Transcripts into
            <span className="text-transparent bg-clip-text bg-gradient-to-r from-primary to-accent">
              {" "}Deliverables
            </span>
          </h1>
          <p className="text-xl text-muted-foreground max-w-2xl mx-auto">
            Automatically convert meeting transcripts into structured PRDs and
            interactive Apple-style mockups in minutes using advanced AI agents.
          </p>
          <div className="flex gap-4 justify-center pt-4">
            <Button
              size="lg"
              onClick={() => navigate("/input")}
              className="bg-primary hover:bg-primary/90 text-primary-foreground gap-2"
            >
              Start Processing
              <ArrowRight className="w-5 h-5" />
            </Button>
          </div>
        </div>
      </section>

      {/* Features Section */}
      <section className="container py-16 md:py-24">
        <div className="max-w-5xl mx-auto">
          <div className="text-center mb-12">
            <h2 className="text-3xl md:text-4xl font-bold text-foreground mb-4">
              Powerful AI Agents
            </h2>
            <p className="text-lg text-muted-foreground">
              Orchestrated multi-agent system powered by Google ADK architecture
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {/* Feature 1 */}
            <Card className="p-8 border border-border hover:border-primary/50 transition-colors">
              <div className="flex items-start gap-4">
                <div className="w-12 h-12 rounded-lg bg-primary bg-opacity-10 flex items-center justify-center flex-shrink-0">
                  <Zap className="w-6 h-6 text-primary" />
                </div>
                <div>
                  <h3 className="text-lg font-semibold text-foreground mb-2">
                    Multi-Agent Orchestration
                  </h3>
                  <p className="text-muted-foreground">
                    Specialized AI agents work together: Transcript, Requirements, PRD, and Mockup agents
                  </p>
                </div>
              </div>
            </Card>

            {/* Feature 2 */}
            <Card className="p-8 border border-border hover:border-primary/50 transition-colors">
              <div className="flex items-start gap-4">
                <div className="w-12 h-12 rounded-lg bg-accent bg-opacity-10 flex items-center justify-center flex-shrink-0">
                  <FileText className="w-6 h-6 text-accent" />
                </div>
                <div>
                  <h3 className="text-lg font-semibold text-foreground mb-2">
                    Structured PRDs
                  </h3>
                  <p className="text-muted-foreground">
                    Get comprehensive Product Requirements Documents with 15+ sections
                  </p>
                </div>
              </div>
            </Card>

            {/* Feature 3 */}
            <Card className="p-8 border border-border hover:border-primary/50 transition-colors">
              <div className="flex items-start gap-4">
                <div className="w-12 h-12 rounded-lg bg-primary bg-opacity-20 flex items-center justify-center flex-shrink-0">
                  <Palette className="w-6 h-6 text-primary" />
                </div>
                <div>
                  <h3 className="text-lg font-semibold text-foreground mb-2">
                    Apple-Style Mockups
                  </h3>
                  <p className="text-muted-foreground">
                    Beautiful, clean HTML mockups following modern design principles
                  </p>
                </div>
              </div>
            </Card>

            {/* Feature 4 */}
            <Card className="p-8 border border-border hover:border-primary/50 transition-colors">
              <div className="flex items-start gap-4">
                <div className="w-12 h-12 rounded-lg bg-accent bg-opacity-20 flex items-center justify-center flex-shrink-0">
                  <Workflow className="w-6 h-6 text-accent" />
                </div>
                <div>
                  <h3 className="text-lg font-semibold text-foreground mb-2">
                    End-to-End Workflow
                  </h3>
                  <p className="text-muted-foreground">
                    Complete automation from transcript upload to downloadable artifacts
                  </p>
                </div>
              </div>
            </Card>
          </div>
        </div>
      </section>

      {/* How It Works */}
      <section className="container py-16 md:py-24">
        <div className="max-w-4xl mx-auto">
          <div className="text-center mb-12">
            <h2 className="text-3xl md:text-4xl font-bold text-foreground mb-4">
              How It Works
            </h2>
          </div>

          <div className="space-y-8">
            {/* Step 1 */}
            <div className="flex gap-6 items-start">
              <div className="flex-shrink-0">
                <div className="flex items-center justify-center h-12 w-12 rounded-lg bg-primary text-primary-foreground font-bold text-lg">
                  1
                </div>
              </div>
              <div className="flex-1">
                <h3 className="text-xl font-semibold text-foreground mb-2">
                  Upload Your Transcript
                </h3>
                <p className="text-muted-foreground">
                  Paste your meeting transcript and provide a project name. Our
                  system accepts any text format.
                </p>
              </div>
            </div>

            {/* Step 2 */}
            <div className="flex gap-6 items-start">
              <div className="flex-shrink-0">
                <div className="flex items-center justify-center h-12 w-12 rounded-lg bg-primary text-primary-foreground font-bold text-lg">
                  2
                </div>
              </div>
              <div className="flex-1">
                <h3 className="text-xl font-semibold text-foreground mb-2">
                  AI Agent Processing
                </h3>
                <p className="text-muted-foreground">
                  Multiple specialized AI agents analyze your transcript, extract requirements,
                  generate use cases, and create deliverables.
                </p>
              </div>
            </div>

            {/* Step 3 */}
            <div className="flex gap-6 items-start">
              <div className="flex-shrink-0">
                <div className="flex items-center justify-center h-12 w-12 rounded-lg bg-primary text-primary-foreground font-bold text-lg">
                  3
                </div>
              </div>
              <div className="flex-1">
                <h3 className="text-xl font-semibold text-foreground mb-2">
                  Review Results
                </h3>
                <p className="text-muted-foreground">
                  View generated PRD and interactive HTML mockup in your browser with
                  syntax highlighting and preview.
                </p>
              </div>
            </div>

            {/* Step 4 */}
            <div className="flex gap-6 items-start">
              <div className="flex-shrink-0">
                <div className="flex items-center justify-center h-12 w-12 rounded-lg bg-primary text-primary-foreground font-bold text-lg">
                  4
                </div>
              </div>
              <div className="flex-1">
                <h3 className="text-xl font-semibold text-foreground mb-2">
                  Download & Share
                </h3>
                <p className="text-muted-foreground">
                  Download your artifacts (PRD.md, Mockup.html) and share them with
                  stakeholders.
                </p>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* CTA Section */}
      <section className="container py-16 md:py-24">
        <div className="max-w-3xl mx-auto bg-gradient-to-r from-primary to-accent rounded-2xl p-12 text-center">
          <h2 className="text-3xl md:text-4xl font-bold text-white mb-4">
            Ready to Transform Your Workflow?
          </h2>
          <p className="text-white/90 text-lg mb-8">
            Start processing your first transcript today and see the power of multi-agent AI.
          </p>
          <Button
            size="lg"
            onClick={() => navigate("/input")}
            className="bg-white text-primary hover:bg-white/90 gap-2"
          >
            Get Started Now
            <ArrowRight className="w-5 h-5" />
          </Button>
        </div>
      </section>

      {/* Footer */}
      <footer className="border-t border-border bg-card mt-16">
        <div className="container py-8 text-center text-muted-foreground text-sm">
          <p>
            AICOE Automation Platform &copy; 2025. Built with Google ADK-inspired architecture.
          </p>
        </div>
      </footer>
    </div>
  );
}
