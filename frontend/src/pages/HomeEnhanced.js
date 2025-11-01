import { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { 
  FileText, Zap, TrendingUp, Target, ChevronRight, 
  Sparkles, CheckCircle2, Clock, Users 
} from "lucide-react";
import "./Home.css";

export default function Home() {
  const navigate = useNavigate();
  const [isVisible, setIsVisible] = useState(false);

  useEffect(() => {
    setIsVisible(true);
  }, []);

  const features = [
    {
      icon: <Zap className="w-6 h-6" />,
      title: "Lightning Fast",
      description: "Process meeting transcripts in under 30 minutes with AI-powered automation",
      color: "from-yellow-400 to-orange-500"
    },
    {
      icon: <FileText className="w-6 h-6" />,
      title: "Complete Documentation",
      description: "Generate PRDs, mockups, proposals, BOMs, and architecture diagrams automatically",
      color: "from-blue-400 to-cyan-500"
    },
    {
      icon: <TrendingUp className="w-6 h-6" />,
      title: "95% Accuracy",
      description: "Industry-leading accuracy powered by advanced multi-agent AI systems",
      color: "from-green-400 to-emerald-500"
    },
    {
      icon: <Target className="w-6 h-6" />,
      title: "Enterprise Ready",
      description: "Built for scale with robust architecture and real-time collaboration",
      color: "from-purple-400 to-pink-500"
    }
  ];

  const stats = [
    { label: "Transcripts Processed", value: "500+", icon: <FileText className="w-5 h-5" /> },
    { label: "Average Processing Time", value: "30min", icon: <Clock className="w-5 h-5" /> },
    { label: "Accuracy Rate", value: "95%", icon: <CheckCircle2 className="w-5 h-5" /> },
    { label: "AI Agent Availability", value: "24/7", icon: <Users className="w-5 h-5" /> }
  ];

  const useCases = [
    {
      title: "Product Teams",
      description: "Transform product meetings into actionable PRDs",
      gradient: "from-blue-500 to-purple-600"
    },
    {
      title: "Enterprise",
      description: "Scale documentation across departments",
      gradient: "from-purple-500 to-pink-600"
    },
    {
      title: "Startups",
      description: "Move faster from idea to execution",
      gradient: "from-pink-500 to-red-600"
    }
  ];

  return (
    <div className="home-container">
      {/* Hero Section with Animated Background */}
      <section className="hero-section">
        <div className="hero-background">
          <div className="gradient-blob blob-1"></div>
          <div className="gradient-blob blob-2"></div>
          <div className="gradient-blob blob-3"></div>
        </div>
        
        <div className={`hero-content ${isVisible ? 'visible' : ''}`}>
          {/* Badge */}
          <div className="hero-badge">
            <Sparkles className="w-4 h-4" />
            <span>Multi-Agent AI Platform v1.0</span>
          </div>

          {/* Main Heading */}
          <h1 className="hero-title">
            Transform Meeting
            <span className="gradient-text"> Transcripts</span>
            <br />
            Into Professional Deliverables
          </h1>

          {/* Subtitle */}
          <p className="hero-subtitle">
            Automate your product development workflow with AI-powered agents that convert
            meeting transcripts into comprehensive PRDs, interactive mockups, and technical
            specifications in under 30 minutes.
          </p>

          {/* CTA Buttons */}
          <div className="hero-actions">
            <Button
              size="lg"
              className="cta-primary"
              onClick={() => navigate("/input")}
            >
              <Zap className="w-5 h-5 mr-2" />
              Start Processing Now
              <ChevronRight className="w-5 h-5 ml-2" />
            </Button>
            <Button
              size="lg"
              variant="outline"
              className="cta-secondary"
              onClick={() => {
                // Demo functionality
                alert("Demo coming soon!");
              }}
            >
              <Clock className="w-5 h-5 mr-2" />
              See Demo
            </Button>
          </div>

          {/* Trust Indicators */}
          <div className="trust-indicators">
            <div className="trust-item">
              <CheckCircle2 className="w-4 h-4 text-green-500" />
              <span>No credit card required</span>
            </div>
            <div className="trust-item">
              <CheckCircle2 className="w-4 h-4 text-green-500" />
              <span>Free for first 5 transcripts</span>
            </div>
            <div className="trust-item">
              <CheckCircle2 className="w-4 h-4 text-green-500" />
              <span>30-minute SLA</span>
            </div>
          </div>
        </div>
      </section>

      {/* Stats Section */}
      <section className="stats-section">
        <div className="container">
          <div className="stats-grid">
            {stats.map((stat, index) => (
              <Card key={index} className="stat-card">
                <div className="stat-icon">{stat.icon}</div>
                <div className="stat-value">{stat.value}</div>
                <div className="stat-label">{stat.label}</div>
              </Card>
            ))}
          </div>
        </div>
      </section>

      {/* Features Section */}
      <section className="features-section">
        <div className="container">
          <div className="section-header">
            <h2 className="section-title">
              Powerful Features for Modern Teams
            </h2>
            <p className="section-subtitle">
              Everything you need to transform meetings into action
            </p>
          </div>

          <div className="features-grid">
            {features.map((feature, index) => (
              <Card key={index} className="feature-card">
                <div className={`feature-icon bg-gradient-to-r ${feature.color}`}>
                  {feature.icon}
                </div>
                <h3 className="feature-title">{feature.title}</h3>
                <p className="feature-description">{feature.description}</p>
              </Card>
            ))}
          </div>
        </div>
      </section>

      {/* Use Cases Section */}
      <section className="use-cases-section">
        <div className="container">
          <div className="section-header">
            <h2 className="section-title">Built for Every Team</h2>
            <p className="section-subtitle">
              Trusted by product teams, enterprises, and startups worldwide
            </p>
          </div>

          <div className="use-cases-grid">
            {useCases.map((useCase, index) => (
              <Card key={index} className="use-case-card">
                <div className={`use-case-gradient bg-gradient-to-br ${useCase.gradient}`}></div>
                <div className="use-case-content">
                  <h3 className="use-case-title">{useCase.title}</h3>
                  <p className="use-case-description">{useCase.description}</p>
                  <Button variant="ghost" size="sm" className="use-case-button">
                    Learn More
                    <ChevronRight className="w-4 h-4 ml-2" />
                  </Button>
                </div>
              </Card>
            ))}
          </div>
        </div>
      </section>

      {/* How It Works */}
      <section className="how-it-works-section">
        <div className="container">
          <div className="section-header">
            <h2 className="section-title">How It Works</h2>
            <p className="section-subtitle">
              Three simple steps to transform your meetings
            </p>
          </div>

          <div className="steps-container">
            <div className="step-card">
              <div className="step-number">1</div>
              <div className="step-content">
                <h3 className="step-title">Upload Transcript</h3>
                <p className="step-description">
                  Paste your meeting transcript or upload a file
                </p>
              </div>
            </div>

            <div className="step-connector"></div>

            <div className="step-card">
              <div className="step-number">2</div>
              <div className="step-content">
                <h3 className="step-title">AI Processing</h3>
                <p className="step-description">
                  12 specialized agents work together to analyze and create
                </p>
              </div>
            </div>

            <div className="step-connector"></div>

            <div className="step-card">
              <div className="step-number">3</div>
              <div className="step-content">
                <h3 className="step-title">Get Results</h3>
                <p className="step-description">
                  Download PRDs, mockups, proposals, and more
                </p>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* CTA Section */}
      <section className="cta-section">
        <div className="container">
          <Card className="cta-card">
            <div className="cta-content">
              <h2 className="cta-title">
                Ready to Transform Your Workflow?
              </h2>
              <p className="cta-description">
                Start processing your meeting transcripts today. No credit card required.
              </p>
              <Button
                size="lg"
                className="cta-button"
                onClick={() => navigate("/input")}
              >
                <Zap className="w-5 h-5 mr-2" />
                Get Started Free
                <ChevronRight className="w-5 h-5 ml-2" />
              </Button>
            </div>
          </Card>
        </div>
      </section>
    </div>
  );
}
