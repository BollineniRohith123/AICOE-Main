import { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import {
  Download, ChevronLeft, Eye, Code, FileText, PlayCircle,
  FolderOpen, FileCode, File, CheckCircle2, XCircle, Loader2
} from "lucide-react";
import axios from "axios";
import { API_BASE_URL } from "@/const";

// Artifact Preview Component with iframe for HTML files
const ArtifactPreview = ({ content, type, title }) => {
  const [viewMode, setViewMode] = useState('preview');

  if (type === 'html' || type === 'mockup') {
    return (
      <div className="h-full flex flex-col">
        <div className="flex items-center justify-between p-4 border-b bg-gray-50">
          <h3 className="font-semibold text-lg">{title}</h3>
          <div className="flex gap-2">
            <Button
              size="sm"
              variant={viewMode === 'preview' ? 'default' : 'outline'}
              onClick={() => setViewMode('preview')}
            >
              <Eye className="w-4 h-4 mr-2" />
              Preview
            </Button>
            <Button
              size="sm"
              variant={viewMode === 'code' ? 'default' : 'outline'}
              onClick={() => setViewMode('code')}
            >
              <Code className="w-4 h-4 mr-2" />
              Code
            </Button>
          </div>
        </div>

        <div className="flex-1 overflow-auto">
          {viewMode === 'preview' ? (
            <iframe
              srcDoc={content}
              className="w-full h-full border-0"
              title={title}
              sandbox="allow-scripts allow-same-origin"
            />
          ) : (
            <pre className="p-4 text-sm bg-gray-900 text-green-400 overflow-auto h-full">
              <code>{content}</code>
            </pre>
          )}
        </div>
      </div>
    );
  }

  if (type === 'json') {
    try {
      const formatted = JSON.stringify(JSON.parse(content), null, 2);
      return (
        <div className="h-full flex flex-col">
          <div className="p-4 border-b bg-gray-50">
            <h3 className="font-semibold text-lg">{title}</h3>
          </div>
          <pre className="flex-1 p-4 text-sm bg-gray-900 text-green-400 overflow-auto">
            <code>{formatted}</code>
          </pre>
        </div>
      );
    } catch (e) {
      return <div className="p-4 text-red-500">Invalid JSON</div>;
    }
  }

  return (
    <div className="h-full flex flex-col">
      <div className="p-4 border-b bg-gray-50">
        <h3 className="font-semibold text-lg">{title}</h3>
      </div>
      <div className="flex-1 p-4 overflow-auto">
        <pre className="text-sm whitespace-pre-wrap">{content}</pre>
      </div>
    </div>
  );
};

// File Tree Component
const FileTree = ({ files, onFileSelect, selectedFile }) => {
  const [expanded, setExpanded] = useState({});
  
  const toggleFolder = (path) => {
    setExpanded(prev => ({ ...prev, [path]: !prev[path] }));
  };
  
  const renderTree = (items, level = 0) => {
    return Object.entries(items).map(([name, value]) => {
      const isFolder = typeof value === 'object' && !value.content;
      const path = `${level}-${name}`;
      const isExpanded = expanded[path];
      const isSelected = selectedFile === value?.path;

      return (
        <div key={path} style={{ marginLeft: `${level * 16}px` }}>
          <div
            className={`flex items-center gap-2 p-2 rounded cursor-pointer hover:bg-gray-100 ${
              isSelected ? 'bg-blue-100' : ''
            }`}
            onClick={() => {
              if (isFolder) {
                toggleFolder(path);
              } else if (value.content) {
                onFileSelect(value);
              }
            }}
          >
            {isFolder ? (
              <>
                <FolderOpen className="w-4 h-4 text-yellow-600" />
                <span className="font-medium">{name}</span>
                <span className="text-xs text-gray-500">
                  {isExpanded ? '▼' : '▶'}
                </span>
              </>
            ) : (
              <>
                {name.endsWith('.html') ? (
                  <FileCode className="w-4 h-4 text-orange-500" />
                ) : name.endsWith('.json') ? (
                  <File className="w-4 h-4 text-blue-500" />
                ) : (
                  <FileText className="w-4 h-4 text-gray-500" />
                )}
                <span className="text-sm">{name}</span>
              </>
            )}
          </div>
          {isFolder && isExpanded && renderTree(value, level + 1)}
        </div>
      );
    });
  };
  
  return (
    <div className="h-full overflow-auto p-2 bg-white border-r">
      {renderTree(files)}
    </div>
  );
};

export default function Results() {
  const navigate = useNavigate();
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(true);
  const [selectedFile, setSelectedFile] = useState(null);
  const [fileStructure, setFileStructure] = useState({});

  useEffect(() => {
    const stored = sessionStorage.getItem("lastResult");
    if (stored) {
      try {
        const data = JSON.parse(stored);
        setResult(data);

        // Build file structure from results
        const structure = buildFileStructure(data);
        setFileStructure(structure);

        // Select first HTML file by default
        const firstHtml = findFirstHtmlFile(structure);
        if (firstHtml) {
          setSelectedFile(firstHtml);
        }

        setLoading(false);
      } catch (error) {
        console.error("Failed to parse result:", error);
        navigate("/");
      }
    } else {
      navigate("/");
    }
  }, [navigate]);

  const buildFileStructure = (data) => {
    const structure = {
      "📁 Project Files": {}
    };

    const results = data.results || {};

    // Add PRD documents
    if (results.prd) {
      structure["📁 Project Files"]["📄 PRD"] = {
        "PRD_v1.html": {
          content: typeof results.prd === 'string' ? results.prd : JSON.stringify(results.prd, null, 2),
          type: 'html',
          path: 'prd/PRD_v1.html'
        }
      };
    }

    // Add Mockups
    if (results.mockup) {
      const mockupFolder = {};
      const mockupData = results.mockup;

      if (mockupData.mockup_pages) {
        Object.entries(mockupData.mockup_pages).forEach(([filename, content]) => {
          mockupFolder[filename] = {
            content,
            type: 'html',
            path: `mockup/${filename}`
          };
        });
      }

      structure["📁 Project Files"]["🎨 Mockups"] = mockupFolder;
    }

    // Add Requirements/Use Cases
    if (results.requirements) {
      structure["📁 Project Files"]["📋 Requirements"] = {
        "requirements.json": {
          content: JSON.stringify(results.requirements, null, 2),
          type: 'json',
          path: 'requirements/requirements.json'
        }
      };
    }

    // Add Commercial Proposal
    if (results.commercial_proposal) {
      structure["📁 Project Files"]["💼 Commercial Proposal"] = {
        "proposal_v1.html": {
          content: typeof results.commercial_proposal === 'string'
            ? results.commercial_proposal
            : JSON.stringify(results.commercial_proposal, null, 2),
          type: 'html',
          path: 'proposal/proposal_v1.html'
        }
      };
    }

    // Add BOM
    if (results.bom) {
      structure["📁 Project Files"]["📦 Bill of Materials"] = {
        "bom_v1.html": {
          content: typeof results.bom === 'string'
            ? results.bom
            : JSON.stringify(results.bom, null, 2),
          type: 'html',
          path: 'bom/bom_v1.html'
        }
      };
    }

    // Add Architecture
    if (results.architecture_diagram) {
      structure["📁 Project Files"]["🏗️ Architecture"] = {
        "architecture_v1.html": {
          content: typeof results.architecture_diagram === 'string'
            ? results.architecture_diagram
            : JSON.stringify(results.architecture_diagram, null, 2),
          type: 'html',
          path: 'architecture/architecture_v1.html'
        }
      };
    }

    // Add Research
    if (results.researcher) {
      structure["📁 Project Files"]["🔍 Research"] = {
        "research.json": {
          content: JSON.stringify(results.researcher, null, 2),
          type: 'json',
          path: 'research/research.json'
        }
      };
    }

    return structure;
  };

  const findFirstHtmlFile = (structure, found = null) => {
    for (const value of Object.values(structure)) {
      if (value.content && value.type === 'html') {
        return value;
      }
      if (typeof value === 'object' && !value.content) {
        const result = findFirstHtmlFile(value, found);
        if (result) return result;
      }
    }
    return found;
  };

  const downloadAllArtifacts = () => {
    // Create a zip-like download of all artifacts
    alert("Download all artifacts functionality will be implemented here");
  };

  if (loading || !result) {
    return (
      <div className="min-h-screen bg-background flex items-center justify-center">
        <div className="text-center">
          <Loader2 className="w-8 h-8 animate-spin mx-auto mb-4 text-primary" />
          <p className="text-muted-foreground">Loading results...</p>
        </div>
      </div>
    );
  }

  const projectName = result.project_name || "Project";
  const projectId = result.project_id;

  return (
    <div className="min-h-screen bg-gray-50 flex flex-col">
      {/* Header */}
      <header className="border-b bg-white shadow-sm z-50">
        <div className="container py-3">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-4">
              <Button
                variant="ghost"
                size="sm"
                onClick={() => navigate("/")}
                className="gap-2"
              >
                <ChevronLeft className="w-4 h-4" />
                Back
              </Button>
              <div>
                <h1 className="text-xl font-bold text-foreground">
                  {projectName} - Playground
                </h1>
                <p className="text-xs text-muted-foreground">
                  Interactive artifact viewer and code playground
                </p>
              </div>
            </div>
            <div className="flex gap-2">
              <Button
                size="sm"
                variant="outline"
                onClick={downloadAllArtifacts}
                className="gap-2"
              >
                <Download className="w-4 h-4" />
                Download All
              </Button>
            </div>
          </div>
        </div>
      </header>

      {/* Agent Status Bar */}
      <div className="bg-white border-b py-2">
        <div className="container">
          <div className="flex items-center gap-4 overflow-x-auto">
            <span className="text-sm font-medium text-gray-600 whitespace-nowrap">
              Agents:
            </span>
            {result.stages && result.stages.map((stage, idx) => (
              <div key={idx} className="flex items-center gap-2 whitespace-nowrap">
                {stage.status === "completed" ? (
                  <CheckCircle2 className="w-4 h-4 text-green-500" />
                ) : stage.status === "failed" ? (
                  <XCircle className="w-4 h-4 text-red-500" />
                ) : (
                  <Loader2 className="w-4 h-4 animate-spin text-blue-500" />
                )}
                <span className="text-sm capitalize">{stage.name}</span>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Main Playground Area */}
      <div className="flex-1 flex overflow-hidden">
        {/* File Tree Sidebar */}
        <div className="w-64 bg-white border-r flex flex-col">
          <div className="p-3 border-b bg-gray-50">
            <h2 className="font-semibold text-sm">Project Explorer</h2>
          </div>
          <FileTree
            files={fileStructure}
            onFileSelect={setSelectedFile}
            selectedFile={selectedFile?.path}
          />
        </div>

        {/* Preview Area */}
        <div className="flex-1 bg-white">
          {selectedFile ? (
            <ArtifactPreview
              content={selectedFile.content}
              type={selectedFile.type}
              title={selectedFile.path}
            />
          ) : (
            <div className="h-full flex items-center justify-center text-gray-500">
              <div className="text-center">
                <PlayCircle className="w-16 h-16 mx-auto mb-4 text-gray-300" />
                <p className="text-lg font-medium">Select a file to preview</p>
                <p className="text-sm text-gray-400 mt-2">
                  Choose a file from the project explorer
                </p>
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Footer */}
      <div className="bg-white border-t py-2">
        <div className="container flex items-center justify-between text-xs text-gray-500">
          <div>
            Workflow ID: {result.workflow_id} | Status: {result.status}
          </div>
          <div>
            {Object.keys(fileStructure).length} folders • {selectedFile ? 'File selected' : 'No file selected'}
          </div>
        </div>
      </div>
    </div>
  );
}
