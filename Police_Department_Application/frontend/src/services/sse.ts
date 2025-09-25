/**
 * SSE (Server-Sent Events) Service
 * Handles real-time communication with the backend
 */

import { IncidentSummary, Incident } from '../types/incident';

export type SSEEventType = 
  | 'connected'
  | 'heartbeat'
  | 'incident_created'
  | 'incident_updated' 
  | 'incident_acknowledged'
  | 'stats_updated'
  | 'system_status'
  | 'error';

export interface SSEEvent {
  type: SSEEventType;
  data?: any;
  message?: string;
  timestamp: string;
  [key: string]: any;
}

export type SSEEventHandler = (event: SSEEvent) => void;

class SSEService {
  private eventSource: EventSource | null = null;
  private reconnectAttempts = 0;
  private maxReconnectAttempts = 5;
  private reconnectDelay = 1000; // Start with 1 second
  private isConnected = false;
  private handlers: Map<SSEEventType, Set<SSEEventHandler>> = new Map();

  constructor() {
    // Initialize handler sets for all event types
    const eventTypes: SSEEventType[] = [
      'connected', 'heartbeat', 'incident_created', 'incident_updated',
      'incident_acknowledged', 'stats_updated', 'system_status', 'error'
    ];
    
    eventTypes.forEach(type => {
      this.handlers.set(type, new Set());
    });
  }

  /**
   * Connect to SSE stream
   */
  connect(): void {
    if (this.eventSource && this.eventSource.readyState === EventSource.OPEN) {
      console.log('SSE already connected');
      return;
    }

    try {
      console.log('Connecting to SSE stream...');
      
      // Create EventSource connection
      this.eventSource = new EventSource('/api/v1/stream');

      // Handle connection open
      this.eventSource.onopen = (event) => {
        console.log('SSE connection established');
        this.isConnected = true;
        this.reconnectAttempts = 0;
        this.reconnectDelay = 1000;
      };

      // Handle generic messages
      this.eventSource.onmessage = (event) => {
        this.handleEvent(event);
      };

      // Handle connection errors
      this.eventSource.onerror = (event) => {
        console.error('SSE connection error:', event);
        this.isConnected = false;
        
        if (this.eventSource?.readyState === EventSource.CLOSED) {
          this.handleReconnect();
        }
      };

      // Handle specific event types
      this.setupEventHandlers();

    } catch (error) {
      console.error('Failed to establish SSE connection:', error);
      this.handleReconnect();
    }
  }

  /**
   * Disconnect from SSE stream
   */
  disconnect(): void {
    if (this.eventSource) {
      console.log('Disconnecting SSE stream...');
      this.eventSource.close();
      this.eventSource = null;
      this.isConnected = false;
    }
  }

  /**
   * Check if SSE is connected
   */
  isSSEConnected(): boolean {
    return this.isConnected && this.eventSource?.readyState === EventSource.OPEN;
  }

  /**
   * Add event listener for specific event type
   */
  addEventListener(eventType: SSEEventType, handler: SSEEventHandler): void {
    const handlers = this.handlers.get(eventType);
    if (handlers) {
      handlers.add(handler);
    }
  }

  /**
   * Remove event listener
   */
  removeEventListener(eventType: SSEEventType, handler: SSEEventHandler): void {
    const handlers = this.handlers.get(eventType);
    if (handlers) {
      handlers.delete(handler);
    }
  }

  /**
   * Remove all event listeners for a specific type
   */
  removeAllListeners(eventType?: SSEEventType): void {
    if (eventType) {
      this.handlers.get(eventType)?.clear();
    } else {
      this.handlers.forEach(handlers => handlers.clear());
    }
  }

  /**
   * Setup event handlers for different event types
   */
  private setupEventHandlers(): void {
    if (!this.eventSource) return;

    // Handle specific event types
    const eventTypes: SSEEventType[] = [
      'connected', 'heartbeat', 'incident_created', 'incident_updated',
      'incident_acknowledged', 'stats_updated', 'system_status', 'error'
    ];

    eventTypes.forEach(eventType => {
      this.eventSource!.addEventListener(eventType, (event) => {
        this.handleTypedEvent(eventType, event as MessageEvent);
      });
    });
  }

  /**
   * Handle generic SSE event
   */
  private handleEvent(event: MessageEvent): void {
    try {
      const data = JSON.parse(event.data);
      const sseEvent: SSEEvent = {
        type: data.type || 'message',
        ...data
      };
      
      this.notifyHandlers(sseEvent.type, sseEvent);
    } catch (error) {
      console.error('Failed to parse SSE event:', error, event.data);
    }
  }

  /**
   * Handle typed SSE event
   */
  private handleTypedEvent(eventType: SSEEventType, event: MessageEvent): void {
    try {
      const data = JSON.parse(event.data);
      const sseEvent: SSEEvent = {
        type: eventType,
        ...data
      };
      
      // Log important events
      if (eventType !== 'heartbeat') {
        console.log(`SSE ${eventType}:`, sseEvent);
      }
      
      this.notifyHandlers(eventType, sseEvent);
    } catch (error) {
      console.error(`Failed to parse SSE ${eventType} event:`, error, event.data);
    }
  }

  /**
   * Notify all handlers for an event type
   */
  private notifyHandlers(eventType: SSEEventType, event: SSEEvent): void {
    const handlers = this.handlers.get(eventType);
    if (handlers) {
      handlers.forEach(handler => {
        try {
          handler(event);
        } catch (error) {
          console.error(`Error in SSE event handler for ${eventType}:`, error);
        }
      });
    }
  }

  /**
   * Handle reconnection logic
   */
  private handleReconnect(): void {
    if (this.reconnectAttempts >= this.maxReconnectAttempts) {
      console.error('Max SSE reconnection attempts reached');
      return;
    }

    this.reconnectAttempts++;
    
    console.log(`SSE reconnecting in ${this.reconnectDelay}ms (attempt ${this.reconnectAttempts}/${this.maxReconnectAttempts})`);
    
    setTimeout(() => {
      this.connect();
    }, this.reconnectDelay);

    // Exponential backoff
    this.reconnectDelay = Math.min(this.reconnectDelay * 2, 30000);
  }

  /**
   * Get connection statistics
   */
  getConnectionInfo() {
    return {
      connected: this.isConnected,
      readyState: this.eventSource?.readyState,
      reconnectAttempts: this.reconnectAttempts,
      url: this.eventSource?.url
    };
  }
}

// Export singleton instance
export const sseService = new SSEService();
export default sseService;
