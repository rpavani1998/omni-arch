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
  Presentation,
  Settings,
  Key,
  ShieldCheck,
  Eye,
  EyeOff,
  Save,
  Activity,
  Box,
  Database
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
    label: '1. High-Level Architecture (HLD / C4 Component)',
    badge: 'System Design',
    description: 'Presentation tier, API gateway ingress, core microservices, data persistence stores, and external cloud integrations.',
    directive: 'Decompose the complete architecture into presentation clients, API gateway ingress, core application microservices, data persistence stores, and external third-party integrations with clear boundary responsibilities.'
  },
  {
    id: 'data_flow',
    label: '2. Request Lifecycle & API Execution Flow',
    badge: 'API & Execution',
    description: 'Traces client requests, routing, auth validation, internal RPC calls, database queries, and cache lookups.',
    directive: 'Trace end-to-end request lifecycle from client action through gateway routing, authentication/authorization validation, internal service-to-service calls, database reads/writes, cache lookups, and response return.'
  },
  {
    id: 'database_storage',
    label: '3. Data Model & Schema Topology (LLD / ERD)',
    badge: 'Data Layer',
    description: 'Relational SQL tables, NoSQL collections, foreign keys, transaction boundaries, and Redis caching layers.',
    directive: 'Focus on data persistence architecture: core entity schemas, primary database tables/collections, foreign key relations, transactional boundaries, Redis caching layers, and connection pooling.'
  },
  {
    id: 'devops_pipeline',
    label: '4. CI/CD & DevOps Deployment Pipeline',
    badge: 'DevOps & SRE',
    description: 'Git triggers, automated testing, Docker build stages, artifact registry, and cloud environment promotion.',
    directive: 'Map the continuous integration and deployment lifecycle: Git repository triggers, automated lint/test stages, Docker containerization, artifact registry packaging, cloud infrastructure deployment, and environment promotion.'
  },
  {
    id: 'security_auth',
    label: '5. Security, Auth & Zero-Trust Boundary',
    badge: 'Security',
    description: 'OAuth2/OIDC/JWT flows, token verification, API gateway rate limiting, RBAC permissions, and secret vault storage.',
    directive: 'Analyze security and trust boundaries: public vs private subnet zones, OAuth2/OIDC/JWT authentication flows, API gateway rate limiting, RBAC permission checks, secret management, and secure communication protocols.'
  },
  {
    id: 'async_workers',
    label: '6. Async Task Queues & Worker Pipelines',
    badge: 'Background Jobs',
    description: 'Task queues, worker pools, cron schedulers, webhook ingestion, pub/sub topics, and retry dead-letter queues.',
    directive: 'Highlight asynchronous background processing: task queue ingestion, distributed worker pool execution, cron schedulers, webhook consumers, pub/sub messaging channels, and retry / dead-letter queues.'
  },
  {
    id: 'observability',
    label: '7. Observability, Distributed Tracing & SRE',
    badge: 'Monitoring',
    description: 'OpenTelemetry trace propagation, Prometheus metrics, structured logging pipelines, and automated alerts.',
    directive: 'Structure the observability and site reliability architecture: distributed trace propagation, Prometheus metrics exporters, structured logging pipelines, health check probes, and automated alerting integrations.'
  },
  {
    id: 'ai_rag',
    label: '8. AI / LLM & RAG Agentic Pipeline',
    badge: 'AI & Agents',
    description: 'Prompt orchestration, document chunking, vector DB retrieval, LLM reasoning loop, and streaming output.',
    directive: 'Deconstruct the AI / RAG architecture: user prompt orchestrator, document chunking & vector database retrieval, LLM inference agent workflows, tool calling integrations, memory store, and streaming response output.'
  }
];

