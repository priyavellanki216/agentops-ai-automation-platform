import { useState } from "react";
import { useLocation } from "wouter";
import { useAuth } from "@/_core/hooks/useAuth";
import { startLogin } from "@/const";
import {
  Activity,
  AlertTriangle,
  ArrowUpRight,
  Bot,
  ChevronRight,
  CircleCheck,
  Clock3,
  Code2,
  Database,
  FileSearch,
  GitCompareArrows,
  KeyRound,
  LayoutDashboard,
  LifeBuoy,
  Menu,
  Network,
  Play,
  Plus,
  Search,
  ShieldCheck,
  SlidersHorizontal,
  Sparkles,
  Terminal,
  X,
  Zap,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Input } from "@/components/ui/input";

const navItems = [
  { label: "Agent Console", icon: LayoutDashboard },
  { label: "Trace Viewer", icon: Activity },
  { label: "Evaluation Dashboard", icon: GitCompareArrows },
  { label: "Tool Registry", icon: Network },
  { label: "System Health", icon: ShieldCheck },
];

const toolRows = [
  { name: "query_database", type: "SQL / approved views", role: "analyst", status: "Ready" },
  { name: "search_knowledge_base", type: "MCP / pgvector", role: "viewer", status: "Ready" },
  { name: "get_financial_summary", type: "MCP / finance", role: "admin", status: "Restricted" },
  { name: "create_ticket", type: "MCP / support", role: "support", status: "Ready" },
];

const traceSteps = [
  { label: "Request parsed", meta: "business_request", icon: Sparkles, color: "text-cyan-300" },
  { label: "Plan selected", meta: "2 tools · v2.4.1", icon: Bot, color: "text-violet-300" },
  { label: "Evidence retrieved", meta: "4 sources · 0.91 score", icon: FileSearch, color: "text-amber-300" },
  { label: "Answer grounded", meta: "citations attached", icon: CircleCheck, color: "text-emerald-300" },
];

function MetricCard({ label, value, detail, icon: Icon, tone = "cyan" }: { label: string; value: string; detail: string; icon: typeof Activity; tone?: "cyan" | "violet" | "amber" | "green" }) {
  const tones = { cyan: "text-cyan-300 bg-cyan-300/10", violet: "text-violet-300 bg-violet-300/10", amber: "text-amber-300 bg-amber-300/10", green: "text-emerald-300 bg-emerald-300/10" };
  return <div className="metric-card"><div className={`metric-icon ${tones[tone]}`}><Icon className="size-4" /></div><div><div className="metric-label">{label}</div><div className="metric-value">{value}</div><div className="metric-detail">{detail}</div></div></div>;
}

