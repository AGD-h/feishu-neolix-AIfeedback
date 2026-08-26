export type LogLevel = 'info' | 'success' | 'warn' | 'error';

export interface LogEntry {
  id: number;
  time: string;
  level: LogLevel;
  module: string;
  message: string;
  data?: unknown;
}

class Logger {
  private logs: LogEntry[] = [];
  private listeners: ((logs: LogEntry[]) => void)[] = [];
  private counter = 0;

  private add(level: LogLevel, module: string, message: string, data?: unknown) {
    const entry: LogEntry = {
      id: ++this.counter,
      time: new Date().toLocaleTimeString('zh-CN', { hour12: false }),
      level,
      module,
      message,
      data,
    };
    this.logs.push(entry);
    if (this.logs.length > 200) this.logs.shift();

    const prefix = `[${entry.time}] [${module}]`;
    const args = data !== undefined ? [prefix, message, data] : [prefix, message];
    switch (level) {
      case 'info': console.log(...args); break;
      case 'success': console.log('%c' + prefix, 'color: #34a853; font-weight: bold', message, data ?? ''); break;
      case 'warn': console.warn(...args); break;
      case 'error': console.error(...args); break;
    }

    this.listeners.forEach(fn => fn([...this.logs]));
  }

  info(module: string, message: string, data?: unknown) { this.add('info', module, message, data); }
  success(module: string, message: string, data?: unknown) { this.add('success', module, message, data); }
  warn(module: string, message: string, data?: unknown) { this.add('warn', module, message, data); }
  error(module: string, message: string, data?: unknown) { this.add('error', module, message, data); }

  getLogs() { return [...this.logs]; }
  clear() { this.logs = []; this.counter = 0; this.listeners.forEach(fn => fn([])); }

  subscribe(fn: (logs: LogEntry[]) => void) {
    this.listeners.push(fn);
    return () => { this.listeners = this.listeners.filter(l => l !== fn); };
  }
}

export const logger = new Logger();

if (typeof window !== 'undefined') {
  (window as unknown as Record<string, unknown>).__logger = logger;
}
