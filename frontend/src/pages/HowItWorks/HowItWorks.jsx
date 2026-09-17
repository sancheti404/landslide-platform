import React, { useState } from 'react';
import {
  Mountain,
  Satellite,
  CloudRain,
  ShieldAlert,
  MapPin,
  ArrowRight,
  AlertTriangle,
  Info,
  ChevronDown,
  ChevronUp,
  Database,
  Layers,
  CheckCircle2,
} from 'lucide-react';
import { Badge } from '../../components/common/Badge';

export function HowItWorks() {
  const [techDetailsOpen, setTechDetailsOpen] = useState(false);

  return (
    <div style={{ maxWidth: '880px', margin: '0 auto', padding: '1.75rem 1.25rem', width: '100%' }}>
      {/* 1. Header */}
      <div style={{ borderBottom: '1px solid var(--border-subtle)', paddingBottom: '1rem', marginBottom: '1.5rem' }}>
        <h1 style={{ fontSize: '1.5rem', fontWeight: 800, color: 'var(--text-primary)', letterSpacing: '-0.02em', marginBottom: '0.35rem' }}>
          How It Works
        </h1>
        <p style={{ fontSize: '0.9rem', color: 'var(--text-secondary)', margin: 0 }}>
          UK-LIP combines terrain, satellite imagery, and recent rainfall conditions to provide landslide risk information.
        </p>
      </div>

      <div style={{ display: 'flex', flexDirection: 'column', gap: '1.75rem' }}>
        {/* 2. Simple Overview (Visual Flow) */}
        <section
          style={{
            background: '#ffffff',
            border: '1px solid var(--border-subtle)',
            borderRadius: 'var(--radius-md)',
            padding: '1.25rem 1.5rem',
            boxShadow: 'var(--shadow-xs)',
          }}
          aria-label="System Overview Flow"
        >
          <div style={{ fontSize: '0.75rem', fontWeight: 700, color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.05em', marginBottom: '0.85rem' }}>
            System Workflow Overview
          </div>

          <div
            style={{
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'space-between',
              flexWrap: 'wrap',
              gap: '0.5rem',
            }}
          >
            <FlowStep label="Terrain" icon={<Mountain size={16} style={{ color: '#0284c7' }} />} />
            <ArrowRight size={14} style={{ color: 'var(--text-dim)', flexShrink: 0 }} />
            <FlowStep label="Satellite Imagery" icon={<Satellite size={16} style={{ color: '#0f766e' }} />} />
            <ArrowRight size={14} style={{ color: 'var(--text-dim)', flexShrink: 0 }} />
            <FlowStep label="Rainfall Conditions" icon={<CloudRain size={16} style={{ color: '#6366f1' }} />} />
            <ArrowRight size={14} style={{ color: 'var(--text-dim)', flexShrink: 0 }} />
            <FlowStep label="Combined Risk" icon={<ShieldAlert size={16} style={{ color: '#d97706' }} />} highlight />
            <ArrowRight size={14} style={{ color: 'var(--text-dim)', flexShrink: 0 }} />
            <FlowStep label="Location Information" icon={<MapPin size={16} style={{ color: '#059669' }} />} />
          </div>
        </section>

        {/* 3. What the System Looks At */}
        <section aria-label="Input Factors">
          <div style={{ marginBottom: '0.85rem' }}>
            <h2 style={{ fontSize: '1.1rem', fontWeight: 700, color: 'var(--text-primary)', margin: 0 }}>
              What the System Looks At
            </h2>
            <p style={{ fontSize: '0.825rem', color: 'var(--text-secondary)', marginTop: '0.2rem' }}>
              Three primary operational signals are evaluated for any assessed location.
            </p>
          </div>

          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(250px, 1fr))', gap: '1rem' }}>
            <FactorCard
              title="TERRAIN"
              icon={<Mountain size={20} style={{ color: '#0284c7' }} />}
              description="Terrain characteristics such as slope and elevation are used to identify areas with terrain conditions associated with landslides."
            />
            <FactorCard
              title="SATELLITE IMAGERY"
              icon={<Satellite size={20} style={{ color: '#0f766e' }} />}
              description="Recent satellite imagery is analyzed for visual patterns associated with landslide-related conditions."
            />
            <FactorCard
              title="RAINFALL CONDITIONS"
              icon={<CloudRain size={20} style={{ color: '#6366f1' }} />}
              description="Recent rainfall over multiple time windows is used as an operational trigger/stress signal. Rainfall is an operational stress factor, not a standalone landslide prediction or calibrated probability."
            />
          </div>
        </section>

        {/* 4. Combined Risk */}
        <section
          style={{
            background: '#ffffff',
            border: '1px solid var(--border-subtle)',
            borderRadius: 'var(--radius-md)',
            padding: '1.5rem',
            boxShadow: 'var(--shadow-xs)',
          }}
          aria-label="Combined Risk Explanation"
        >
          <h2 style={{ fontSize: '1.1rem', fontWeight: 700, color: 'var(--text-primary)', marginBottom: '0.5rem' }}>
            Combined Risk
          </h2>
          <p style={{ fontSize: '0.9rem', color: 'var(--text-secondary)', lineHeight: 1.6, margin: 0 }}>
            Terrain and satellite-based signals are combined, then recent rainfall conditions can increase the operational risk level.
          </p>

          <div
            style={{
              background: '#f8fafc',
              border: '1px solid var(--border-subtle)',
              borderLeft: '4px solid var(--brand-primary)',
              borderRadius: 'var(--radius-sm)',
              padding: '0.85rem 1rem',
              marginTop: '1rem',
              fontSize: '0.825rem',
              color: 'var(--text-primary)',
              lineHeight: 1.5,
            }}
          >
            <strong>Operational Decision-Support Heuristic:</strong> Risk scores are decision-support heuristics and should not be interpreted as calibrated probabilities. They do not represent a guaranteed percentage chance of slope failure.
          </div>
        </section>

        {/* 5. What a Result Means */}
        <section aria-label="Risk Categories">
          <div style={{ marginBottom: '0.85rem' }}>
            <h2 style={{ fontSize: '1.1rem', fontWeight: 700, color: 'var(--text-primary)', margin: 0 }}>
              What a Result Means
            </h2>
            <p style={{ fontSize: '0.825rem', color: 'var(--text-secondary)', marginTop: '0.2rem' }}>
              Assessments are grouped into four operational categories to guide response planning.
            </p>
          </div>

          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '0.85rem' }}>
            <CategoryCard
              level="LOW"
              color="#059669"
              bg="#ecfdf5"
              border="#a7f3d0"
              meaning="Lower operational risk under the assessed conditions."
            />
            <CategoryCard
              level="MODERATE"
              color="#d97706"
              bg="#fffbeb"
              border="#fde68a"
              meaning="Moderate operational risk under the assessed conditions."
            />
            <CategoryCard
              level="HIGH"
              color="#ea580c"
              bg="#fff7ed"
              border="#fed7aa"
              meaning="High operational risk under the assessed conditions."
            />
            <CategoryCard
              level="CRITICAL"
              color="#dc2626"
              bg="#fef2f2"
              border="#fecaca"
              meaning="Very high operational risk under the assessed conditions."
            />
          </div>
        </section>

        {/* 6. Data Sources */}
        <section
          style={{
            background: '#ffffff',
            border: '1px solid var(--border-subtle)',
            borderRadius: 'var(--radius-md)',
            padding: '1.5rem',
            boxShadow: 'var(--shadow-xs)',
          }}
          aria-label="Data Sources"
        >
          <h2 style={{ fontSize: '1.1rem', fontWeight: 700, color: 'var(--text-primary)', marginBottom: '0.5rem' }}>
            Data Sources
          </h2>
          <p style={{ fontSize: '0.825rem', color: 'var(--text-secondary)', marginBottom: '1rem' }}>
            The platform relies on four primary datasets:
          </p>

          <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
            <DataSourceItem
              title="GSI NLSM Landslide Inventory"
              description="GSI NLSM Inventory — 5,523 historical records used by the project to identify past landslide locations across Uttarakhand."
            />
            <DataSourceItem
              title="SRTM GL1 30m DEM"
              description="Terrain elevation data (30-meter resolution) used by the project to calculate slope, aspect, and curvature."
            />
            <DataSourceItem
              title="Sentinel-2 satellite imagery"
              description="Multispectral satellite imagery used by the project to assess visual surface patterns."
            />
            <DataSourceItem
              title="CHIRPS Daily rainfall data"
              description="Daily precipitation estimates (0.05° resolution) used to calculate recent rainfall conditions across multiple time windows."
            />
          </div>
        </section>

        {/* 7. Limitations ("What this system cannot tell you") */}
        <section
          style={{
            background: '#f8fafc',
            border: '1px solid var(--border-subtle)',
            borderRadius: 'var(--radius-md)',
            padding: '1.5rem',
          }}
          aria-label="System Limitations"
        >
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '0.65rem' }}>
            <AlertTriangle size={18} style={{ color: '#d97706' }} />
            <h2 style={{ fontSize: '1.05rem', fontWeight: 700, color: 'var(--text-primary)', margin: 0 }}>
              What this system cannot tell you
            </h2>
          </div>

          <p style={{ fontSize: '0.825rem', color: 'var(--text-secondary)', marginBottom: '0.85rem' }}>
            Important operational boundaries and constraints:
          </p>

          <ul style={{ paddingLeft: '1.25rem', margin: 0, fontSize: '0.825rem', color: 'var(--text-secondary)', display: 'flex', flexDirection: 'column', gap: '0.45rem', lineHeight: 1.5 }}>
            <li>A risk score is not a guarantee that a landslide will or will not occur.</li>
            <li>The score is not a calibrated probability.</li>
            <li>Satellite imagery may not represent the exact current ground condition.</li>
            <li>Rainfall conditions are an operational trigger/stress signal, not a standalone landslide prediction.</li>
            <li>Results are limited to the supported Uttarakhand operating area and available training-data coverage.</li>
            <li>Reference map routes do not automatically account for landslide hazards.</li>
            <li>Emergency resources shown in the platform may be synthetic demo data.</li>
          </ul>
        </section>

        {/* 8. Technical Details (Collapsed by Default) */}
        <section style={{ borderTop: '1px solid var(--border-subtle)', paddingTop: '1rem' }}>
          <button
            type="button"
            onClick={() => setTechDetailsOpen((prev) => !prev)}
            style={{
              background: 'none',
              border: 'none',
              color: 'var(--text-muted)',
              fontSize: '0.85rem',
              fontWeight: 600,
              cursor: 'pointer',
              display: 'flex',
              alignItems: 'center',
              gap: '0.35rem',
              padding: '0.25rem 0',
            }}
          >
            <span>Technical details</span>
            {techDetailsOpen ? <ChevronUp size={16} /> : <ChevronDown size={16} />}
          </button>

          {techDetailsOpen && (
            <div
              style={{
                marginTop: '0.85rem',
                background: '#ffffff',
                border: '1px solid var(--border-subtle)',
                borderRadius: 'var(--radius-md)',
                padding: '1.25rem',
                display: 'flex',
                flexDirection: 'column',
                gap: '0.85rem',
                fontSize: '0.825rem',
              }}
            >
              <div>
                <div style={{ fontWeight: 700, color: 'var(--text-primary)', marginBottom: '0.2rem' }}>
                  Model Architecture & Fusion Formula
                </div>
                <div
                  style={{
                    background: '#f8fafc',
                    padding: '0.75rem 1rem',
                    borderRadius: 'var(--radius-sm)',
                    fontFamily: 'ui-monospace, SFMono-Regular, monospace',
                    fontSize: '0.8rem',
                    color: '#0f766e',
                    border: '1px solid var(--border-subtle)',
                    lineHeight: 1.6,
                  }}
                >
                  static_visual_fusion_score = 0.38 * P_xgboost + 0.62 * P_swin<br />
                  operational_risk_score = min(1.0, static_visual_fusion_score * (1.0 + 0.50 * S_rain))
                </div>
              </div>

              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(240px, 1fr))', gap: '0.75rem' }}>
                <div style={{ background: '#f8fafc', padding: '0.75rem', borderRadius: 'var(--radius-sm)', border: '1px solid var(--border-subtle)' }}>
                  <div style={{ fontWeight: 600, color: 'var(--text-primary)' }}>Terrain Model: XGBoost</div>
                  <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', marginTop: '0.15rem' }}>
                    Tuned gradient-boosted trees evaluating 10 geomorphometric features derived from SRTM GL1 30m DEM. Weight: 0.38. ROC-AUC: 0.9481.
                  </div>
                </div>

                <div style={{ background: '#f8fafc', padding: '0.75rem', borderRadius: 'var(--radius-sm)', border: '1px solid var(--border-subtle)' }}>
                  <div style={{ fontWeight: 600, color: 'var(--text-primary)' }}>Satellite Model: Swin Transformer</div>
                  <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', marginTop: '0.15rem' }}>
                    Hierarchical vision transformer classifying 128×128 Sentinel-2 optical patches resized to 224×224. Weight: 0.62. ROC-AUC: 0.9666.
                  </div>
                </div>

                <div style={{ background: '#f8fafc', padding: '0.75rem', borderRadius: 'var(--radius-sm)', border: '1px solid var(--border-subtle)' }}>
                  <div style={{ fontWeight: 600, color: 'var(--text-primary)' }}>Rainfall Trigger: CHIRPS Daily</div>
                  <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', marginTop: '0.15rem' }}>
                    0.05° gridded daily precipitation computing causal 3d, 7d, 14d, and 30d antecedent accumulations as an operational trigger multiplier.
                  </div>
                </div>

                <div style={{ background: '#f8fafc', padding: '0.75rem', borderRadius: 'var(--radius-sm)', border: '1px solid var(--border-subtle)' }}>
                  <div style={{ fontWeight: 600, color: 'var(--text-primary)' }}>Weighted Late Fusion</div>
                  <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', marginTop: '0.15rem' }}>
                    Late fusion combining terrain (0.38) and satellite (0.62) models with operational rainfall trigger. ROC-AUC: 0.9707.
                  </div>
                </div>
              </div>

              <div style={{ fontSize: '0.72rem', color: 'var(--text-dim)', paddingTop: '0.5rem', borderTop: '1px solid var(--border-subtle)' }}>
                Risk scores are decision-support heuristics and should not be interpreted as calibrated probabilities.
              </div>
            </div>
          )}
        </section>
      </div>
    </div>
  );
}

