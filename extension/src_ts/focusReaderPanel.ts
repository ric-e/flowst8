import * as vscode from 'vscode';

export class FocusReaderPanel {

  public static currentPanel: FocusReaderPanel | undefined;

  public static readonly viewType = 'focusReader';

  private readonly _panel: vscode.WebviewPanel;
  private _disposables: vscode.Disposable[] = [];

  public static render(extensionUri: vscode.Uri) {
    const column = vscode.window.activeTextEditor
      ? vscode.window.activeTextEditor.viewColumn
      : undefined;


    if (FocusReaderPanel.currentPanel) {
      FocusReaderPanel.currentPanel._panel.reveal(column);
      return;
    }


    const panel = vscode.window.createWebviewPanel(
      FocusReaderPanel.viewType,
      'Focus Reader',
      column || vscode.ViewColumn.One,
      {

        enableScripts: true,

        localResourceRoots: [vscode.Uri.joinPath(extensionUri, 'media')]
      }
    );

    FocusReaderPanel.currentPanel = new FocusReaderPanel(panel, extensionUri);
  }

  private constructor(panel: vscode.WebviewPanel, extensionUri: vscode.Uri) {
    this._panel = panel;

    // Set the webview's initial html content
    this._update();


    this._panel.onDidDispose(() => this.dispose(), null, this._disposables);
  }

  public dispose() {
    FocusReaderPanel.currentPanel = undefined;


    this._panel.dispose();

    while (this._disposables.length) {
      const x = this._disposables.pop();
      if (x) {
        x.dispose();
      }
    }
  }

  private _update() {
    const webview = this._panel.webview;
    this._panel.webview.html = this._getHtmlForWebview(webview);
  }

  private _getHtmlForWebview(webview: vscode.Webview) {

    return `<!DOCTYPE html>
      <html lang="en">
      <head>
          <meta charset="UTF-8">
          <meta name="viewport" content="width=device-width, initial-scale=1.0">
          <title>Focus Reader</title>
          <style>
              body {
                  font-family: var(--vscode-font-family);
                  padding: 20px;
                  color: var(--vscode-editor-foreground);
                  background-color: var(--vscode-editor-background);
              }
              h1 {
                  font-weight: 500;
                  margin-bottom: 20px;
              }
          </style>
      </head>
      <body>
          <h1>Flow Assistant: Focus Reader</h1>
          <p>Your agent's focus data will appear here.</p>
          
          <script>
            // This script allows you to handle messages sent from the extension to the webview
            const vscode = acquireVsCodeApi();
            
            window.addEventListener('message', event => {
                const message = event.data; // The JSON data our extension sent
                // Handle messages here when you start sending data to the UI
            });
          </script>
      </body>
      </html>`;
  }
}