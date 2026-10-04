import React, { useState, useEffect } from 'react';
import { 
  GitBranch, 
  Folder, 
  FileCode, 
  Sparkles, 
  Layers, 
  ExternalLink, 
  RefreshCw, 
  CheckCircle2, 
  Cpu, 
  Share2, 
  AlertTriangle, 
  ArrowRight, 
  ChevronDown, 
  ChevronUp, 
  Terminal, 
  Zap, 
  History, 
  X, 
  RotateCcw,
  Clock,
  Radio,
  Coins,
  Sun,
  Moon,
  Sliders,
  Target,
  Presentation
} from 'lucide-react';
import confetti from 'canvas-confetti';
import ArchitectureGraph from './components/ArchitectureGraph';

const DEFAULT_PRESETS_DATA = [
  {
    id: 'run-cloudshop',
    title: 'CloudShop Microservices',
    time: 'Preset',
    source_type: 'prompt',
    architecture: {
      system_title: 'CloudShop Microservices',
      summary: 'A cloud-native e-commerce platform using an SSR storefront, API gateway, domain microservices, event streaming, and distributed data stores.',
      architecture_style: 'Event-Driven Microservices',
      tech_stack: ['Next.js 15', 'FastAPI', 'Go', 'Kafka', 'PostgreSQL', 'Redis', 'Elasticsearch'],
      layers: [
        { id: 'layer_presentation', name: 'Presentation Tier', order: 1 },
        { id: 'layer_gateway', name: 'API Gateway & Ingress', order: 2 },
        { id: 'layer_services', name: 'Domain Microservices', order: 3 },
        { id: 'layer_data', name: 'Storage & Event Bus', order: 4 }
      ],
      nodes: [
        { id: 'web_storefront', name: 'Web Storefront', layer_id: 'layer_presentation', type: 'frontend', tech: 'Next.js 15 / Tailwind', description: 'SSR catalog, cart, and responsive checkout.', endpoints_or_features: ['Product Catalog', 'Cart UI'] },
        { id: 'api_gateway', name: 'API Gateway', layer_id: 'layer_gateway', type: 'gateway', tech: 'Envoy / Kong', description: 'Routes /api/v1 with JWT authentication and rate limiting.', endpoints_or_features: ['JWT Auth', 'Rate Limiter'] },
        { id: 'order_service', name: 'Order Service', layer_id: 'layer_services', type: 'service', tech: 'Go (Golang)', description: 'Manages order state machine and Stripe checkout webhooks.', endpoints_or_features: ['Order State Machine', 'Stripe Webhooks'] },
        { id: 'catalog_service', name: 'Catalog Service', layer_id: 'layer_services', type: 'service', tech: 'Python FastAPI', description: 'Product taxonomy and faceted search.', endpoints_or_features: ['Faceted Search', 'Category API'] },
        { id: 'notification_worker', name: 'Notification Worker', layer_id: 'layer_services', type: 'service', tech: 'Python Celery', description: 'Listens to Kafka events for SendGrid and Twilio alerts.', endpoints_or_features: ['Email Alerts', 'SMS Gateway'] },
        { id: 'postgres_orders', name: 'PostgreSQL Orders DB', layer_id: 'layer_data', type: 'database', tech: 'PostgreSQL 16', description: 'ACID transactional data for orders and user ledger.', endpoints_or_features: ['Orders Table', 'User Accounts'] },
        { id: 'redis_cache', name: 'Redis Cache', layer_id: 'layer_data', type: 'cache', tech: 'Redis 7', description: 'In-memory session tokens and shopping cart storage.', endpoints_or_features: ['Session Store', 'Hot Catalog Cache'] },
        { id: 'kafka_bus', name: 'Kafka Event Bus', layer_id: 'layer_data', type: 'queue', tech: 'Apache Kafka', description: 'Publishes OrderCreated and PaymentCompleted events.', endpoints_or_features: ['OrderCreated', 'StockUpdated'] }
      ],
      connections: [
        { from: 'web_storefront', to: 'api_gateway', protocol: 'HTTPS / REST', label: 'User Actions' },
        { from: 'api_gateway', to: 'order_service', protocol: 'gRPC', label: 'Create Order' },
        { from: 'api_gateway', to: 'catalog_service', protocol: 'REST', label: 'Browse Products' },
        { from: 'order_service', to: 'postgres_orders', protocol: 'SQL', label: 'Persist Order' },
        { from: 'order_service', to: 'kafka_bus', protocol: 'Pub/Sub', label: 'OrderCreated' },
        { from: 'kafka_bus', to: 'notification_worker', protocol: 'Consumer', label: 'Dispatch Alerts' },
        { from: 'catalog_service', to: 'redis_cache', protocol: 'Cache Lookup', label: 'Fast Read' }
      ],
      insights: {
        strengths: ['Decoupled event-driven architecture via Kafka', 'High-speed session caching with Redis', 'Clean separation of concerns across Go and Python microservices'],
        bottlenecks: ['Kafka partition lag under sudden flash sales', 'Potential database connection pool exhaustion during checkout spikes'],
        recommendations: ['Implement pgBouncer connection pooling for PostgreSQL', 'Add dead-letter queues (DLQ) to Kafka notification consumers']
      }
    },
    usage: {
      provider: 'ModelScope Cloud',
      model: 'Qwen/Qwen3.8-27B',
      total_tokens: 2140,
      duration_ms: 12400,
      reasoning: '1. Ingress Tier: Analyzed Envoy/Kong reverse proxy routing traffic from Next.js.\n2. Microservice Boundaries: Decomposed Go Order Service and Python Catalog Service.\n3. State & Persistence: Mapped PostgreSQL transactional storage alongside Redis session cache.\n4. Event Streaming: Modeled asynchronous Kafka pub/sub pipeline for notification dispatch.'
    }
  }
];