function FlowStep({ label, icon, highlight }) {
  return (
    <div
      style={{
        display: 'flex',
        alignItems: 'center',
        gap: '0.45rem',
        background: highlight ? '#fef3c7' : '#f8fafc',
        border: `1px solid ${highlight ? '#fde68a' : 'var(--border-subtle)'}`,
        padding: '0.45rem 0.75rem',
        borderRadius: 'var(--radius-sm)',
        fontSize: '0.8rem',
        fontWeight: highlight ? 700 : 600,
        color: 'var(--text-primary)',
      }}
    >
      {icon}
      <span>{label}</span>
    </div>
  );
}

function FactorCard({ title, icon, description }) {
  return (
    <div
      style={{
        background: '#ffffff',
        border: '1px solid var(--border-subtle)',
        borderRadius: 'var(--radius-md)',
        padding: '1.25rem',
        boxShadow: 'var(--shadow-xs)',
        display: 'flex',
        flexDirection: 'column',
        gap: '0.5rem',
      }}
    >
      <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
        {icon}
        <span style={{ fontSize: '0.85rem', fontWeight: 700, color: 'var(--text-primary)' }}>{title}</span>
      </div>
      <p style={{ fontSize: '0.825rem', color: 'var(--text-secondary)', lineHeight: 1.5, margin: 0 }}>
        {description}
      </p>
    </div>
  );
}

function CategoryCard({ level, color, bg, border, meaning }) {
  return (
    <div
      style={{
        background: bg,
        border: `1px solid ${border}`,
        borderRadius: 'var(--radius-sm)',
        padding: '1rem',
        display: 'flex',
        flexDirection: 'column',
        gap: '0.35rem',
      }}
    >
      <span style={{ fontSize: '0.95rem', fontWeight: 800, color }}>{level}</span>
      <p style={{ fontSize: '0.78rem', color: 'var(--text-primary)', lineHeight: 1.4, margin: 0 }}>
        {meaning}
      </p>
    </div>
  );
}

function DataSourceItem({ title, description }) {
  return (
    <div
      style={{
        background: '#f8fafc',
        border: '1px solid var(--border-subtle)',
        borderRadius: 'var(--radius-sm)',
        padding: '0.85rem 1rem',
      }}
    >
      <div style={{ fontSize: '0.85rem', fontWeight: 700, color: 'var(--text-primary)', marginBottom: '0.2rem' }}>
        {title}
      </div>
      <div style={{ fontSize: '0.8rem', color: 'var(--text-secondary)', lineHeight: 1.45 }}>
        {description}
      </div>
    </div>
  );
}

export default HowItWorks;
