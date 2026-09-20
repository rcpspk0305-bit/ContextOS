import { useState } from 'react';
import { MCPTool, MCPConnection } from '@/types/mcp';
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import {
  Radio,
  Search,
  Wrench,
  CheckCircle2,
  Terminal,
  Globe,
  Layers,
  Sparkles,
  ExternalLink,
} from 'lucide-react';
import { formatTimeAgo } from '@/lib/utils';

export function McpPage({
  tools,
  connections,
}: {
  tools: MCPTool[];
  connections: MCPConnection[];
}) {
  const [search, setSearch] = useState('');
  const [selectedCategory, setSelectedCategory] = useState('ALL');

  const categories = ['ALL', 'context', 'memory', 'session', 'agent', 'task', 'git', 'telemetry'];

  const filteredTools = tools.filter((t) => {
    const matchesSearch =
      t.name.toLowerCase().includes(search.toLowerCase()) ||
      t.description.toLowerCase().includes(search.toLowerCase());
    const matchesCat = selectedCategory === 'ALL' || t.category === selectedCategory;
    return matchesSearch && matchesCat;
  });

  return (
    <div className="flex-1 p-6 space-y-6 overflow-y-auto">
      {/* Top Banner */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-2 border-b border-border/60">
        <div>
          <h1 className="text-xl font-bold tracking-tight text-foreground flex items-center gap-2">
            Model Context Protocol (MCP) Server
            <span className="text-xs font-mono font-medium px-2 py-0.5 rounded bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
              Official SDK v2
            </span>
          </h1>
          <p className="text-xs text-muted-foreground mt-0.5">
            Exposes ContextOS context engine, memory, session checkpoints, and agent supervision tools to AGY, Codex, and Claude Code.
          </p>
        </div>

        <div className="flex items-center gap-2 text-xs font-mono">
          <Badge variant="success" className="text-[11px] font-mono">
            FastMCP Streamable HTTP Active
          </Badge>
        </div>
      </div>

      {/* Connected Clients Grid */}
      <div className="space-y-3">
        <h2 className="text-xs font-semibold text-muted-foreground uppercase tracking-wider font-mono">
          Connected Agent Clients
        </h2>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {connections.map((conn) => (
            <Card key={conn.id} className="p-4 flex items-center justify-between shadow-sm">
              <div className="flex items-center gap-3">
                <div className="p-2 rounded-lg bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
                  <Radio className="w-4 h-4 animate-pulse" />
                </div>
                <div>
                  <div className="font-semibold text-sm text-foreground">{conn.client_name}</div>
                  <div className="text-xs text-muted-foreground font-mono mt-0.5">
                    Transport: <strong className="text-foreground">{conn.transport}</strong> • Endpoint: {conn.endpoint}
                  </div>
                </div>
              </div>

              <div className="text-right font-mono text-xs">
                <Badge variant="success" className="text-[10px]">CONNECTED</Badge>
                <div className="text-[10px] text-muted-foreground mt-1">{conn.calls_count} tool calls</div>
              </div>
            </Card>
          ))}
        </div>
      </div>

      {/* Exposed MCP Tools Catalog */}
      <div className="space-y-4 pt-2">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
          <div>
            <h2 className="text-sm font-semibold tracking-tight text-foreground flex items-center gap-2">
              <Wrench className="w-4 h-4 text-primary" />
              <span>Registered Tools ({tools.length})</span>
            </h2>
            <p className="text-xs text-muted-foreground">All inputs and outputs strictly typed with Pydantic v2 schemas.</p>
          </div>

          <div className="flex items-center gap-2">
            <div className="relative">
              <Search className="w-3.5 h-3.5 text-muted-foreground absolute left-2.5 top-2.5" />
              <Input
                placeholder="Search tools..."
                value={search}
                onChange={(e) => setSearch(e.target.value)}
                className="pl-8 h-8 text-xs w-48"
              />
            </div>
          </div>
        </div>

        {/* Category Pills */}
        <div className="flex items-center gap-1.5 overflow-x-auto text-xs pb-1">
          {categories.map((cat) => (
            <button
              key={cat}
              onClick={() => setSelectedCategory(cat)}
              className={`px-2.5 py-1 rounded-md font-mono text-[11px] uppercase transition-colors cursor-pointer ${
                selectedCategory === cat
                  ? 'bg-primary text-primary-foreground font-bold'
                  : 'bg-secondary/60 text-muted-foreground hover:text-foreground'
              }`}
            >
              {cat}
            </button>
          ))}
        </div>

        {/* Tool Cards Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
          {filteredTools.map((tool) => (
            <Card key={tool.name} className="p-3.5 flex flex-col justify-between hover:border-primary/40 transition-colors shadow-sm text-xs">
              <div className="space-y-1.5">
                <div className="flex items-center justify-between">
                  <span className="font-mono font-bold text-sky-400 text-sm">{tool.name}</span>
                  <Badge variant="outline" className="font-mono text-[9px] uppercase">{tool.category}</Badge>
                </div>
                <p className="text-muted-foreground text-[11px] leading-relaxed">{tool.description}</p>
              </div>

              <div className="mt-3 pt-2 border-t border-border/50 font-mono text-[10px] text-muted-foreground">
                Parameters: <span className="text-foreground">{Object.keys(tool.parameters).join(', ') || 'none'}</span>
              </div>
            </Card>
          ))}
        </div>
      </div>
    </div>
  );
}
