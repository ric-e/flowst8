import * as vscode from 'vscode';
import WebSocket from 'ws';

const RECONNECT_DELAY_MS = 3000;

export class WebSockClient implements vscode.Disposable {
  private socket: WebSocket | undefined;
  private reconnectTimer: ReturnType<typeof setTimeout> | undefined;
  private closedByUser = false;

  constructor(
    private readonly url: string,
    private readonly output: vscode.OutputChannel,
  ) {
    this.connect();
  }

  private connect(): void {
    this.socket = new WebSocket(this.url);

    this.socket.on('open', () => {
      this.output.appendLine(`Connected to backend at ${this.url}`);
    });

    this.socket.on('close', () => {
      if (!this.closedByUser) {
        this.output.appendLine('Backend connection lost — retrying in 3s');
        this.scheduleReconnect();
      }
    });

    this.socket.on('error', (err: Error) => {
      this.output.appendLine(`WebSocket error: ${err.message}`);
    });
  }

  private scheduleReconnect(): void {
    clearTimeout(this.reconnectTimer);
    this.reconnectTimer = setTimeout(() => this.connect(), RECONNECT_DELAY_MS);
  }

  /** Sends one aggregate sample. Drops it silently if the socket isn't
   * currently open — the next periodic flush from KeystrokeTracker tries
   * again in a few seconds, so there's no queue to manage here. */
  send<T>(payload: T): void {
    if (this.socket?.readyState === WebSocket.OPEN) {
      this.socket.send(JSON.stringify(payload));
    }
  }

  dispose(): void {
    this.closedByUser = true;
    clearTimeout(this.reconnectTimer);
    this.socket?.close();
  }
}