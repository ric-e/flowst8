import * as vscode from 'vscode';
import { randomUUID } from 'node:crypto';
import { WebSockClient } from './websockClient';
import { KeystrokeTracker } from './keystrokeTracker';
import { FocusReaderPanel } from './focusReaderPanel';

const DEFAULT_BACKEND_URL = 'ws://127.0.0.1:8000';

export function activate(context: vscode.ExtensionContext): void {
  const output = vscode.window.createOutputChannel('Flow Assistant');
  context.subscriptions.push(output);


  const sessionId = randomUUID()
  output.appendLine(`Starting flow session ${sessionId}`);

  const backendUrl = vscode.workspace
    .getConfiguration('flowAssistant')
    .get<string>('backendUrl', DEFAULT_BACKEND_URL);

  const wsClient = new WebSockClient(`${backendUrl}/ws/keystrokes/${sessionId}`, output);
  context.subscriptions.push(wsClient);

  const tracker = new KeystrokeTracker((payload) => wsClient.send(payload));
  context.subscriptions.push(tracker);

  const focusReaderCommand = vscode.commands.registerCommand(
    'flowAssistant.openFocusReader',
    () => {
      FocusReaderPanel.render(context.extensionUri);
    }
  );
  context.subscriptions.push(focusReaderCommand);
}

export function deactivate(): void {
  // Everything is registered in context.subscriptions, so VS Code disposes the tracker and socket automatically
}