const DIAGRAM_PERSPECTIVES = [
  {
    id: 'overview',
    label: 'System Overview',
    description: 'Multi-tier breakdown of frontend, API gateway, microservices, databases, and third-party APIs.',
    directive: 'Generate a comprehensive end-to-end system architecture overview decomposing presentation tier, API gateway, core backend microservices, data persistence stores, and external integrations.'
  },
  {
    id: 'data_flow',
    label: 'Data Flow & Request Lifecycle',
    description: 'Traces client requests, synchronous API paths, database queries, and caching pathways.',
    directive: 'Focus specifically on the end-to-end data lifecycle: client requests, API routing, synchronous gRPC/REST service calls, database reads/writes, and cache retrieval pathways.'
  },
  {
    id: 'security_auth',
    label: 'Security & Zero-Trust Auth',
    description: 'Authentication (JWT/OAuth2), API gateway token validation, session boundaries, and encryption.',
    directive: 'Focus exclusively on security boundaries: authentication mechanisms (JWT/OAuth2/OIDC), API gateway token validation, session authorization, secrets storage, and protected domain services.'
  },
  {
    id: 'event_driven',
    label: 'Event-Driven & Async Pipelines',
    description: 'Kafka / RabbitMQ event streams, pub/sub topics, worker consumers, and background tasks.',
    directive: 'Emphasize asynchronous messaging patterns: Kafka / RabbitMQ / Redis event streams, pub/sub topics, background worker consumers, event-driven triggers, and failure retry queues.'
  },
  {
    id: 'database_storage',
    label: 'Database & Storage Topology',
    description: 'Relational SQL tables, NoSQL collections, Redis caching, connection pooling, and sharding.',
    directive: 'Focus on data layer topology: primary SQL tables, relational foreign keys, distributed NoSQL stores, Redis session caching, connection pooling, and replication/sharding strategies.'
  },
  {
    id: 'devops_cloud',
    label: 'Cloud & Infrastructure',
    description: 'Docker containers, Kubernetes pods, ingress controllers, load balancers, and CDN caching.',
    directive: 'Structure the diagram around cloud infrastructure: Docker containers, Kubernetes pods, ingress controllers, load balancers, CDN caching, and production cloud deployment tiers.'
  },
  {
    id: 'ai_rag',
    label: 'AI / LLM & RAG Pipeline',
    description: 'Embeddings, vector database retrieval, LLM agents, prompt execution, and multimodal streaming.',
    directive: 'Focus on AI system components: user input orchestrator, embedding models, vector database retrieval, LLM inference agent workflows, tool calls, and streaming output.'
  }
];