const SDLC_ADDON_PROMPTS = [
  {
    id: 'addon_caching',
    label: 'Multi-Tier Caching & CDN',
    icon: 'zap',
    prompt: 'Include multi-level caching strategies (Redis in-memory caching, CDN edge caching, and query result caches) with TTL policies.'
  },
  {
    id: 'addon_security',
    label: 'Strict RBAC & Zero-Trust',
    icon: 'shield',
    prompt: 'Enforce strict RBAC role authorization, granular API permission scopes, encrypted tokens, and least-privilege security boundaries.'
  },
  {
    id: 'addon_resilience',
    label: 'Circuit Breaker & Retries',
    icon: 'refresh',
    prompt: 'Detail failure resilience: circuit breakers, exponential backoff retries, fallback responses, and dead-letter queues (DLQ).'
  },
  {
    id: 'addon_observability',
    label: 'OpenTelemetry & Metrics',
    icon: 'activity',
    prompt: 'Include OpenTelemetry distributed trace IDs, Prometheus metrics collection, and centralized structured log aggregation.'
  },
  {
    id: 'addon_testing',
    label: 'Test Mocks & E2E Points',
    icon: 'test',
    prompt: 'Specify automated testing boundaries: unit test mock interfaces, integration test fixtures, and end-to-end API assertion checkpoints.'
  },
  {
    id: 'addon_docker',
    label: 'Containers & Port Mappings',
    icon: 'box',
    prompt: 'Detail Docker container boundaries, exposed network port bindings, environment variable injection, and volume mounts.'
  },
  {
    id: 'addon_multitenancy',
    label: 'Multi-Tenant Data Isolation',
    icon: 'layers',
    prompt: 'Highlight multi-tenant isolation: tenant ID propagation, row-level security (RLS), and isolated database schema boundaries.'
  },
  {
    id: 'addon_transactions',
    label: 'ACID & Read/Write Splitting',
    icon: 'database',
    prompt: 'Detail transactional consistency: ACID transaction scopes, primary write vs read-replica pools, and database connection pooling.'
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

  const [savedCustomPrompts, setSavedCustomPrompts] = useState(() => {
    try {
      const saved = localStorage.getItem('qwenarch_saved_prompts');
      return saved ? JSON.parse(saved) : [];
    } catch (e) {
      return [];
    }
  });

  const handleSaveCurrentPrompt = () => {
    if (!customInstructions.trim()) return;
    const promptName = prompt('Enter a name for this custom architecture directive preset:');
    if (!promptName || !promptName.trim()) return;
    const newEntry = {
      id: 'custom-' + Date.now(),
      name: promptName.trim(),
      prompt: customInstructions.trim(),
      perspective: selectedPerspective
    };
    const updated = [newEntry, ...savedCustomPrompts.filter(p => p.name !== newEntry.name)].slice(0, 15);
    setSavedCustomPrompts(updated);
    try {
      localStorage.setItem('qwenarch_saved_prompts', JSON.stringify(updated));
    } catch (e) {}
  };

  const handleDeleteSavedPrompt = (id, e) => {
    e.stopPropagation();
    const updated = savedCustomPrompts.filter(p => p.id !== id);
    setSavedCustomPrompts(updated);
    try {
      localStorage.setItem('qwenarch_saved_prompts', JSON.stringify(updated));
    } catch (e) {}
  };

  const [customSettings, setCustomSettings] = useState(() => {
    try {
      const saved = localStorage.getItem('qwenarch_custom_settings');
      return saved ? JSON.parse(saved) : {
        miroAccessToken: '',
        miroBoardId: '',
        aiProvider: 'modelscope',
        aiApiKey: '',
        aiBaseUrl: 'https://api-inference.modelscope.ai/v1',
        aiModelName: 'Qwen/Qwen3.8-27B'
      };
    } catch (e) {
      return {
        miroAccessToken: '',
        miroBoardId: '',
        aiProvider: 'modelscope',
        aiApiKey: '',
        aiBaseUrl: 'https://api-inference.modelscope.ai/v1',
        aiModelName: 'Qwen/Qwen3.8-27B'
      };
    }
  });

  const [showSettingsModal, setShowSettingsModal] = useState(false);
  const [showApiKey, setShowApiKey] = useState(false);
  const [showMiroToken, setShowMiroToken] = useState(false);
  const [testingMiro, setTestingMiro] = useState(false);
  const [miroTestResult, setMiroTestResult] = useState(null);

  useEffect(() => {
    document.documentElement.setAttribute('data-theme', theme);
    localStorage.setItem('qwenarch_theme', theme);
  }, [theme]);

  useEffect(() => {
    fetchBoardInfo();
    fetchSamplePresets();
    loadHistory();

    // Initialize Miro Web SDK v2 if running inside an active Miro Canvas
    const initMiroSDK = async () => {
      try {
        if (typeof window !== 'undefined' && window.miro && window.miro.board) {
          // Register toolbar panel opener if icon is clicked
          if (window.miro.board.ui && window.miro.board.ui.on) {
            window.miro.board.ui.on('icon:click', async () => {
              try {
                await window.miro.board.ui.openPanel({ url: 'index.html' });
              } catch (err) {
                console.debug('Miro panel open error:', err);
              }
            });
          }

          const boardInfoRes = await window.miro.board.getInfo();
          if (boardInfoRes && boardInfoRes.id) {
            setCustomSettings(prev => {
              const updated = {
                ...prev,
                miroBoardId: prev.miroBoardId || boardInfoRes.id
              };
              try {
                localStorage.setItem('omniarch_custom_settings', JSON.stringify(updated));
              } catch (e) {}
              return updated;
            });
            setBoardInfo(prev => ({
              ...(prev || {}),
              id: boardInfoRes.id,
              name: boardInfoRes.title || 'Active Miro Board',
              connected: true,
              in_canvas: true
            }));
          }
        }
      } catch (err) {
        console.debug('Miro Web SDK detection skipped:', err);
      }
    };
    initMiroSDK();
  }, []);

  const toggleTheme = () => {
    setTheme(prev => prev === 'dark' ? 'light' : 'dark');
  };

  const handleSaveSettings = (newSettings) => {
    setCustomSettings(newSettings);
    try {
      localStorage.setItem('qwenarch_custom_settings', JSON.stringify(newSettings));
    } catch (e) {}
    fetchBoardInfo(newSettings.miroAccessToken, newSettings.miroBoardId);
  };

  const handleResetSettings = () => {
    const defaults = {
      miroAccessToken: '',
      miroBoardId: '',
      aiProvider: 'modelscope',
      aiApiKey: '',
      aiBaseUrl: 'https://api-inference.modelscope.ai/v1',
      aiModelName: 'Qwen/Qwen3.8-27B'
    };
    setCustomSettings(defaults);
    try {
      localStorage.removeItem('qwenarch_custom_settings');
    } catch (e) {}
    setMiroTestResult(null);
    fetchBoardInfo('', '');
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

  const fetchBoardInfo = async (customToken, customBoard) => {
    try {
      const token = customToken !== undefined ? customToken : customSettings.miroAccessToken;
      const board = customBoard !== undefined ? customBoard : customSettings.miroBoardId;
      
      const hasCustom = Boolean(token || board);
      const res = await fetch('/api/board-info', {
        method: hasCustom ? 'POST' : 'GET',
        headers: { 'Content-Type': 'application/json' },
        body: hasCustom ? JSON.stringify({ access_token: token || undefined, board_id: board || undefined }) : undefined
      });
      const data = await res.json();
      if (data.success) {
        setBoardInfo(data);
        return { success: true, data };
      } else {
        return { success: false, error: data.error };
      }
    } catch (err) {
      console.error('Failed to fetch board info:', err);
      return { success: false, error: err.message };
    }
  };

  const handleTestMiroConnection = async () => {
    setTestingMiro(true);
    setMiroTestResult(null);
    try {
      const res = await fetchBoardInfo(customSettings.miroAccessToken, customSettings.miroBoardId);
      if (res.success) {
        setMiroTestResult({
          success: true,
          message: `Connected to "${res.data.name}" (${res.data.team || 'Personal'})`
        });
      } else {
        setMiroTestResult({
          success: false,
          message: res.error || 'Connection failed. Verify access token and board ID permissions.'
        });
      }
    } catch (e) {
      setMiroTestResult({
        success: false,
        message: e.message
      });
    } finally {
      setTestingMiro(false);
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
          perspective: selectedPerspective,
          offset_x: -300,
          offset_y: -150,
          access_token: customSettings.miroAccessToken || undefined,
          board_id: customSettings.miroBoardId || undefined
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

      const effectiveProvider = customSettings.aiProvider || provider;
      const res = await fetch('/api/analyze-stream', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          source_type,
          source_value,
          provider: effectiveProvider,
          api_key: customSettings.aiApiKey || undefined,
          base_url: customSettings.aiBaseUrl || undefined,
          model_name: customSettings.aiModelName || undefined,
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
            provider: effectiveProvider,
            api_key: customSettings.aiApiKey || undefined,
            base_url: customSettings.aiBaseUrl || undefined,
            model_name: customSettings.aiModelName || undefined,
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
          <div className="brand-logo-qwen">O</div>
          <span className="brand-cross">/</span>
          <div className="brand-logo-miro">M</div>
          <div className="brand-info">
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.45rem' }}>
              <h1>OmniArch</h1>
              <span className="default-model-badge" title="Universal Multi-Model Architecture Engine">Multi-Model</span>
            </div>
            <p>Universal Codebase to Miro Architecture Engine</p>
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

          {/* Custom Credentials & Settings Modal Trigger */}
          <button
            className="settings-nav-btn"
            onClick={() => setShowSettingsModal(true)}
            title="Configure Custom Credentials (Miro, ModelScope, Ollama, OpenAI, DeepSeek, etc.)"
          >
            <Settings size={15} />
            <span>Settings & Keys</span>
            {(customSettings.miroAccessToken || customSettings.aiApiKey || customSettings.aiProvider === 'custom') && (
              <span className="settings-active-dot" title="Custom credentials active" />
            )}
          </button>

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
              value={customSettings.aiProvider === 'custom' ? 'custom' : provider}
              onChange={(e) => {
                if (e.target.value === 'custom') {
                  setShowSettingsModal(true);
                } else {
                  setProvider(e.target.value);
                  setCustomSettings({
                    ...customSettings,
                    aiProvider: e.target.value
                  });
                }
              }}
              className="model-select"
              title="Select inference model: Qwen, DeepSeek, OpenAI, Claude, or Local Ollama"
            >
              <option value="modelscope">Qwen 3.8 27B (Default Cloud)</option>
              <option value="ollama">Local Qwen / DeepSeek (Ollama)</option>
              {customSettings.aiProvider === 'custom' && (
                <option value="custom">Custom: {customSettings.aiModelName || 'Custom Model'}</option>
              )}
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

          {/* Diagram Perspective & SDLC Use-Cases */}
          <div className="custom-focus-section">
            <div className="input-group">
              <label className="input-label">
                <span>Diagram Perspective & SDLC Use-Case</span>
                <span style={{ color: 'var(--text-secondary)' }}>8 Standard SDLC Tiers</span>
              </label>
              <select
                value={selectedPerspective}
                onChange={(e) => setSelectedPerspective(e.target.value)}
                className="perspective-select"
              >
                {DIAGRAM_PERSPECTIVES.map(p => (
                  <option key={p.id} value={p.id}>
                    {p.label}
                  </option>
                ))}
              </select>
            </div>

            {/* Default Diagram Goal / Base Prompt Preview */}
            {(() => {
              const activeP = DIAGRAM_PERSPECTIVES.find(p => p.id === selectedPerspective) || DIAGRAM_PERSPECTIVES[0];
              return (
                <div className="default-directive-preview">
                  <div className="default-directive-header">
                    <Target size={13} />
                    <span>Default Diagram Goal ({activeP.badge}):</span>
                  </div>
                  <p className="default-directive-text">{activeP.directive}</p>
                </div>
              );
            })()}

            {/* Extra Comments & Add-On Instructions */}
            <div 
              className="custom-focus-header" 
              onClick={() => setShowCustomFocus(!showCustomFocus)}
            >
              <div className="custom-focus-title">
                <Sliders size={13} />
                <span>Add-On Instructions & Extra Comments</span>
              </div>
              <span className="optional-tag">
                {showCustomFocus ? 'Collapse' : (customInstructions.trim() ? `${customInstructions.length} chars added` : '+ Add Extra Instructions')}
              </span>
            </div>

            {(showCustomFocus || customInstructions.trim()) && (
              <div className="custom-focus-body">
                <textarea
                  className="text-area custom-focus-textarea"
                  rows={3}
                  placeholder="Add extra instructions or comments (e.g., Highlight Stripe billing webhooks, migrate auth to OAuth2, detail Redis cache TTL, or specify team constraints)..."
                  value={customInstructions}
                  onChange={(e) => setCustomInstructions(e.target.value)}
                />
                
                {/* SDLC Add-On Directives Section */}
                <div className="addon-section-header">
                  <span className="addon-section-label">Quick Add-On Directives (Click to toggle & append):</span>
                </div>

                <div className="quick-focus-chips">
                  {SDLC_ADDON_PROMPTS.map((addon) => {
                    const isSelected = customInstructions.includes(addon.prompt);
                    return (
                      <button
                        key={addon.id}
                        type="button"
                        className={`quick-focus-chip ${isSelected ? 'active' : ''}`}
                        title={addon.prompt}
                        onClick={() => {
                          if (isSelected) {
                            setCustomInstructions(prev => 
                              prev.replace(addon.prompt, '')
                                  .replace(/,\s*,/g, ',')
                                  .replace(/^[\s,]+|[\s,]+$/g, '')
                                  .trim()
                            );
                          } else {
                            setCustomInstructions(prev => {
                              const base = prev.trim();
                              return base ? `${base} ${addon.prompt}` : addon.prompt;
                            });
                          }
                        }}
                      >
                        {addon.icon === 'zap' && <Zap size={11} />}
                        {addon.icon === 'shield' && <ShieldCheck size={11} />}
                        {addon.icon === 'refresh' && <RotateCcw size={11} />}
                        {addon.icon === 'activity' && <Activity size={11} />}
                        {addon.icon === 'test' && <CheckCircle2 size={11} />}
                        {addon.icon === 'box' && <Box size={11} />}
                        {addon.icon === 'layers' && <Layers size={11} />}
                        {addon.icon === 'database' && <Database size={11} />}
                        <span>{addon.label}</span>
                      </button>
                    );
                  })}
                </div>

                {/* Prompt Actions: Save Preset & Reset */}
                <div className="prompt-actions-row">
                  <button
                    type="button"
                    className="prompt-action-btn primary"
                    onClick={handleSaveCurrentPrompt}
                    title="Save extra instructions as reusable preset"
                  >
                    <Save size={12} />
                    <span>Save Add-On Preset</span>
                  </button>
                  <button
                    type="button"
                    className="prompt-action-btn danger"
                    onClick={() => setCustomInstructions('')}
                    title="Clear extra instructions"
                  >
                    <X size={12} />
                    <span>Clear</span>
                  </button>
                </div>

                {/* User Saved Presets List */}
                {savedCustomPrompts.length > 0 && (
                  <div className="saved-prompts-container">
                    <span className="saved-prompts-label">My Saved Add-On Presets:</span>
                    <div className="saved-prompts-list">
                      {savedCustomPrompts.map(sp => (
                        <div
                          key={sp.id}
                          className="saved-prompt-chip"
                          onClick={() => {
                            if (sp.perspective) setSelectedPerspective(sp.perspective);
                            setCustomInstructions(sp.prompt);
                          }}
                          title={`Click to load: "${sp.name}"`}
                        >
                          <span>{sp.name}</span>
                          <span 
                            className="saved-prompt-delete"
                            onClick={(e) => handleDeleteSavedPrompt(sp.id, e)}
                            title="Delete preset"
                          >
                            ×
                          </span>
                        </div>
                      ))}
                    </div>
                  </div>
                )}
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
                <span>Synthesizing Architecture...</span>
              </>
            ) : (
              <>
                <Sparkles size={17} />
                <span>Analyze Architecture</span>
              </>
            )}
          </button>

          {/* Enhanced Error Banner with Custom Model / Credit Settings Hint */}
          {error && (
            <div className="error-banner">
              <div className="error-body-wrapper">
                <AlertTriangle size={17} className="error-icon" />
                <div className="error-message-col">
                  <span className="error-text">{error}</span>
                  <div className="error-hint-box">
                    <p>If API credits are exhausted or rate limited, switch to your own custom API key or model:</p>
                    <button
                      type="button"
                      className="error-settings-cta"
                      onClick={() => setShowSettingsModal(true)}
                    >
                      <Settings size={13} />
                      <span>Open Settings & Add Custom Model / Key</span>
                    </button>
                  </div>
                </div>
              </div>
              <button className="error-close-btn" onClick={() => setError(null)} aria-label="Dismiss error">
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
                  {currentStep === 2 && 'AI reasoning through architecture...'}
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

          {/* Success Banner with Frame Zoom */}
          {syncSuccess && (
            <div className="success-banner">
              <div style={{ display: 'flex', alignItems: 'center', gap: '0.6rem' }}>
                <CheckCircle2 size={16} />
                <span>
                  <b>Framed & Synced on Miro:</b> {syncSuccess.frame_title || 'Architecture Canvas'} ({syncSuccess.created_nodes} nodes, {syncSuccess.created_connectors} connectors)
                </span>
              </div>
              <a
                href={syncSuccess.board_url}
                target="_blank"
                rel="noopener noreferrer"
                className="view-miro-btn"
                title="Open and zoom directly into this perspective frame on Miro"
              >
                <span>Zoom to Frame on Miro</span>
                <ExternalLink size={14} />
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
                  <span>Architectural Reasoning Chain</span>
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
                    ? 'Analyzing modules, databases, and message brokers into visual layers.'
                    : 'Select a repository, local codebase, or preset on the left, then click "Analyze Architecture".'}
                </p>
              </div>
            </div>
          )}
        </section>
      </main>

      {/* Custom Credentials & Settings Modal */}
      {showSettingsModal && (
        <div className="modal-overlay" onClick={() => setShowSettingsModal(false)}>
          <div className="modal-card settings-modal" onClick={(e) => e.stopPropagation()}>
            <div className="modal-header">
              <div className="modal-title-group">
                <Settings size={18} className="modal-icon" />
                <div>
                  <h3>Settings & Custom Credentials</h3>
                  <p>Configure custom Miro board access and universal AI model inference endpoints</p>
                </div>
              </div>
              <button 
                className="modal-close-btn" 
                onClick={() => setShowSettingsModal(false)}
                aria-label="Close Settings"
              >
                <X size={18} />
              </button>
            </div>

            <div className="modal-body settings-body">
              {/* Section 1: Miro Credentials */}
              <div className="settings-section">
                <div className="settings-section-title">
                  <div className="section-badge miro-badge">Miro</div>
                  <h4>Miro Workspace Credentials</h4>
                </div>
                <p className="settings-desc">
                  Provide your personal Miro OAuth2 / Developer Access Token and Board ID to sync directly to your own boards. Leave blank to use server defaults.
                </p>

                <div className="settings-grid">
                  <div className="settings-field">
                    <label>Miro Access Token</label>
                    <div className="input-with-action">
                      <input
                        type={showMiroToken ? 'text' : 'password'}
                        placeholder="eyJhbGciOi..."
                        value={customSettings.miroAccessToken}
                        onChange={(e) => setCustomSettings({ ...customSettings, miroAccessToken: e.target.value })}
                        className="settings-input"
                      />
                      <button
                        type="button"
                        className="input-eye-btn"
                        onClick={() => setShowMiroToken(!showMiroToken)}
                        title={showMiroToken ? 'Hide token' : 'Show token'}
                      >
                        {showMiroToken ? <EyeOff size={15} /> : <Eye size={15} />}
                      </button>
                    </div>
                  </div>

                  <div className="settings-field">
                    <label>Miro Board ID</label>
                    <input
                      type="text"
                      placeholder="e.g. uXjVN5oQe0Y="
                      value={customSettings.miroBoardId}
                      onChange={(e) => setCustomSettings({ ...customSettings, miroBoardId: e.target.value })}
                      className="settings-input"
                    />
                  </div>
                </div>

                <div className="miro-test-bar">
                  <button
                    type="button"
                    className="test-btn"
                    onClick={handleTestMiroConnection}
                    disabled={testingMiro}
                  >
                    {testingMiro ? <RefreshCw size={14} className="spin" /> : <ShieldCheck size={14} />}
                    <span>{testingMiro ? 'Testing Miro...' : 'Verify Miro Credentials'}</span>
                  </button>

                  {miroTestResult && (
                    <div className={`test-result-badge ${miroTestResult.success ? 'success' : 'error'}`}>
                      {miroTestResult.success ? <CheckCircle2 size={14} /> : <AlertTriangle size={14} />}
                      <span>{miroTestResult.message}</span>
                    </div>
                  )}
                </div>
              </div>

              {/* Section 2: Universal AI Model / Inference Provider */}
              <div className="settings-section">
                <div className="settings-section-title">
                  <div className="section-badge ai-badge">AI Engine</div>
                  <h4>Universal Model & Inference Provider</h4>
                </div>
                <p className="settings-desc">
                  Connect to ModelScope, local Ollama, DeepSeek, OpenAI, OpenRouter, Groq, or any OpenAI-compatible endpoint.
                </p>

                {/* Quick Presets */}
                <div className="presets-wrapper">
                  <label className="field-label-small">Quick Model Presets</label>
                  <div className="preset-chips">
                    <button
                      type="button"
                      className="preset-chip"
                      onClick={() => setCustomSettings({
                        ...customSettings,
                        aiProvider: 'modelscope',
                        aiBaseUrl: 'https://api-inference.modelscope.ai/v1',
                        aiModelName: 'Qwen/Qwen3.8-27B'
                      })}
                    >
                      Qwen 3.8 27B (ModelScope)
                    </button>
                    <button
                      type="button"
                      className="preset-chip"
                      onClick={() => setCustomSettings({
                        ...customSettings,
                        aiProvider: 'modelscope',
                        aiBaseUrl: 'https://api-inference.modelscope.ai/v1',
                        aiModelName: 'Qwen/Qwen2.5-Coder-32B-Instruct'
                      })}
                    >
                      Qwen 2.5 Coder 32B
                    </button>
                    <button
                      type="button"
                      className="preset-chip"
                      onClick={() => setCustomSettings({
                        ...customSettings,
                        aiProvider: 'custom',
                        aiBaseUrl: 'https://api.deepseek.com/v1',
                        aiModelName: 'deepseek-chat'
                      })}
                    >
                      DeepSeek V3
                    </button>
                    <button
                      type="button"
                      className="preset-chip"
                      onClick={() => setCustomSettings({
                        ...customSettings,
                        aiProvider: 'custom',
                        aiBaseUrl: 'https://api.openai.com/v1',
                        aiModelName: 'gpt-4o'
                      })}
                    >
                      OpenAI GPT-4o
                    </button>
                    <button
                      type="button"
                      className="preset-chip"
                      onClick={() => setCustomSettings({
                        ...customSettings,
                        aiProvider: 'custom',
                        aiBaseUrl: 'https://openrouter.ai/api/v1',
                        aiModelName: 'qwen/qwen-2.5-coder-32b-instruct'
                      })}
                    >
                      OpenRouter (Any LLM)
                    </button>
                    <button
                      type="button"
                      className="preset-chip"
                      onClick={() => setCustomSettings({
                        ...customSettings,
                        aiProvider: 'custom',
                        aiBaseUrl: 'https://api.groq.com/openai/v1',
                        aiModelName: 'llama-3.3-70b-versatile'
                      })}
                    >
                      Groq (Ultra-Fast)
                    </button>
                    <button
                      type="button"
                      className="preset-chip"
                      onClick={() => setCustomSettings({
                        ...customSettings,
                        aiProvider: 'ollama',
                        aiBaseUrl: 'http://localhost:11434/v1',
                        aiModelName: 'qwen2.5-coder:7b'
                      })}
                    >
                      Local Ollama
                    </button>
                  </div>
                </div>

                <div className="settings-grid">
                  <div className="settings-field">
                    <label>Provider Mode</label>
                    <select
                      value={customSettings.aiProvider}
                      onChange={(e) => setCustomSettings({ ...customSettings, aiProvider: e.target.value })}
                      className="settings-input"
                    >
                      <option value="modelscope">ModelScope (Cloud Qwen)</option>
                      <option value="ollama">Local Ollama</option>
                      <option value="custom">Custom (OpenAI-compatible / DeepSeek / OpenRouter / Groq / vLLM)</option>
                    </select>
                  </div>

                  <div className="settings-field">
                    <label>Model ID / Name</label>
                    <input
                      type="text"
                      placeholder="e.g. Qwen/Qwen3.8-27B or gpt-4o"
                      value={customSettings.aiModelName}
                      onChange={(e) => setCustomSettings({ ...customSettings, aiModelName: e.target.value })}
                      className="settings-input"
                    />
                  </div>

                  <div className="settings-field full-width">
                    <label>Base URL Endpoint</label>
                    <input
                      type="text"
                      placeholder="https://api-inference.modelscope.ai/v1"
                      value={customSettings.aiBaseUrl}
                      onChange={(e) => setCustomSettings({ ...customSettings, aiBaseUrl: e.target.value })}
                      className="settings-input"
                    />
                  </div>

                  <div className="settings-field full-width">
                    <label>API Key / Bearer Token</label>
                    <div className="input-with-action">
                      <input
                        type={showApiKey ? 'text' : 'password'}
                        placeholder="Leave blank to use server environment default"
                        value={customSettings.aiApiKey}
                        onChange={(e) => setCustomSettings({ ...customSettings, aiApiKey: e.target.value })}
                        className="settings-input"
                      />
                      <button
                        type="button"
                        className="input-eye-btn"
                        onClick={() => setShowApiKey(!showApiKey)}
                        title={showApiKey ? 'Hide API key' : 'Show API key'}
                      >
                        {showApiKey ? <EyeOff size={15} /> : <Eye size={15} />}
                      </button>
                    </div>
                  </div>
                </div>
              </div>
            </div>

            <div className="modal-footer">
              <button
                type="button"
                className="reset-btn"
                onClick={handleResetSettings}
              >
                <RotateCcw size={14} />
                <span>Reset to Defaults</span>
              </button>

              <button
                type="button"
                className="save-btn"
                onClick={() => {
                  handleSaveSettings(customSettings);
                  setShowSettingsModal(false);
                }}
              >
                <Save size={14} />
                <span>Save & Apply Settings</span>
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
