import * as vscode from 'vscode';
import { WebSockClient } from './websockClient';
import { KeystrokeTracker } from './keystrokeTracker';

const DEFAULT_BACKEND_URL = 'ws://localhost:8000';

export function activate(context: vscode.ExtensionContext): void {
  const output = vscode.window.createOutputChannel('Flow Assistant');
  context.subscriptions.push(output);

  // One session per activation — a new id each time VS Code (re)loads the
  // extension host. The backend's GET /session/current always reflects
  // whichever session last connected, so the Pi agent picks this one up
  // automatically without any manual coordination.
  const sessionId = crypto.randomUUID();
  output.appendLine(`Starting flow session ${sessionId}`);

  const backendUrl = vscode.workspace
    .getConfiguration('flowAssistant')
    .get<string>('backendUrl', DEFAULT_BACKEND_URL);

  const wsClient = new WebSockClient(`${backendUrl}/ws/keystrokes/${sessionId}`, output);
  context.subscriptions.push(wsClient);

  const tracker = new KeystrokeTracker((payload) => wsClient.send(payload));
  context.subscriptions.push(tracker);

  // TODO: register the focus reader panel command here once
  // focusReaderPanel.ts is built (e.g. flowAssistant.openFocusReader).
}

export function deactivate(): void {
  // Everything is registered in context.subscriptions, so VS Code disposes
  // the tracker and socket automatically — nothing to do here.
}