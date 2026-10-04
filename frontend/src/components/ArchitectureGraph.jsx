import React from 'react';
import { 
  ArrowRight, 
  CheckCircle2, 
  AlertTriangle, 
  Lightbulb,
  Globe,
  ShieldCheck,
  Server,
  Database,
  Zap,
  Inbox,
  Plug,
  Code2
} from 'lucide-react';

const TYPE_CONFIG = {
  frontend: { 
    border: '#0071e3', 
    badgeBg: 'rgba(0, 113, 227, 0.12)', 
    badgeText: '#0071e3', 
    label: 'Client / UI', 
    icon: Globe 
  },
  gateway: { 
    border: '#af52de', 
    badgeBg: 'rgba(175, 82, 222, 0.12)', 
    badgeText: '#af52de', 
    label: 'Gateway', 
    icon: ShieldCheck 
  },
  service: { 
    border: '#34c759', 
    badgeBg: 'rgba(52, 199, 89, 0.12)', 
    badgeText: '#34c759', 
    label: 'Service', 
    icon: Server 
  },
  database: { 
    border: '#ff9f0a', 
    badgeBg: 'rgba(255, 159, 10, 0.12)', 
    badgeText: '#ff9f0a', 
    label: 'Database', 
    icon: Database 
  },
  cache: { 
    border: '#ff3b30', 
    badgeBg: 'rgba(255, 59, 48, 0.12)', 
    badgeText: '#ff3b30', 
    label: 'Cache', 
    icon: Zap 
  },
  queue: { 
    border: '#5856d6', 
    badgeBg: 'rgba(88, 86, 214, 0.12)', 
    badgeText: '#5856d6', 
    label: 'Event Queue', 
    icon: Inbox 
  },
  external: { 
    border: '#8e8e93', 
    badgeBg: 'rgba(142, 142, 147, 0.12)', 
    badgeText: '#8e8e93', 
    label: 'External API', 
    icon: Plug 
  }
};

export default function ArchitectureGraph({ architecture, onScaffold }) {
  if (!architecture || !architecture.layers) {
    return null;
  }

  const { layers, nodes, connections, insights } = architecture;

  // Group nodes by layer
  const layerBuckets = {};
  layers.forEach(l => { layerBuckets[l.id] = []; });
  
  nodes.forEach(node => {
    const lid = node.layer_id || 'layer_services';
    if (!layerBuckets[lid]) layerBuckets[lid] = [];
    layerBuckets[lid].push(node);
  });

  return (
    <div className="preview-container">
      {/* 2D Layered Graph Canvas */}
      <div className="graph-canvas">
        {layers.map(layer => {
          const layerNodes = layerBuckets[layer.id] || [];
          if (layerNodes.length === 0) return null;

          return (
            <div key={layer.id} className="layer-column">
              <div className="layer-title-badge">
                <span>{layer.name}</span>
                <span className="count-pill">{layerNodes.length}</span>
              </div>
              
              <div className="layer-nodes-stack">
                {layerNodes.map(node => {
                  const style = TYPE_CONFIG[node.type] || TYPE_CONFIG.service;
                  const IconComp = style.icon;

                  return (
                    <div
                      key={node.id}
                      className={`node-card ${node.type || 'service'}`}
                      style={{ 
                        borderColor: style.border,
                        borderLeftWidth: '4px'
                      }}
                    >
                      <div className="node-card-header">
                        <span style={{ color: style.badgeText, display: 'flex', alignItems: 'center' }}>
                          <IconComp size={16} />
                        </span>
                        <h4 className="node-title">{node.name}</h4>
                      </div>

                      {node.tech && (
                        <div 
                          className="node-tech-badge"
                          style={{ 
                            backgroundColor: style.badgeBg, 
                            color: style.badgeText,
                            border: `1px solid ${style.border}40`
                          }}
                        >
                          {node.tech}
                        </div>
                      )}

                      {node.description && (
                        <p className="node-description">
                          {node.description}
                        </p>
                      )}

                      {node.endpoints_or_features && node.endpoints_or_features.length > 0 && (
                        <div className="node-features-list">
                          {node.endpoints_or_features.slice(0, 2).map((feat, fIdx) => (
                            <span key={fIdx} className="feature-chip">
                              • {feat}
                            </span>
                          ))}
                        </div>
                      )}

                      {onScaffold && (
                        <div className="node-card-footer">
                          <button
                            type="button"
                            className="node-scaffold-btn"
                            onClick={(e) => {
                              e.stopPropagation();
                              onScaffold(node);
                            }}
                            title={`Scaffold production starter code for ${node.name}`}
                          >
                            <Code2 size={12} />
                            <span>Scaffold Code</span>
                          </button>
                        </div>
                      )}
                    </div>
                  );
                })}
              </div>
            </div>
          );
        })}
      </div>

      {/* Connections Flow Summary */}
      {connections && connections.length > 0 && (
        <div className="connections-card">
          <div className="connections-header">
            <h4>Data Flow & Protocols ({connections.length})</h4>
          </div>
          <div className="connections-pills-row">
            {connections.map((c, i) => (
              <div key={i} className="connection-chip">
                <span className="from-node">{c.from}</span>
                <ArrowRight size={12} className="conn-arrow" />
                <span className="to-node">{c.to}</span>
                <span className="proto-badge">{c.protocol || 'calls'}</span>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Architectural Insights Grid */}
      {insights && (
        <div className="insights-grid">
          {insights.strengths && insights.strengths.length > 0 && (
            <div className="insight-box strengths">
              <h4>
                <CheckCircle2 size={15} style={{ color: '#34c759' }} />
                <span>Architectural Strengths</span>
              </h4>
              <ul>
                {insights.strengths.map((s, idx) => (
                  <li key={idx}>{s}</li>
                ))}
              </ul>
            </div>
          )}
          {insights.bottlenecks && insights.bottlenecks.length > 0 && (
            <div className="insight-box bottlenecks">
              <h4>
                <AlertTriangle size={15} style={{ color: '#ff3b30' }} />
                <span>Bottlenecks & Scaling Risks</span>
              </h4>
              <ul>
                {insights.bottlenecks.map((b, idx) => (
                  <li key={idx}>{b}</li>
                ))}
              </ul>
            </div>
          )}
          {insights.recommendations && insights.recommendations.length > 0 && (
            <div className="insight-box recommendations">
              <h4>
                <Lightbulb size={15} style={{ color: '#0071e3' }} />
                <span>Recommendations</span>
              </h4>
              <ul>
                {insights.recommendations.map((r, idx) => (
                  <li key={idx}>{r}</li>
                ))}
              </ul>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
