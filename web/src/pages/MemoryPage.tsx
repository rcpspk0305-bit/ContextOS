import { useState } from 'react';
import { MemoryRecord, MemoryType } from '@/types/memory';
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Input } from '@/components/ui/input';
import {
  Database,
  Search,
  Plus,
  Brain,
  AlertOctagon,
  FileCheck,
  Code2,
  Bookmark,
  Check,
} from 'lucide-react';
import { formatTimeAgo } from '@/lib/utils';

export function MemoryPage({ memories }: { memories: MemoryRecord[] }) {
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedType, setSelectedType] = useState<string>('ALL');

  const types: MemoryType[] = ['semantic', 'episodic', 'decision', 'task', 'failure', 'code_reference'];

  const filteredMemories = memories.filter((m) => {
    const matchesSearch =
      m.title.toLowerCase().includes(searchQuery.toLowerCase()) ||
      m.content.toLowerCase().includes(searchQuery.toLowerCase()) ||
      m.summary.toLowerCase().includes(searchQuery.toLowerCase());
    const matchesType = selectedType === 'ALL' || m.type === selectedType;
    return matchesSearch && matchesType;
  });

  const getTypeIcon = (type: MemoryType) => {
    switch (type) {
      case 'decision':
        return <Bookmark className="w-3.5 h-3.5 text-primary" />;
      case 'failure':
        return <AlertOctagon className="w-3.5 h-3.5 text-red-400" />;
      case 'semantic':
        return <Brain className="w-3.5 h-3.5 text-purple-400" />;
      case 'task':
        return <FileCheck className="w-3.5 h-3.5 text-emerald-400" />;
      case 'code_reference':
      default:
        return <Code2 className="w-3.5 h-3.5 text-sky-400" />;
    }
  };

  return (
    <div className="flex-1 p-6 space-y-6 overflow-y-auto">
      {/* Top action header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-2 border-b border-border/60">
        <div>
          <h1 className="text-xl font-bold tracking-tight text-foreground flex items-center gap-2">
            Persistent Memory Engine
            <span className="text-xs font-mono font-medium px-2 py-0.5 rounded bg-purple-500/10 text-purple-400 border border-purple-500/20">
              {memories.length} Stored Records
            </span>
          </h1>
          <p className="text-xs text-muted-foreground mt-0.5">
            Durable project knowledge: semantic facts, architectural decisions (ADRs), failure modes, and code references.
          </p>
        </div>

        <Button size="sm" className="text-xs gap-1.5 bg-primary text-primary-foreground">
          <Plus className="w-3.5 h-3.5" />
          <span>Record ADR</span>
        </Button>
      </div>

      {/* Search Bar & Type Filter */}
      <div className="flex flex-col sm:flex-row items-center gap-3">
        <div className="relative flex-1 w-full">
          <Search className="w-4 h-4 text-muted-foreground absolute left-3 top-2.5" />
          <Input
            placeholder="Search semantic memory, architectural decisions, or failure patterns..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="pl-9 h-9 text-xs"
          />
        </div>

        <div className="flex items-center gap-1 overflow-x-auto text-xs w-full sm:w-auto">
          <button
            onClick={() => setSelectedType('ALL')}
            className={`px-3 py-1.5 rounded-lg font-medium transition-colors cursor-pointer text-xs ${
              selectedType === 'ALL'
                ? 'bg-primary text-primary-foreground shadow-sm'
                : 'bg-secondary/60 text-muted-foreground hover:text-foreground'
            }`}
          >
            All ({memories.length})
          </button>
          {types.map((t) => (
            <button
              key={t}
              onClick={() => setSelectedType(t)}
              className={`px-2.5 py-1.5 rounded-lg font-medium transition-colors cursor-pointer font-mono text-[11px] capitalize ${
                selectedType === t
                  ? 'bg-primary text-primary-foreground shadow-sm'
                  : 'bg-secondary/60 text-muted-foreground hover:text-foreground'
              }`}
            >
              {t.replace('_', ' ')}
            </button>
          ))}
        </div>
      </div>

      {/* Memories Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {filteredMemories.map((m) => (
          <Card key={m.id} className="p-4 flex flex-col justify-between hover:border-primary/40 transition-colors shadow-sm">
            <div className="space-y-2 text-xs">
              <div className="flex items-start justify-between gap-2">
                <div className="flex items-center gap-2">
                  <div className="p-1 rounded bg-secondary text-primary">
                    {getTypeIcon(m.type)}
                  </div>
                  <h3 className="font-semibold text-foreground text-sm leading-tight">{m.title}</h3>
                </div>
                <Badge variant="outline" className="font-mono text-[10px] uppercase">{m.type}</Badge>
              </div>

              <p className="text-muted-foreground leading-relaxed pt-1">{m.content}</p>
            </div>

            <div className="flex items-center justify-between pt-3 mt-3 border-t border-border/50 text-[10px] font-mono text-muted-foreground">
              <span>Source: <strong className="text-foreground">{m.source}</strong></span>
              <div className="flex items-center gap-3">
                <span>Importance: <strong className="text-primary">{m.importance}/10</strong></span>
                <span>Accessed: {formatTimeAgo(m.last_accessed_at)}</span>
              </div>
            </div>
          </Card>
        ))}
      </div>
    </div>
  );
}
