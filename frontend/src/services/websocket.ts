import type { EventCategoryType, PayguardEvent } from '../types';

export type WebSocketStatus = 'CONNECTING' | 'CONNECTED' | 'RECONNECTING' | 'DISCONNECTED' | 'ERROR';

type EventListener = (event: PayguardEvent) => void;
type StatusListener = (status: WebSocketStatus) => void;

class PayguardWebSocketService {
  private url: string;
  private socket: WebSocket | null = null;
  private status: WebSocketStatus = 'DISCONNECTED';
  private reconnectAttempts = 0;
  private maxReconnectDelay = 15000;
  private reconnectTimer: any = null;
  private heartbeatTimer: any = null;
  private seenEventIds: Set<string> = new Set();
  private maxSeenEvents = 2000;
  private eventHistory: string[] = [];
  private eventListeners: Map<string, Set<EventListener>> = new Map();
  private statusListeners: Set<StatusListener> = new Set();
  private currentSubscriptions: Set<string> = new Set(['all']);

  constructor(url = 'ws://127.0.0.1:8000/ws/events') {
    this.url = url;
  }

  public getStatus(): WebSocketStatus {
    return this.status;
  }

  public connect(): void {
    if (this.socket && (this.socket.readyState === WebSocket.OPEN || this.socket.readyState === WebSocket.CONNECTING)) {
      return;
    }

    this.setStatus(this.reconnectAttempts === 0 ? 'CONNECTING' : 'RECONNECTING');

    try {
      this.socket = new WebSocket(this.url);

      this.socket.onopen = () => {
        this.setStatus('CONNECTED');
        this.reconnectAttempts = 0;
        this.startHeartbeat();

        // Resubscribe if custom categories were selected
        if (this.currentSubscriptions.size > 0 && !this.currentSubscriptions.has('all')) {
          this.sendSubscription(Array.from(this.currentSubscriptions));
        }
      };

      this.socket.onmessage = (event) => {
        if (event.data === 'pong') {
          return;
        }

        try {
          const raw = JSON.parse(event.data);

          // Handle system pongs or subscription confirmations
          if (raw.type === 'pong' || raw.type === 'system.subscription_updated') {
            return;
          }

          const eventId = raw.event_id || raw.id;
          if (eventId) {
            if (this.seenEventIds.has(eventId)) {
              return; // deduplicate
            }
            this.seenEventIds.add(eventId);
            this.eventHistory.push(eventId);
            if (this.eventHistory.length > this.maxSeenEvents) {
              const old = this.eventHistory.shift();
              if (old) this.seenEventIds.delete(old);
            }
          }

          const parsedEvent: PayguardEvent = {
            event_id: eventId || `evt_local_${Date.now()}`,
            event_type: raw.event_type || raw.type || 'unknown',
            category: (raw.category as EventCategoryType) || 'transactions',
            transaction_id: raw.transaction_id || raw.payload?.transaction_id,
            timestamp: raw.timestamp || new Date().toISOString(),
            source: raw.source || 'backend',
            severity: raw.severity || 'INFO',
            payload: raw.payload || raw,
          };

          this.dispatchToListeners(parsedEvent);
        } catch {
          // Plain text or unparseable frame
        }
      };

      this.socket.onclose = () => {
        this.stopHeartbeat();
        this.setStatus('DISCONNECTED');
        this.scheduleReconnect();
      };

      this.socket.onerror = () => {
        this.setStatus('ERROR');
        if (this.socket) {
          this.socket.close();
        }
      };
    } catch {
      this.setStatus('ERROR');
      this.scheduleReconnect();
    }
  }

  public disconnect(): void {
    this.stopHeartbeat();
    clearTimeout(this.reconnectTimer);
    if (this.socket) {
      this.socket.onclose = null;
      this.socket.close();
      this.socket = null;
    }
    this.setStatus('DISCONNECTED');
  }

  public subscribe(
    categories: string[] | string = 'all',
    listener: EventListener
  ): () => void {
    const cats = Array.isArray(categories) ? categories : [categories];

    cats.forEach((cat) => {
      if (!this.eventListeners.has(cat)) {
        this.eventListeners.set(cat, new Set());
      }
      this.eventListeners.get(cat)!.add(listener);
      this.currentSubscriptions.add(cat);
    });

    if (this.socket && this.socket.readyState === WebSocket.OPEN) {
      this.sendSubscription(Array.from(this.currentSubscriptions));
    }

    // Auto-connect if not already running
    if (this.status === 'DISCONNECTED') {
      this.connect();
    }

    return () => {
      cats.forEach((cat) => {
        const listeners = this.eventListeners.get(cat);
        if (listeners) {
          listeners.delete(listener);
          if (listeners.size === 0) {
            this.eventListeners.delete(cat);
            this.currentSubscriptions.delete(cat);
          }
        }
      });
    };
  }

  public onStatusChange(listener: StatusListener): () => void {
    this.statusListeners.add(listener);
    listener(this.status);
    return () => {
      this.statusListeners.delete(listener);
    };
  }

  private setStatus(newStatus: WebSocketStatus): void {
    if (this.status !== newStatus) {
      this.status = newStatus;
      this.statusListeners.forEach((l) => l(newStatus));
    }
  }

  private dispatchToListeners(event: PayguardEvent): void {
    // Deliver to specific category listeners
    const catListeners = this.eventListeners.get(event.category);
    if (catListeners) {
      catListeners.forEach((fn) => fn(event));
    }

    // Deliver to 'all' listeners
    const allListeners = this.eventListeners.get('all');
    if (allListeners) {
      allListeners.forEach((fn) => fn(event));
    }
  }

  private scheduleReconnect(): void {
    clearTimeout(this.reconnectTimer);
    this.reconnectAttempts += 1;
    // Exponential backoff: 1000, 2000, 4000, 8000, max 15000ms
    const delay = Math.min(1000 * Math.pow(2, this.reconnectAttempts - 1), this.maxReconnectDelay);
    this.reconnectTimer = setTimeout(() => {
      this.connect();
    }, delay);
  }

  private startHeartbeat(): void {
    this.stopHeartbeat();
    this.heartbeatTimer = setInterval(() => {
      if (this.socket && this.socket.readyState === WebSocket.OPEN) {
        this.socket.send('ping');
      }
    }, 20000);
  }

  private stopHeartbeat(): void {
    if (this.heartbeatTimer) {
      clearInterval(this.heartbeatTimer);
      this.heartbeatTimer = null;
    }
  }

  private sendSubscription(categories: string[]): void {
    if (this.socket && this.socket.readyState === WebSocket.OPEN) {
      this.socket.send(
        JSON.stringify({
          action: 'subscribe',
          categories,
        })
      );
    }
  }
}

export const payguardWs = new PayguardWebSocketService();
