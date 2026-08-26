import { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Bug, X, Trash2, ChevronUp, ChevronDown, Wifi, WifiOff, ServerCrash, Clock, CheckCircle2 } from 'lucide-react';
import { logger, type LogEntry, type LogLevel } from '../utils/logger';
import { setMockMode, getMockMode, type MockMode } from '../api';

const levelColors: Record<LogLevel, { dot: string; text: string; bg: string }> = {
  info: { dot: 'bg-blue-500', text: 'text-blue-300', bg: 'bg-blue-500/10' },
  success: { dot: 'bg-green-500', text: 'text-green-300', bg: 'bg-green-500/10' },
  warn: { dot: 'bg-yellow-500', text: 'text-yellow-300', bg: 'bg-yellow-500/10' },
  error: { dot: 'bg-red-500', text: 'text-red-300', bg: 'bg-red-500/10' },
};

const mockModes: { mode: MockMode; label: string; icon: typeof Wifi; color: string }[] = [
  { mode: 'success', label: '成功', icon: CheckCircle2, color: 'text-green-400 border-green-400/40 bg-green-400/10' },
  { mode: 'network_error', label: '断网', icon: WifiOff, color: 'text-red-400 border-red-400/40 bg-red-400/10' },
  { mode: 'server_error', label: '500', icon: ServerCrash, color: 'text-orange-400 border-orange-400/40 bg-orange-400/10' },
  { mode: 'timeout', label: '超时', icon: Clock, color: 'text-yellow-400 border-yellow-400/40 bg-yellow-400/10' },
];

export default function DebugPanel() {
  const [visible, setVisible] = useState(false);
  const [expanded, setExpanded] = useState(false);
  const [logs, setLogs] = useState<LogEntry[]>([]);
  const [currentMock, setCurrentMock] = useState<MockMode>('success');

  useEffect(() => {
    const unsub = logger.subscribe(setLogs);
    setCurrentMock(getMockMode());
    return unsub;
  }, []);

  const handleMockChange = (mode: MockMode) => {
    setMockMode(mode);
    setCurrentMock(mode);
  };

  const recentLogs = logs.slice(-30);
  const errorCount = logs.filter(l => l.level === 'error').length;
  const warnCount = logs.filter(l => l.level === 'warn').length;
  const badgeCount = errorCount + warnCount;

  return (
    <>
      {/* Toggle Button */}
      <button
        onClick={() => setVisible(!visible)}
        className="absolute bottom-4 right-4 z-50 w-11 h-11 bg-gray-900/80 backdrop-blur text-white rounded-full shadow-lg flex items-center justify-center active:scale-90 transition-transform touch-target"
        style={{ touchAction: 'manipulation' }}
      >
        <Bug className="w-5 h-5" />
        {badgeCount > 0 && (
          <span className="absolute -top-1 -right-1 w-5 h-5 bg-red-500 text-white text-[10px] rounded-full flex items-center justify-center font-bold">
            {badgeCount}
          </span>
        )}
      </button>

      {/* Panel */}
      <AnimatePresence>
        {visible && (
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: 20 }}
            className="absolute bottom-20 right-2 left-2 z-50 bg-gray-900/95 backdrop-blur rounded-2xl shadow-2xl text-white overflow-hidden"
            style={{ maxHeight: expanded ? '70vh' : '45vh' }}
          >
            {/* Header */}
            <div className="flex items-center justify-between px-4 py-2.5 border-b border-white/10">
              <div className="flex items-center gap-2">
                <Bug className="w-4 h-4" />
                <span className="text-sm font-semibold">调试面板</span>
                <span className="text-[10px] text-white/40">{logs.length} 条日志</span>
              </div>
              <div className="flex items-center gap-1">
                <button
                  onClick={() => logger.clear()}
                  className="p-1.5 hover:bg-white/10 rounded-lg"
                  title="清空日志"
                >
                  <Trash2 className="w-4 h-4" />
                </button>
                <button
                  onClick={() => setExpanded(!expanded)}
                  className="p-1.5 hover:bg-white/10 rounded-lg"
                  title={expanded ? '收起' : '展开'}
                >
                  {expanded ? <ChevronDown className="w-4 h-4" /> : <ChevronUp className="w-4 h-4" />}
                </button>
                <button
                  onClick={() => setVisible(false)}
                  className="p-1.5 hover:bg-white/10 rounded-lg"
                  title="关闭"
                >
                  <X className="w-4 h-4" />
                </button>
              </div>
            </div>

            {/* Mock Mode Selector */}
            <div className="px-4 py-2 border-b border-white/10 bg-white/[0.02]">
              <div className="flex items-center gap-1.5">
                <span className="text-[10px] text-white/40 mr-1">模拟模式:</span>
                {mockModes.map(({ mode, label, icon: Icon, color }) => (
                  <button
                    key={mode}
                    onClick={() => handleMockChange(mode)}
                    className={`flex items-center gap-1 px-2 py-1 rounded-md text-[11px] border transition-all ${
                      currentMock === mode
                        ? color + ' border-current font-semibold'
                        : 'text-white/50 border-white/10 hover:border-white/30'
                    }`}
                  >
                    <Icon className="w-3 h-3" />
                    <span>{label}</span>
                  </button>
                ))}
              </div>
            </div>

            {/* Logs */}
            <div className="overflow-y-auto px-3 py-2 space-y-1" style={{ maxHeight: expanded ? 'calc(70vh - 100px)' : 'calc(45vh - 100px)' }}>
              {recentLogs.length === 0 && (
                <p className="text-white/30 text-xs text-center py-6">暂无日志，操作页面后会在此显示</p>
              )}
              {recentLogs.map(log => {
                const c = levelColors[log.level];
                return (
                  <div key={log.id} className={`${c.bg} rounded-lg px-3 py-1.5 text-xs`}>
                    <div className="flex items-start gap-2">
                      <span className={`w-1.5 h-1.5 rounded-full ${c.dot} mt-1.5 flex-shrink-0`} />
                      <div className="flex-1 min-w-0">
                        <div className="flex items-center gap-2">
                          <span className="text-white/30 font-mono text-[10px]">{log.time}</span>
                          <span className={`font-semibold ${c.text}`}>[{log.module}]</span>
                        </div>
                        <p className={`${c.text} mt-0.5 break-words leading-relaxed`}>{log.message}</p>
                        {log.data !== undefined && (
                          <pre className="text-white/50 text-[10px] mt-1 whitespace-pre-wrap break-all font-mono leading-relaxed">
                            {typeof log.data === 'object' ? JSON.stringify(log.data, null, 2).slice(0, 500) : String(log.data)}
                          </pre>
                        )}
                      </div>
                    </div>
                  </div>
                );
              })}
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </>
  );
}
