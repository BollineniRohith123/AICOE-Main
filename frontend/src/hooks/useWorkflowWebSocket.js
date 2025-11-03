import { useState, useEffect, useRef, useCallback } from 'react';
import { API_BASE_URL } from '../const';

/**
 * Custom hook for WebSocket-based workflow progress tracking
 * Provides real-time updates from backend as agents execute
 */
export const useWorkflowWebSocket = () => {
  const [isConnected, setIsConnected] = useState(false);
  const [currentAgent, setCurrentAgent] = useState(null);
  const [agentStatuses, setAgentStatuses] = useState({});
  const [messages, setMessages] = useState([]);
  const [error, setError] = useState(null);
  const [isComplete, setIsComplete] = useState(false);
  const [results, setResults] = useState(null);
  const [startTime, setStartTime] = useState(null);
  const [elapsedTime, setElapsedTime] = useState(0);
  
  const wsRef = useRef(null);
  const reconnectTimeoutRef = useRef(null);
  const elapsedTimerRef = useRef(null);
  const reconnectAttemptsRef = useRef(0);
  const maxReconnectAttempts = 5;
  const workflowDataRef = useRef(null); // Store workflow data for reconnection
  const workflowStartedRef = useRef(false); // Track if workflow has successfully started

  // Agent name mapping (backend names to frontend display names)
  const agentNameMap = {
    'storage': 'storage',
    'transcript': 'transcript',
    'researcher': 'researcher',
    'requirements': 'requirements',
    'knowledge_base': 'knowledge_base',
    'prd': 'prd',
    'mockup': 'mockup',
    'synthetic_data': 'synthetic_data',
    'commercial_proposal': 'commercial_proposal',
    'bom': 'bom',
    'architecture_diagram': 'architecture_diagram',
    'reviewer': 'reviewer'
  };

  // Start elapsed time counter
  useEffect(() => {
    if (startTime && !isComplete) {
      elapsedTimerRef.current = setInterval(() => {
        setElapsedTime(Math.floor((Date.now() - startTime) / 1000));
      }, 1000);
    } else {
      if (elapsedTimerRef.current) {
        clearInterval(elapsedTimerRef.current);
      }
    }
    
    return () => {
      if (elapsedTimerRef.current) {
        clearInterval(elapsedTimerRef.current);
      }
    };
  }, [startTime, isComplete]);

  // Function to restore state from backend
  const restoreState = useCallback((workflowStatus) => {
    console.log('🔄 Restoring workflow state:', workflowStatus);

    // Restore agent statuses
    if (workflowStatus.agent_statuses) {
      setAgentStatuses(workflowStatus.agent_statuses);
    }

    // Restore current agent
    if (workflowStatus.current_agent) {
      setCurrentAgent(workflowStatus.current_agent);
    }

    // Restore results if workflow is completed
    if (workflowStatus.status === 'completed' && workflowStatus.results) {
      setResults(workflowStatus.results);
      setIsComplete(true);
    }

    // Mark workflow as started
    workflowStartedRef.current = true;
  }, []);

  const connect = useCallback((workflowId, projectName, transcript, isReconnecting = false) => {
    console.log('🔧 NEW CODE LOADED - VERSION 4.0 - STATE PERSISTENCE 🔧');

    console.log('🔍 Connection parameters:', {
      workflowId,
      isReconnecting,
      workflowStarted: workflowStartedRef.current
    });

    // Store workflow data for potential reconnection
    workflowDataRef.current = { workflowId, projectName, transcript };

    // Close existing connection
    if (wsRef.current) {
      wsRef.current.close();
    }

    // Clear any pending reconnect
    if (reconnectTimeoutRef.current) {
      clearTimeout(reconnectTimeoutRef.current);
      reconnectTimeoutRef.current = null;
    }

    if (!isReconnecting) {
      // This is a new workflow - reset everything
      reconnectAttemptsRef.current = 0;
      workflowStartedRef.current = false; // Reset workflow started flag
      setAgentStatuses({});
      setMessages([]);
      setError(null);
      setIsConnected(false);
      setIsComplete(false);
      setResults(null);
      setStartTime(Date.now());
      setElapsedTime(0);
    }

    // Create WebSocket URL (convert http to ws, https to wss)
    let wsUrl;
    if (API_BASE_URL.startsWith('https://')) {
      wsUrl = API_BASE_URL.replace('https://', 'wss://') + `/api/ws/${workflowId}`;
    } else if (API_BASE_URL.startsWith('http://')) {
      wsUrl = API_BASE_URL.replace('http://', 'ws://') + `/api/ws/${workflowId}`;
    } else {
      wsUrl = 'ws://' + API_BASE_URL + `/api/ws/${workflowId}`;
    }

    console.log('Connecting to WebSocket:', wsUrl);
    console.log('API_BASE_URL:', API_BASE_URL);

    const ws = new WebSocket(wsUrl);
    wsRef.current = ws;

    ws.onopen = () => {
      console.log('WebSocket connected');
      setIsConnected(true);

      // Determine if this is a reconnection or initial connection
      // Use the isReconnecting parameter OR check if workflow was already started
      const isReconnect = isReconnecting ||
                          (reconnectAttemptsRef.current > 0 &&
                           workflowDataRef.current &&
                           workflowDataRef.current.workflowId === workflowId &&
                           workflowStartedRef.current);

      console.log('🔍 ws.onopen reconnection check:', {
        isReconnectingParam: isReconnecting,
        reconnectAttempts: reconnectAttemptsRef.current,
        workflowDataRefId: workflowDataRef.current?.workflowId,
        currentWorkflowId: workflowId,
        workflowStarted: workflowStartedRef.current,
        isReconnect
      });

      if (isReconnect) {
        // This is a reconnection - send reconnect message instead of start
        console.log('Reconnection successful! Sending reconnect message...');
        setError(null);
        setMessages(prev => [...prev, {
          from: 'System',
          message: 'Connection restored successfully',
          timestamp: new Date().toISOString(),
          type: 'success'
        }]);

        const reconnectMessage = {
          action: 'reconnect',
          workflow_id: workflowId
        };

        console.log('Sending reconnect message:', reconnectMessage);
        ws.send(JSON.stringify(reconnectMessage));

        // Mark workflow as started
        workflowStartedRef.current = true;

        // Don't reset reconnect attempts here - only reset when workflow completes
        // This ensures we continue sending "reconnect" on subsequent disconnections
      } else {
        // This is the initial connection - send start message
        const startMessage = {
          action: 'start',
          project_name: projectName,
          transcript: transcript
        };

        console.log('Sending start message:', startMessage);
        ws.send(JSON.stringify(startMessage));

        // Mark workflow as started (so future reconnections will send "reconnect")
        workflowStartedRef.current = true;

        // Add initial message (only on first connection)
        setMessages(prev => [...prev, {
          from: 'Orchestrator',
          message: `Starting workflow for project: ${projectName}`,
          timestamp: new Date().toISOString(),
          type: 'info'
        }]);
      }
    };

    ws.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        console.log('WebSocket message:', data);

        if (data.type === 'progress') {
          handleProgressUpdate(data);
        } else if (data.type === 'complete') {
          handleComplete(data);
        } else if (data.type === 'error') {
          handleError(data);
        } else if (data.type === 'reconnect_ack') {
          // Handle reconnection acknowledgment
          console.log('Reconnection acknowledged:', data);
          setMessages(prev => [...prev, {
            from: 'System',
            message: data.message || 'Reconnected to workflow',
            timestamp: new Date().toISOString(),
            type: 'info'
          }]);
        }
      } catch (err) {
        console.error('Error parsing WebSocket message:', err);
      }
    };

    ws.onerror = (event) => {
      console.error('WebSocket error:', event);
      setError('Connection error occurred - attempting to reconnect...');
      setIsConnected(false);
    };

    ws.onclose = (event) => {
      console.log('WebSocket closed:', event.code, event.reason);
      setIsConnected(false);

      // CRITICAL FIX: Do NOT reconnect if workflow has completed or failed
      // This prevents duplicate workflows from starting
      const shouldReconnect = !isComplete &&
                              workflowStartedRef.current &&
                              reconnectAttemptsRef.current < maxReconnectAttempts &&
                              workflowDataRef.current;

      console.log('🔍 WebSocket close - reconnection check:', {
        isComplete,
        workflowStarted: workflowStartedRef.current,
        reconnectAttempts: reconnectAttemptsRef.current,
        maxAttempts: maxReconnectAttempts,
        hasWorkflowData: !!workflowDataRef.current,
        shouldReconnect
      });

      // Attempt to reconnect ONLY if workflow is still running
      if (shouldReconnect) {
        reconnectAttemptsRef.current += 1;
        const delay = Math.min(1000 * Math.pow(2, reconnectAttemptsRef.current - 1), 10000); // Exponential backoff, max 10s

        console.log(`Attempting to reconnect (${reconnectAttemptsRef.current}/${maxReconnectAttempts}) in ${delay}ms...`);
        setError(`Connection lost. Reconnecting in ${Math.round(delay/1000)}s... (Attempt ${reconnectAttemptsRef.current}/${maxReconnectAttempts})`);

        reconnectTimeoutRef.current = setTimeout(() => {
          const { workflowId, projectName, transcript } = workflowDataRef.current;
          connect(workflowId, projectName, transcript, true); // CRITICAL: Pass true for reconnection
        }, delay);
      } else if (reconnectAttemptsRef.current >= maxReconnectAttempts) {
        setError('Connection lost. Maximum reconnection attempts reached. Workflow may still be running in the background.');
      } else if (isComplete) {
        console.log('✅ Workflow complete - NOT reconnecting');
      } else {
        console.log('ℹ️ Workflow not started or no data - NOT reconnecting');
      }
    };
  }, []);

  const handleProgressUpdate = (data) => {
    const { stage, status, message, timestamp } = data;
    
    // Map backend stage name to frontend agent name
    const agentName = agentNameMap[stage] || stage;
    
    // Update current agent
    if (status === 'running') {
      setCurrentAgent(agentName);
    }
    
    // Update agent status
    setAgentStatuses(prev => ({
      ...prev,
      [agentName]: {
        status: status, // 'running', 'completed', 'failed'
        message: message,
        timestamp: timestamp
      }
    }));
    
    // Add message to communication log
    const agentDisplayNames = {
      'storage': 'StorageAgent',
      'transcript': 'TranscriptAgent',
      'researcher': 'ResearcherAgent',
      'requirements': 'RequirementsAgent',
      'knowledge_base': 'KnowledgeBaseAgent',
      'prd': 'PRDAgent',
      'mockup': 'MockupAgent',
      'synthetic_data': 'SyntheticDataAgent',
      'commercial_proposal': 'CommercialProposalAgent',
      'bom': 'BOMAgent',
      'architecture_diagram': 'ArchitectureDiagramAgent',
      'reviewer': 'ReviewerAgent'
    };
    
    setMessages(prev => [...prev, {
      from: agentDisplayNames[agentName] || agentName,
      message: message,
      timestamp: timestamp,
      type: status === 'failed' ? 'error' : status === 'completed' ? 'success' : 'info'
    }]);
  };

  const handleComplete = (data) => {
    console.log('Workflow complete:', data);
    setIsComplete(true);
    // Store the entire data object, not just data.results
    // This includes project_name, workflow_id, status, and results
    setResults(data);
    setCurrentAgent(null);

    // Reset reconnect attempts and workflow started flag when workflow completes
    reconnectAttemptsRef.current = 0;
    workflowStartedRef.current = false;

    setMessages(prev => [...prev, {
      from: 'Orchestrator',
      message: 'All agents completed successfully!',
      timestamp: new Date().toISOString(),
      type: 'success'
    }]);
  };

  const handleError = (data) => {
    console.error('Workflow error:', data);
    setError(data.message);
    setIsComplete(true);

    // Reset reconnect attempts and workflow started flag when workflow fails
    reconnectAttemptsRef.current = 0;
    workflowStartedRef.current = false;

    setMessages(prev => [...prev, {
      from: 'System',
      message: `Error: ${data.message}`,
      timestamp: new Date().toISOString(),
      type: 'error'
    }]);
  };

  const disconnect = useCallback(() => {
    if (wsRef.current) {
      wsRef.current.close();
      wsRef.current = null;
    }
    
    if (reconnectTimeoutRef.current) {
      clearTimeout(reconnectTimeoutRef.current);
    }
    
    if (elapsedTimerRef.current) {
      clearInterval(elapsedTimerRef.current);
    }
    
    setIsConnected(false);
  }, []);

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      disconnect();
    };
  }, [disconnect]);

  // Format elapsed time as MM:SS
  const formatElapsedTime = () => {
    const minutes = Math.floor(elapsedTime / 60);
    const seconds = elapsedTime % 60;
    return `${minutes.toString().padStart(2, '0')}:${seconds.toString().padStart(2, '0')}`;
  };

  // Calculate progress percentage (0-100)
  const getProgressPercentage = () => {
    const totalAgents = 12; // Updated to 12 agents
    const completedAgents = Object.values(agentStatuses).filter(
      status => status.status === 'completed'
    ).length;
    return Math.round((completedAgents / totalAgents) * 100);
  };

  // Estimate time remaining based on average agent completion time
  const getEstimatedTimeRemaining = () => {
    const completedAgents = Object.values(agentStatuses).filter(
      status => status.status === 'completed'
    ).length;

    if (completedAgents === 0 || elapsedTime === 0) {
      return 'Calculating...';
    }

    const avgTimePerAgent = elapsedTime / completedAgents;
    const remainingAgents = 12 - completedAgents; // Updated to 12 agents
    const estimatedSeconds = Math.round(avgTimePerAgent * remainingAgents);

    const minutes = Math.floor(estimatedSeconds / 60);
    const seconds = estimatedSeconds % 60;

    if (minutes > 0) {
      return `~${minutes}m ${seconds}s`;
    } else {
      return `~${seconds}s`;
    }
  };

  return {
    connect,
    disconnect,
    restoreState,
    isConnected,
    currentAgent,
    agentStatuses,
    messages,
    error,
    isComplete,
    results,
    elapsedTime: formatElapsedTime(),
    progressPercentage: getProgressPercentage(),
    estimatedTimeRemaining: getEstimatedTimeRemaining()
  };
};

