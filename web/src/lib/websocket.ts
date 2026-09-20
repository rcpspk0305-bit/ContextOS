import { AgentEvent, EventType } from '@/types/agent';
import { INITIAL_EVENTS } from './mock-data';

type EventHandler = (event: AgentEvent) => void;

class RealtimeEventBus {
  private ws: WebSocket | null = null;
  private listeners: Map<EventType | '*', Set<EventHandler>> = new Map();
  private reconnectTimeout: any = null;
  private isConnected: boolean = false;
  private eventHistory: AgentEvent[] = [...INITIAL_EVENTS];

  constructor() {
    this.connect();
  }

  connect() {
    const wsUrl = import.meta.env.VITE_WS_URL || 'ws://localhost:8000/api/events/ws';
    try {
      this.ws = new WebSocket(wsUrl);

      this.ws.onopen = () => {
        this.isConnected = true;
        console.log('[ContextOS WS] Connected to daemon event stream');
      };

      this.ws.onmessage = (msg) => {
        try {
          const event: AgentEvent = JSON.parse(msg.data);
          this.emit(event);
        } catch (e) {
          console.error('[ContextOS WS] Parse error:', e);
        }
      };

      this.ws.onclose = () => {
        this.isConnected = false;
        // Attempt reconnection after 3 seconds
        clearTimeout(this.reconnectTimeout);
        this.reconnectTimeout = setTimeout(() => this.connect(), 3000);
      };

      this.ws.onerror = () => {
        this.isConnected = false;
        this.ws?.close();
      };
    } catch {
      this.isConnected = false;
    }
  }

  subscribe(eventType: EventType | '*', handler: EventHandler): () => void {
    if (!this.listeners.has(eventType)) {
      this.listeners.set(eventType, new Set());
    }
    this.listeners.get(eventType)!.add(handler);

    return () => {
      this.listeners.get(eventType)?.delete(handler);
    };
  }

  emit(event: AgentEvent) {
    this.eventHistory = [event, ...this.eventHistory.slice(0, 99)];

    // Specific listeners
    const specific = this.listeners.get(event.type);
    specific?.forEach((h) => h(event));

    // Catch-all listeners
    const wildcards = this.listeners.get('*');
    wildcards?.forEach((h) => h(event));
  }

  getHistory(): AgentEvent[] {
    return [...this.eventHistory];
  }

  getIsConnected(): boolean {
    return this.isConnected;
  }
}

export const realtime = new RealtimeEventBus();