export default function Home() {
  const [location, setLocation] = useLocation();
  const { user } = useAuth();
  const routeLabels: Record<string, string> = { "/": "Agent Console", "/trace-viewer": "Trace Viewer", "/evaluation-dashboard": "Evaluation Dashboard", "/tool-registry": "Tool Registry", "/system-health": "System Health" };
  const [active, setActive] = useState(routeLabels[location] ?? "Agent Console");
  const [question, setQuestion] = useState("");
  const [submitted, setSubmitted] = useState(false);
  const [mobileOpen, setMobileOpen] = useState(false);

  const runAgent = () => { if (!user) { startLogin(); return; } if (question.trim()) setSubmitted(true); };

  return <div className="agent-shell">
    <aside className={`agent-sidebar ${mobileOpen ? "open" : ""}`}>
      <div className="brand-row"><div className="brand-mark"><Zap className="size-4" /></div><div><div className="brand-name">agent<span>ops</span></div><div className="brand-caption">AI operations platform</div></div><button className="mobile-close" onClick={() => setMobileOpen(false)}><X className="size-4" /></button></div>
      <div className="workspace-switcher"><div className="workspace-dot" /><div><div className="workspace-name">Acme workspace</div><div className="workspace-meta">Production · us-east-1</div></div><ChevronRight className="size-4 ml-auto text-slate-500" /></div>
      <div className="nav-section-label">Operations</div>
      <nav>{navItems.map(item => <button key={item.label} className={`nav-item ${active === item.label ? "active" : ""}`} onClick={() => { setActive(item.label); setLocation(item.label === "Agent Console" ? "/" : `/${item.label.toLowerCase().replaceAll(" ", "-")}`); setMobileOpen(false); }}><item.icon className="size-[17px]" /><span>{item.label}</span>{item.label === "System Health" && <span className="health-pip" />}</button>)}</nav>
      <div className="nav-section-label mt-7">Workspace</div>
      <nav><button className="nav-item"><Database className="size-[17px]" /><span>Data sources</span></button><button className="nav-item"><KeyRound className="size-[17px]" /><span>Access policies</span></button><button className="nav-item"><Code2 className="size-[17px]" /><span>API reference</span></button></nav>
      <div className="sidebar-bottom"><div className="security-note"><ShieldCheck className="size-4 text-emerald-300" /><div><div className="text-xs font-semibold text-slate-200">All systems secure</div><div className="text-[11px] text-slate-500 mt-1">Last checked 12s ago</div></div></div><div className="user-row"><div className="avatar">AK</div><div className="min-w-0"><div className="text-xs font-semibold text-slate-200 truncate">Alex Kim</div><div className="text-[11px] text-slate-500 truncate">admin · SSO connected</div></div><SlidersHorizontal className="size-4 text-slate-500 ml-auto" /></div></div>
    </aside>
    {mobileOpen && <button className="sidebar-overlay" onClick={() => setMobileOpen(false)} aria-label="Close navigation" />}
    <main className="agent-main">
      <header className="topbar"><div className="topbar-left"><button className="mobile-menu" onClick={() => setMobileOpen(true)}><Menu className="size-5" /></button><div className="breadcrumbs"><span>Workspace</span><ChevronRight className="size-3.5" /><strong>{active}</strong></div></div><div className="topbar-actions"><div className="auth-state">{user ? "Signed in" : "Preview mode"}</div><div className="status-live"><span className="live-dot" /> Operational</div><button className="icon-button"><Search className="size-4" /></button><div className="top-avatar">AK</div></div></header>
      <div className="content-wrap">
        <div className="page-heading"><div><div className="eyebrow"><span className="eyebrow-line" /> CONTROL PLANE / {active.toUpperCase()}</div><h1>{active}</h1><p>{active === "Agent Console" ? "Ask the platform to investigate internal business data with a complete evidence trail." : "Inspect platform behavior, reliability, and governance from one operational surface."}</p>{!user && <div className="auth-banner"><KeyRound className="size-3.5" /> Sign in to execute investigations; the console is in preview mode.</div>}</div><div className="heading-actions"><Badge className="version-badge"><span className="live-dot" /> agent-v2.4.1</Badge><Button variant="outline" className="export-button"><ArrowUpRight className="size-4" /> Export view</Button></div></div>
        <section className="metric-grid"><MetricCard label="Executions · 24h" value="1,284" detail="+18.4% vs. previous day" icon={Activity} tone="cyan" /><MetricCard label="Task success" value="92.8%" detail="Target ≥ 90% · on track" icon={CircleCheck} tone="green" /><MetricCard label="P95 latency" value="2.84s" detail="−11.2% · improving" icon={Clock3} tone="violet" /><MetricCard label="Active incidents" value="03" detail="1 requires attention" icon={AlertTriangle} tone="amber" /></section>
        <div className="workspace-grid">
          <section className="panel ask-panel"><div className="panel-header"><div><div className="panel-kicker"><Bot className="size-3.5" /> AGENT CONSOLE</div><h2>What should we investigate?</h2></div><Badge variant="outline" className="secure-badge"><ShieldCheck className="size-3" /> Evidence-gated</Badge></div><p className="panel-description">The agent will select approved tools, validate evidence, and return a cited answer. No arbitrary SQL execution.</p><div className="question-box"><textarea value={question} onChange={e => { setQuestion(e.target.value); setSubmitted(false); }} placeholder="e.g. Which customer segment had the highest increase in support tickets last month?" rows={3} /><div className="question-footer"><div className="question-hints"><span><Terminal className="size-3.5" /> Natural language</span><span><ShieldCheck className="size-3.5" /> Role-aware tools</span></div><Button onClick={runAgent} className="run-button"><Play className="size-3.5 fill-current" /> Run investigation</Button></div></div>{submitted && <div className="answer-preview"><div className="answer-top"><div className="answer-label"><CircleCheck className="size-4 text-emerald-300" /> Investigation complete</div><span>1.84s · trace_9f31a</span></div><p>Enterprise accounts showed the largest week-over-week increase in unresolved tickets, driven by authentication and billing workflows.</p><div className="source-chips"><span>query_database · 0.98</span><span>support_policy_07 · 0.91</span><span>+ 2 more sources</span></div></div>}
            <div className="suggestion-row"><span className="text-xs text-slate-500">Try a saved investigation</span><button onClick={() => setQuestion("What caused the increase in failed transactions last week?")}>Failed transactions <ArrowUpRight className="size-3" /></button><button onClick={() => setQuestion("Compare campaign performance across regions.")}>Campaign performance <ArrowUpRight className="size-3" /></button></div></section>
          <section className="panel trace-panel"><div className="panel-header"><div><div className="panel-kicker"><Activity className="size-3.5" /> LIVE TRACE</div><h2>Execution trace</h2></div><button className="text-button">View all <ArrowUpRight className="size-3.5" /></button></div><div className="trace-id"><span className="trace-pulse" /> trace_9f31a <span className="trace-time">just now</span></div><div className="trace-list">{traceSteps.map((step, i) => <div className="trace-step" key={step.label}><div className={`trace-icon ${step.color}`}><step.icon className="size-4" /></div><div className="trace-copy"><div>{step.label}</div><span>{step.meta}</span></div>{i < traceSteps.length - 1 && <div className="trace-connector" />}</div>)}</div><div className="trace-footer"><div><span className="footer-label">MODEL</span><strong>gpt-4.1-mini</strong></div><div><span className="footer-label">TOKENS</span><strong>1,842</strong></div><div><span className="footer-label">COST EST.</span><strong>$0.014</strong></div></div></section>
        </div>
        <div className="lower-grid"><section className="panel table-panel"><div className="panel-header"><div><div className="panel-kicker"><Network className="size-3.5" /> CONNECTORS</div><h2>Tool registry</h2></div><button className="text-button"><Plus className="size-3.5" /> Add connector</button></div><div className="tool-table"><div className="table-row table-head"><span>Tool</span><span>Interface</span><span>Permission</span><span>Status</span></div>{toolRows.map(tool => <div className="table-row" key={tool.name}><span className="tool-name"><span className="tool-symbol">⌘</span>{tool.name}</span><span className="muted-cell">{tool.type}</span><span><Badge variant="outline" className={`role-badge ${tool.role === "admin" ? "role-admin" : ""}`}>{tool.role}</Badge></span><span className={tool.status === "Ready" ? "ready-cell" : "restricted-cell"}><span className="status-dot" />{tool.status}</span></div>)}</div></section><section className="panel health-panel"><div className="panel-header"><div><div className="panel-kicker"><ShieldCheck className="size-3.5" /> SYSTEM HEALTH</div><h2>Service health</h2></div><button className="text-button">Details <ArrowUpRight className="size-3.5" /></button></div><div className="health-list"><div><div className="health-service"><span className="status-dot" /> API gateway</div><span className="health-latency">42ms</span></div><div><div className="health-service"><span className="status-dot" /> PostgreSQL + pgvector</div><span className="health-latency">18ms</span></div><div><div className="health-service"><span className="status-dot" /> MCP connector</div><span className="health-latency">67ms</span></div><div><div className="health-service warning"><span className="status-dot warning-dot" /> Evaluation worker</div><span className="health-latency warning-text">degraded</span></div></div><div className="health-foot"><span>Uptime SLA</span><strong>99.98%</strong><span className="sla-bar"><i /></span></div></section></div>
        <div className="bottom-note"><LifeBuoy className="size-4" /><span>Need to debug a run? Trace data is retained for 30 days.</span><button>Open documentation <ArrowUpRight className="size-3.5" /></button></div>
      </div>
    </main>
  </div>;
}
