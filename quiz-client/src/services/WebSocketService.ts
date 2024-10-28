import EventEmitter from 'eventemitter3';

export class WebSocketService extends EventEmitter {
  private ws: WebSocket | null = null;
  private reconnectAttempts = 0;
  private pingInterval: NodeJS.Timeout | null = null;
  private readonly MAX_RECONNECT_ATTEMPTS = 5;
  private isConnecting = false;

  constructor(
    private readonly url: string,
    private readonly options: {
      pingInterval?: number;
      reconnectDelay?: number;
    } = {}
  ) {
    super();
    this.options = {
      pingInterval: 30000,
      reconnectDelay: 3000,
      ...options,
    };
  }

  public connect(): void {
    if (this.isConnecting || this.ws?.readyState === WebSocket.OPEN) {
      console.log('[WS] Connection already in progress or established');
      return;
    }

    this.isConnecting = true;
    console.log('[WS] Connecting to:', this.url);

    try {
      this.ws = new WebSocket(this.url);

      this.ws.onopen = this.handleOpen.bind(this);
      this.ws.onclose = this.handleClose.bind(this);
      this.ws.onmessage = this.handleMessage.bind(this);
      this.ws.onerror = this.handleError.bind(this);

      // Set connection timeout
      setTimeout(() => {
        if (this.ws?.readyState === WebSocket.CONNECTING) {
          console.log('[WS] Connection timeout');
          this.ws.close();
        }
      }, 5000);

    } catch (error) {
      console.error('[WS] Connection error:', error);
      this.handleClose();
    }
  }

  public disconnect(): void {
    if (this.ws) {
      this.ws.close(1000, 'Normal closure');
      this.cleanup();
    }
  }

  public send(data: any): boolean {
    if (this.ws?.readyState === WebSocket.OPEN) {
      try {
        this.ws.send(JSON.stringify(data));
        return true;
      } catch (error) {
        console.error('[WS] Send error:', error);
        return false;
      }
    }
    return false;
  }

  private handleOpen(): void {
    console.log('[WS] Connected');
    this.isConnecting = false;
    this.reconnectAttempts = 0;
    this.startPingInterval();
    this.emit('connected');
  }

  private handleClose(event?: CloseEvent): void {
    this.cleanup();
    this.emit('disconnected');

    if (event?.code !== 1000) {
      this.scheduleReconnect();
    }
  }

  private handleMessage(event: MessageEvent): void {
    try {
      const data = JSON.parse(event.data);
      if (data.type === 'pong') {
        console.debug('[WS] Received pong');
        return;
      }
      console.debug('[WS] Received message:', data);
      this.emit('message', data);
    } catch (error) {
      console.error('[WS] Message parsing error:', error);
    }
  }

  private handleError(error: Event): void {
    console.error('[WS] Error:', error);
    this.emit('error', error);
  }

  private cleanup(): void {
    this.isConnecting = false;
    if (this.pingInterval) {
      clearInterval(this.pingInterval);
      this.pingInterval = null;
    }
    if (this.ws) {
      this.ws.onopen = null;
      this.ws.onclose = null;
      this.ws.onmessage = null;
      this.ws.onerror = null;
      this.ws = null;
    }
  }

  private startPingInterval(): void {
    if (this.pingInterval) {
      clearInterval(this.pingInterval);
    }
    this.pingInterval = setInterval(() => {
      if (this.ws?.readyState === WebSocket.OPEN) {
        this.send({ type: 'ping' });
      }
    }, this.options.pingInterval);
  }

  private scheduleReconnect(): void {
    if (this.reconnectAttempts >= this.MAX_RECONNECT_ATTEMPTS) {
      console.log('[WS] Max reconnection attempts reached');
      return;
    }

    const delay = Math.min(
      1000 * Math.pow(2, this.reconnectAttempts),
      10000
    );

    console.log(`[WS] Reconnecting in ${delay}ms (attempt ${this.reconnectAttempts + 1})`);
    setTimeout(() => {
      this.reconnectAttempts++;
      this.connect();
    }, delay);
  }
}