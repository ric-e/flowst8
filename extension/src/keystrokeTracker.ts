import * as vscode from 'vscode';

export interface KeystrokeAggregate {
  keystrokes_per_min: number;
  backspace_ratio: number;
}

const FLUSH_INTERVAL_MS = 5000;
const PASTE_CHAR_THRESHOLD = 20;

export class KeystrokeTracker implements vscode.Disposable {
  private editCount = 0;
  private backspaceCount = 0;
  private windowStart = Date.now();
  private readonly changeListener: vscode.Disposable;
  private readonly flushTimer: ReturnType<typeof setInterval>;

  constructor(
    private readonly onAggregate: (payload: KeystrokeAggregate) => void,
    private readonly flushIntervalMs: number = FLUSH_INTERVAL_MS,
  ) {
    this.changeListener = vscode.workspace.onDidChangeTextDocument(this.handleChange, this);
    this.flushTimer = setInterval(() => this.flush(), this.flushIntervalMs);
  }

  private handleChange(event: vscode.TextDocumentChangeEvent): void {
    if (event.document.uri.scheme !== 'file') {
      return;
    }

    for (const change of event.contentChanges) {
      const isDeletion = change.text.length === 0 && change.rangeLength > 0;
      const isPasteLike = change.text.length > PASTE_CHAR_THRESHOLD;

      if (isPasteLike) {
        continue;
      }
      if (isDeletion) {
        this.backspaceCount += 1;
        this.editCount += 1;
      } else if (change.text.length > 0) {
        this.editCount += change.text.length;
      }
    }
  }

  private flush(): void {
    const elapsedMinutes = (Date.now() - this.windowStart) / 60000;
    const keystrokesPerMin = elapsedMinutes > 0 ? this.editCount / elapsedMinutes : 0;
    const backspaceRatio = this.editCount > 0 ? this.backspaceCount / this.editCount : 0;

    this.onAggregate({
      keystrokes_per_min: Math.round(keystrokesPerMin * 10) / 10,
      backspace_ratio: Math.round(backspaceRatio * 1000) / 1000,
    });

    this.editCount = 0;
    this.backspaceCount = 0;
    this.windowStart = Date.now();
  }

  dispose(): void {
    this.changeListener.dispose();
    clearInterval(this.flushTimer);
  }
}