export default function App() {
  const [theme, setTheme] = useState(() => {
    return localStorage.getItem('qwenarch_theme') || 'dark';
  });

  const [activeTab, setActiveTab] = useState('github'); // 'github' | 'local' | 'prompt'
  const [githubUrl, setGithubUrl] = useState('');
  const [localPath, setLocalPath] = useState('');
  const [promptText, setPromptText] = useState('');
  const [selectedPerspective, setSelectedPerspective] = useState('overview');
  const [customInstructions, setCustomInstructions] = useState('');
  const [showCustomFocus, setShowCustomFocus] = useState(false);
  const [provider, setProvider] = useState('modelscope'); // 'modelscope' | 'ollama'

  const [loading, setLoading] = useState(false);
  const [currentStep, setCurrentStep] = useState(0); // 1: Ingest, 2: Reasoning, 3: Synthesis, 4: Done
  const [activeTargetName, setActiveTargetName] = useState('');
  
  const [autoSyncMiro, setAutoSyncMiro] = useState(true);
  const [syncing, setSyncing] = useState(false);
  const [error, setError] = useState(null);
  const [syncSuccess, setSyncSuccess] = useState(null);

  const [boardInfo, setBoardInfo] = useState(null);
  const [presets, setPresets] = useState([]);
  const [architecture, setArchitecture] = useState(null);
  const [usage, setUsage] = useState(null);
  const [showReasoning, setShowReasoning] = useState(false);
  const [history, setHistory] = useState([]);
  const [showHistory, setShowHistory] = useState(false);

  useEffect(() => {
    document.documentElement.setAttribute('data-theme', theme);
    localStorage.setItem('qwenarch_theme', theme);
  }, [theme]);

  useEffect(() => {
    fetchBoardInfo();
    fetchSamplePresets();
    loadHistory();
  }, []);

  const toggleTheme = () => {
    setTheme(prev => prev === 'dark' ? 'light' : 'dark');
  };

  const loadHistory = () => {
    try {
      const saved = localStorage.getItem('qwenarch_history');
      if (saved) {
        setHistory(JSON.parse(saved));
      } else {
        setHistory(DEFAULT_PRESETS_DATA);
      }
    } catch (e) {
      setHistory(DEFAULT_PRESETS_DATA);
    }
  };

  const saveToHistory = (newRun) => {
    const updated = [newRun, ...history.filter(h => h.id !== newRun.id)].slice(0, 8);
    setHistory(updated);
    try {
      localStorage.setItem('qwenarch_history', JSON.stringify(updated));
    } catch (e) {}
  };

  const fetchBoardInfo = async () => {
    try {
      const res = await fetch('/api/board-info');
      const data = await res.json();
      if (data.success) {
        setBoardInfo(data);
      }
    } catch (err) {
      console.error('Failed to fetch board info:', err);
    }
  };

  const fetchSamplePresets = async () => {
    try {
      const res = await fetch('/api/sample-repos');
      const data = await res.json();
      setPresets(data);
      if (data.length > 0 && !promptText) {
        setPromptText(data[0].source.trim());
      }
    } catch (err) {
      console.error('Failed to fetch sample repos:', err);
    }
  };

  const handleSelectPreset = (preset) => {
    setActiveTab('prompt');
    setPromptText(preset.source.trim());
    setArchitecture(null);
    setSyncSuccess(null);
    setUsage(null);
  };

  const handleLoadPastRun = (run) => {
    setArchitecture(run.architecture);
    setUsage(run.usage);
    if (run.custom_instructions) {
      setCustomInstructions(run.custom_instructions);
      setShowCustomFocus(true);
    }
    setError(null);
    setSyncSuccess(null);
    setShowReasoning(false);
    setLoading(false);
  };

  const executeMiroSync = async (archToSync) => {
    const targetArch = archToSync || architecture;
    if (!targetArch) return;

    setSyncing(true);
    setSyncSuccess(null);
    setError(null);

    try {
      const res = await fetch('/api/sync-miro', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          architecture: targetArch,
          offset_x: -250,
          offset_y: -120
        })
      });

      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || 'Failed to sync to Miro');

      setSyncSuccess(data.result);
      confetti({
        particleCount: 80,
        spread: 70,
        origin: { y: 0.5 }
      });
    } catch (err) {
      setError(err.message || 'Miro API synchronization failed.');
    } finally {
      setSyncing(false);
    }
  };

  const handleAnalyze = async (isPullUpdate = false) => {
    let source_type = activeTab;
    let source_value = '';

    if (activeTab === 'github') source_value = githubUrl;
    else if (activeTab === 'local') source_value = localPath;
    else source_value = promptText;

    if (!source_value.trim()) {
      setError('Please provide a repository URL, local path, or architecture description.');
      return;
    }

    setArchitecture(null);
    setSyncSuccess(null);
    setError(null);
    setLoading(true);
    setCurrentStep(1); // 1. Ingesting
    setShowReasoning(true);

    const displayName = activeTab === 'github' 
      ? source_value.split('/').pop() || source_value 
      : activeTab === 'local' ? source_value.split('/').pop() || source_value : 'Custom System Spec';
    setActiveTargetName(displayName);

    try {
      setUsage({
        model: provider === 'ollama' ? 'Local Qwen 7B' : 'Qwen 3.8 27B',
        provider: provider === 'ollama' ? 'Local Ollama' : 'ModelScope Cloud',
        total_tokens: 'Streaming...',
        duration_ms: 0,
        reasoning: isPullUpdate 
          ? 'Pulling latest code changes & analyzing incremental diffs...\n'
          : `Ingesting ${displayName}... initiating real-time reasoning stream...\n`
      });

      setCurrentStep(2); // 2. Reasoning

      const res = await fetch('/api/analyze-stream', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          source_type,
          source_value,
          provider,
          perspective: selectedPerspective,
          custom_instructions: customInstructions
        })
      });

      if (!res.ok) {
        const errData = await res.json();
        throw new Error(errData.detail || 'Analysis stream failed');
      }

      const reader = res.body.getReader();
      const decoder = new TextDecoder();
      let buffer = '';
      let streamedReasoning = '';
      let completedSuccessfully = false;

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split('\n');
        // Keep the trailing incomplete line in buffer
        buffer = lines.pop() || '';

        for (const line of lines) {
          const trimmed = line.trim();
          if (!trimmed || !trimmed.startsWith('data: ')) continue;
          const jsonPayload = trimmed.slice(6).trim();
          if (!jsonPayload) continue;

          try {
            const data = JSON.parse(jsonPayload);
            if (data.type === 'reasoning') {
              setCurrentStep(2); // 2. Reasoning
              streamedReasoning += data.chunk;
              setUsage(prev => ({
                ...prev,
                reasoning: streamedReasoning
              }));
            } else if (data.type === 'content') {
              setCurrentStep(3); // 3. Synthesizing diagram
              if (!streamedReasoning || streamedReasoning.length < 50) {
                streamedReasoning += data.chunk;
                setUsage(prev => ({
                  ...prev,
                  reasoning: streamedReasoning
                }));
              }
            } else if (data.type === 'complete') {
              completedSuccessfully = true;
              setCurrentStep(4); // 4. Done
              setArchitecture(data.architecture);
              setUsage(data.usage);
              setShowReasoning(false);

              // Trigger confetti celebration
              confetti({
                particleCount: 50,
                spread: 60,
                origin: { y: 0.8 }
              });

              // Save to history
              saveToHistory({
                id: `run-${Date.now()}`,
                title: data.architecture.system_title || displayName,
                time: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
                source_type,
                custom_instructions: customInstructions,
                architecture: data.architecture,
                usage: data.usage
              });

              // Auto-sync to Miro if toggle is active!
              if (autoSyncMiro) {
                executeMiroSync(data.architecture);
              }
            } else if (data.type === 'error') {
              throw new Error(data.error);
            }
          } catch (pErr) {
            console.warn('SSE chunk buffering issue:', pErr);
          }
        }
      }

      // Check remaining buffer if any
      if (buffer.trim().startsWith('data: ')) {
        try {
          const data = JSON.parse(buffer.trim().slice(6).trim());
          if (data.type === 'complete') {
            completedSuccessfully = true;
            setCurrentStep(4);
            setArchitecture(data.architecture);
            setUsage(data.usage);
            setShowReasoning(false);
            if (autoSyncMiro) executeMiroSync(data.architecture);
          }
        } catch (e) {}
      }

      // If stream ended without complete payload, fetch via standard POST
      if (!completedSuccessfully) {
        console.log('Stream ended before complete payload. Fetching direct analysis...');
        setCurrentStep(3);
        const directRes = await fetch('/api/analyze', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            source_type,
            source_value,
            provider,
            perspective: selectedPerspective,
            custom_instructions: customInstructions
          })
        });
        if (directRes.ok) {
          const directData = await directRes.json();
          if (directData.success && directData.architecture) {
            setArchitecture(directData.architecture);
            setUsage(directData.usage || {});
            setShowReasoning(false);
            setCurrentStep(4);
            if (autoSyncMiro) executeMiroSync(directData.architecture);
          }
        }
      }
    } catch (err) {
      setError(err.message || 'An error occurred during codebase analysis.');
    } finally {
      setLoading(false);
      setCurrentStep(0);
    }
  };

  return (
    <div className="app-container">
      {/* Navbar */}
      <header className="navbar">
        <div className="brand-badge">
          <div className="brand-logo-qwen">Q</div>
          <span className="brand-cross">/</span>
          <div className="brand-logo-miro">M</div>
          <div className="brand-info">
            <h1>QwenArch</h1>
            <p>Codebase to Miro Architecture Engine</p>
          </div>
        </div>

        <div className="nav-actions">
          {/* Pitch Deck / Presentation Slides */}
          <a
            href="/slides.html"
            target="_blank"
            rel="noopener noreferrer"
            className="deck-link-btn"
            title="Open Interactive Pitch Deck Presentation"
          >
            <Presentation size={15} />
            <span>Pitch Deck</span>
          </a>

          {/* Light / Dark Mode Toggle */}
          <button 
            className="theme-toggle-btn"
            onClick={toggleTheme}
            title={`Switch to ${theme === 'dark' ? 'Light' : 'Dark'} Mode`}
            aria-label="Toggle Theme"
          >
            {theme === 'dark' ? <Sun size={16} /> : <Moon size={16} />}
          </button>

          {boardInfo && (
            <a
              href={boardInfo.view_link}
              target="_blank"
              rel="noopener noreferrer"
              className="board-link-btn"
            >
              <ExternalLink size={14} />
              <span>Open Miro Board ({boardInfo.team || 'NeuCorelytix'})</span>
            </a>
          )}
          <div className="header-status-badge">
            <span className="status-dot"></span>
            <span>Miro Live</span>
          </div>
        </div>
      </header>

      {/* Main Grid */}
      <main className="main-grid">
        {/* Left Column: Controls & Input */}
        <section className="card">
          <div className="card-header">
            <div className="card-title">
              <Cpu size={17} />
              <span>1. Ingest Codebase</span>
            </div>
            
            {/* Model Selector */}
            <select
              value={provider}
              onChange={(e) => setProvider(e.target.value)}
              className="model-select"
            >
              <option value="modelscope">Qwen 3.8 27B (Cloud)</option>
              <option value="ollama">Local Qwen-Coder 7B</option>
            </select>
          </div>

          {/* Source Tabs */}
          <div className="tabs-container">
            <button
              className={`tab-btn ${activeTab === 'github' ? 'active' : ''}`}
              onClick={() => { setActiveTab('github'); setArchitecture(null); }}
            >
              <GitBranch size={14} />
              <span>GitHub Repo</span>
            </button>
            <button
              className={`tab-btn ${activeTab === 'local' ? 'active' : ''}`}
              onClick={() => { setActiveTab('local'); setArchitecture(null); }}
            >
              <Folder size={14} />
              <span>Local Dir</span>
            </button>
            <button
              className={`tab-btn ${activeTab === 'prompt' ? 'active' : ''}`}
              onClick={() => { setActiveTab('prompt'); setArchitecture(null); }}
            >
              <FileCode size={14} />
              <span>Spec / Prompt</span>
            </button>
          </div>

          {/* Tab Content */}
          {activeTab === 'github' && (
            <div className="input-group">
              <label className="input-label">
                <span>GitHub Repository URL</span>
                <span style={{ color: 'var(--text-secondary)' }}>Public or Cloned</span>
              </label>
              <input
                type="text"
                className="text-input"
                placeholder="https://github.com/username/repository"
                value={githubUrl}
                onChange={(e) => setGithubUrl(e.target.value)}
              />
            </div>
          )}

          {activeTab === 'local' && (
            <div className="input-group">
              <label className="input-label">
                <span>Local Directory Absolute Path</span>
              </label>
              <input
                type="text"
                className="text-input"
                placeholder="/path/to/your/project"
                value={localPath}
                onChange={(e) => setLocalPath(e.target.value)}
              />
            </div>
          )}

          {activeTab === 'prompt' && (
            <div className="input-group">
              <label className="input-label">
                <span>Architecture Specification / Services List</span>
              </label>
              <textarea
                className="text-area"
                rows={6}
                placeholder="Paste code structure, services list, or architectural prompt..."
                value={promptText}
                onChange={(e) => setPromptText(e.target.value)}
              />
            </div>
          )}

          {/* Diagram Perspective & Focus Directives */}
          <div className="custom-focus-section">
            <div className="input-group">
              <label className="input-label">
                <span>Diagram Perspective & Focus Mode</span>
                <span style={{ color: 'var(--text-secondary)' }}>Predefined Use-Cases</span>
              </label>
              <select
                value={selectedPerspective}
                onChange={(e) => {
                  const pId = e.target.value;
                  setSelectedPerspective(pId);
                  const matched = DIAGRAM_PERSPECTIVES.find(p => p.id === pId);
                  if (matched) {
                    setCustomInstructions(matched.directive);
                    setShowCustomFocus(true);
                  }
                }}
                className="perspective-select"
              >
                {DIAGRAM_PERSPECTIVES.map(p => (
                  <option key={p.id} value={p.id}>
                    {p.label}
                  </option>
                ))}
              </select>
            </div>

            <div 
              className="custom-focus-header" 
              onClick={() => setShowCustomFocus(!showCustomFocus)}
            >
              <div className="custom-focus-title">
                <Sliders size={13} />
                <span>Custom Architecture Directives</span>
              </div>
              <span className="optional-tag">
                {showCustomFocus ? 'Hide Details' : (customInstructions.trim() ? 'Active Directives' : '+ Customize')}
              </span>
            </div>

            {(showCustomFocus || customInstructions.trim()) && (
              <div className="custom-focus-body">
                <textarea
                  className="text-area custom-focus-textarea"
                  rows={3}
                  placeholder="What specific components or flows should Qwen prioritize? e.g., Detail auth & JWT token flow, highlight Kafka event streaming, or focus on PostgreSQL schema and Redis caching..."
                  value={customInstructions}
                  onChange={(e) => setCustomInstructions(e.target.value)}
                />
                
                {/* Quick Focus Preset Chips */}
                <div className="quick-focus-chips">
                  {[
                    'JWT Auth & RBAC',
                    'Kafka Event Bus',
                    'Postgres & Redis Caching',
                    'Microservice Domain Boundaries',
                    'Envoy Ingress Gateway',
                    'Kubernetes & Docker',
                    'Vector DB & RAG'
                  ].map((chip, cIdx) => (
                    <button
                      key={cIdx}
                      type="button"
                      className={`quick-focus-chip ${customInstructions.includes(chip) ? 'active' : ''}`}
                      onClick={() => {
                        if (customInstructions.includes(chip)) {
                          setCustomInstructions(customInstructions.replace(chip, '').replace(/,\s*,/g, ',').replace(/^,\s*|,\s*$/g, '').trim());
                        } else {
                          setCustomInstructions(prev => prev.trim() ? `${prev.trim()}, ${chip}` : chip);
                        }
                      }}
                    >
                      {chip}
                    </button>
                  ))}
                </div>
              </div>
            )}
          </div>

          {/* Quick Demo Presets */}
          <div className="presets-group">
            <label className="input-label">
              <span>Quick Demo Architecture Presets</span>
            </label>
            {presets.map((preset, idx) => (
              <div
                key={idx}
                className="preset-card"
                onClick={() => handleSelectPreset(preset)}
              >
                <h4>{preset.name}</h4>
                <p>{preset.description}</p>
              </div>
            ))}
          </div>

          {/* Previous Runs / History Accordion */}
          {history.length > 0 && (
            <div className="history-section">
              <div className="history-header" onClick={() => setShowHistory(!showHistory)}>
                <span className="history-title">
                  <History size={14} />
                  <span>Saved Runs & Demo History ({history.length})</span>
                </span>
                {showHistory ? <ChevronUp size={14} /> : <ChevronDown size={14} />}
              </div>

              {showHistory && (
                <div className="history-items-list">
                  {history.map(item => (
                    <div
                      key={item.id}
                      className="history-item-chip"
                      onClick={() => handleLoadPastRun(item)}
                    >
                      <span className="history-item-name">{item.title}</span>
                      <span className="history-item-time">{item.time}</span>
                    </div>
                  ))}
                </div>
              )}
            </div>
          )}

          {/* Primary Action Button */}
          <button
            className="btn-primary"
            onClick={() => handleAnalyze(false)}
            disabled={loading}
          >
            {loading ? (
              <>
                <RefreshCw size={17} className="spin" />
                <span>Qwen Analyzing Architecture...</span>
              </>
            ) : (
              <>
                <Sparkles size={17} />
                <span>Analyze with Qwen-Coder</span>
              </>
            )}
          </button>

          {/* Strictly Contained Error Banner */}
          {error && (
            <div className="error-banner">
              <AlertTriangle size={16} style={{ flexShrink: 0, marginTop: '2px' }} />
              <span className="error-text">{error}</span>
              <button className="error-close-btn" onClick={() => setError(null)}>
                <X size={14} />
              </button>
            </div>
          )}
        </section>

        {/* Right Column: Output & Miro Sync */}
        <section className="card">
          <div className="canvas-preview-header">
            <div className="canvas-title-group">
              <div className="card-title">
                <Layers size={18} />
                <span>2. Visual Architecture Canvas</span>
              </div>
              {architecture && (
                <div className="architecture-meta-badge">
                  <span className="system-title">{architecture.system_title}</span>
                  <span className="style-pill">{architecture.architecture_style}</span>
                </div>
              )}
            </div>

            {/* Canvas Actions */}
            <div className="canvas-actions">
              {/* Auto-Sync Toggle */}
              <div 
                className={`auto-sync-toggle ${autoSyncMiro ? 'active' : ''}`}
                onClick={() => setAutoSyncMiro(!autoSyncMiro)}
                title="Automatically push generated diagram to Miro upon completion"
              >
                <Radio size={12} />
                <span>Auto-Sync Miro: <b>{autoSyncMiro ? 'ON' : 'OFF'}</b></span>
              </div>

              {architecture && (activeTab === 'github' || activeTab === 'local') && (
                <button
                  className="btn-pull-refresh"
                  onClick={() => handleAnalyze(true)}
                  disabled={loading}
                  title="Pull latest git commits/files and update architecture"
                >
                  <RotateCcw size={14} />
                  <span>Pull Code & Update</span>
                </button>
              )}

              {architecture && (
                <button
                  className="btn-primary btn-sync-miro"
                  onClick={() => executeMiroSync()}
                  disabled={syncing}
                >
                  {syncing ? (
                    <>
                      <RefreshCw size={15} className="spin" />
                      <span>Syncing Miro...</span>
                    </>
                  ) : (
                    <>
                      <Share2 size={15} />
                      <span>Sync Directly to Miro</span>
                    </>
                  )}
                </button>
              )}
            </div>
          </div>

          {/* Active Generation Progress Pipeline */}
          {loading && (
            <div className="progress-pipeline">
              <div className="pipeline-header">
                <span>Model Execution Progress</span>
                <span style={{ color: 'var(--text-secondary)', fontSize: '0.74rem' }}>
                  {currentStep === 1 && `Ingesting ${activeTargetName}...`}
                  {currentStep === 2 && 'Qwen reasoning through architecture...'}
                  {currentStep === 3 && 'Synthesizing layers, nodes and protocol links...'}
                  {currentStep === 4 && 'Rendering visual diagram and syncing to Miro...'}
                </span>
              </div>
              <div className="pipeline-steps">
                <div className={`pipeline-step ${currentStep >= 1 ? (currentStep === 1 ? 'active' : 'completed') : ''}`}>
                  <span>1. Ingestion</span>
                </div>
                <div className={`pipeline-step ${currentStep >= 2 ? (currentStep === 2 ? 'active' : 'completed') : ''}`}>
                  <span>2. Reasoning</span>
                </div>
                <div className={`pipeline-step ${currentStep >= 3 ? (currentStep === 3 ? 'active' : 'completed') : ''}`}>
                  <span>3. Synthesis</span>
                </div>
                <div className={`pipeline-step ${currentStep >= 4 ? 'completed' : ''}`}>
                  <span>4. Miro Sync</span>
                </div>
              </div>
            </div>
          )}

          {/* Success Banner */}
          {syncSuccess && (
            <div className="success-banner">
              <div style={{ display: 'flex', alignItems: 'center', gap: '0.6rem' }}>
                <CheckCircle2 size={16} />
                <span>
                  <b>Successfully Rendered on Miro Canvas!</b> ({syncSuccess.created_nodes} nodes & {syncSuccess.created_connectors} connectors)
                </span>
              </div>
              <a
                href={syncSuccess.board_url}
                target="_blank"
                rel="noopener noreferrer"
                className="view-miro-btn"
              >
                <span>Open in Miro</span>
                <ArrowRight size={14} />
              </a>
            </div>
          )}

          {/* Token Metrics Bar */}
          {usage && (
            <div className="metrics-bar">
              <div className="metric-item provider">
                <Zap size={14} />
                <span>{usage.provider || 'ModelScope'}</span>
                <span className="model-sub">({usage.model})</span>
              </div>
              <span className="divider">•</span>
              <div className="metric-item tokens">
                <Coins size={13} />
                <span><b>{typeof usage.total_tokens === 'number' ? usage.total_tokens.toLocaleString() : usage.total_tokens}</b> tokens</span>
              </div>
              <span className="divider">•</span>
              <div className="metric-item time">
                <Clock size={13} />
                <span><b>{((usage.duration_ms || 0) / 1000).toFixed(1)}s</b></span>
              </div>

              {usage.reasoning && (
                <button
                  className={`reasoning-toggle-btn ${showReasoning ? 'active' : ''}`}
                  onClick={() => setShowReasoning(!showReasoning)}
                >
                  <Terminal size={13} />
                  <span>{showReasoning ? 'Hide Reasoning' : 'View Chain-of-Thought'}</span>
                  {showReasoning ? <ChevronUp size={14} /> : <ChevronDown size={14} />}
                </button>
              )}
            </div>
          )}

          {/* Collapsible Chain-of-Thought Reasoning Box */}
          {showReasoning && usage && usage.reasoning && (
            <div className="reasoning-container">
              <div className="reasoning-header">
                <div style={{ display: 'flex', alignItems: 'center', gap: '0.4rem' }}>
                  <Terminal size={14} />
                  <span>Qwen Architectural Reasoning Chain</span>
                </div>
                {loading && <span className="streaming-badge">Streaming...</span>}
              </div>
              <div className="reasoning-body">
                {usage.reasoning}
              </div>
            </div>
          )}

          {/* Tech Stack Pills */}
          {architecture && architecture.tech_stack && (
            <div className="tech-stack-row">
              {architecture.tech_stack.map((tech, i) => (
                <span key={i} className="tech-tag">
                  {tech}
                </span>
              ))}
            </div>
          )}

          {/* Architecture Graph Render or Live Generating State */}
          {architecture ? (
            <ArchitectureGraph architecture={architecture} />
          ) : (
            <div className="empty-state-card">
              <div className={`empty-icon-circle ${loading ? 'spinning' : ''}`}>
                {loading ? <RefreshCw size={26} className="spin" /> : <Layers size={28} />}
              </div>
              <div>
                <h3>{loading ? `Synthesizing Architecture for ${activeTargetName}...` : 'No Architecture Generated Yet'}</h3>
                <p>
                  {loading 
                    ? 'Qwen is decomposing modules, databases, and message brokers into visual layers.'
                    : 'Select a repository, local codebase, or preset on the left, then click "Analyze with Qwen-Coder".'}
                </p>
              </div>
            </div>
          )}
        </section>
      </main>
    </div>
  );
}
