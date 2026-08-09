import { motion } from 'framer-motion';
import { Brain, Search, Tag, FileText, Send } from 'lucide-react';
import type { FeedbackSubmitData } from '../types';
import { useEffect, useState } from 'react';

interface SubmittingPageProps {
  data: FeedbackSubmitData | null;
}

const steps = [
  { icon: Send, label: '正在提交您的反馈', duration: 600 },
  { icon: Search, label: 'AI分析语义内容', duration: 800 },
  { icon: Tag, label: '自动识别问题类型与优先级', duration: 800 },
  { icon: FileText, label: '生成工单号并通知负责人', duration: 600 },
];

export default function SubmittingPage({ data }: SubmittingPageProps) {
  const [currentStep, setCurrentStep] = useState(0);

  useEffect(() => {
    let elapsed = 0;
    const timers: ReturnType<typeof setTimeout>[] = [];

    steps.forEach((step, i) => {
      elapsed += step.duration;
      timers.push(setTimeout(() => setCurrentStep(i + 1), elapsed - 300));
    });

    return () => timers.forEach(clearTimeout);
  }, []);

  return (
    <div className="flex-1 flex flex-col items-center justify-center px-8">
      {/* AI Brain Animation */}
      <motion.div
        initial={{ scale: 0 }}
        animate={{ scale: 1 }}
        transition={{ type: 'spring', stiffness: 200, damping: 15 }}
        className="relative mb-8"
      >
        {/* Pulse ring */}
        <div className="absolute inset-0 w-28 h-28 rounded-full bg-neolix-500/20 animate-pulse-ring" />
        <div className="absolute inset-0 w-28 h-28 rounded-full bg-neolix-500/10" style={{ animationDelay: '0.5s' }} />

        {/* Main circle */}
        <div className="relative w-28 h-28 bg-gradient-to-br from-neolix-500 to-neolix-700 rounded-full flex items-center justify-center shadow-2xl shadow-neolix-500/30">
          <motion.div
            animate={{ rotate: 360 }}
            transition={{ duration: 2, repeat: Infinity, ease: 'linear' }}
            className="absolute inset-2 rounded-full border-2 border-dashed border-white/30"
          />
          <Brain className="w-12 h-12 text-white" />
        </div>
      </motion.div>

      {/* Scanning line effect */}
      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ delay: 0.3 }}
        className="relative w-64 h-2 bg-neolix-100 rounded-full overflow-hidden mb-8"
      >
        <motion.div
          animate={{ x: ['-100%', '0%'] }}
          transition={{ duration: 1.5, repeat: Infinity, ease: 'easeInOut' }}
          className="absolute inset-y-0 w-1/3 bg-gradient-to-r from-transparent via-neolix-500 to-transparent rounded-full"
        />
      </motion.div>

      {/* Steps */}
      <div className="w-full max-w-xs space-y-3">
        {steps.map((step, i) => {
          const isActive = i <= currentStep;
          const isCurrent = i === currentStep;
          const Icon = step.icon;

          return (
            <motion.div
              key={i}
              initial={{ opacity: 0, x: -20 }}
              animate={{ opacity: isActive ? 1 : 0.4, x: 0 }}
              transition={{ delay: i * 0.15 }}
              className="flex items-center gap-3"
            >
              <div className={`w-8 h-8 rounded-full flex items-center justify-center transition-colors ${
                isCurrent ? 'bg-neolix-500 text-white shadow-lg shadow-neolix-500/30' :
                isActive ? 'bg-green-500 text-white' : 'bg-gray-200 text-gray-400'
              }`}>
                {i < currentStep ? (
                  <motion.svg
                    initial={{ scale: 0 }}
                    animate={{ scale: 1 }}
                    className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor"
                  >
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={3} d="M5 13l4 4L19 7" />
                  </motion.svg>
                ) : (
                  <Icon className="w-4 h-4" />
                )}
              </div>
              <span className={`text-sm transition-colors ${
                isCurrent ? 'text-neolix-700 font-semibold' :
                isActive ? 'text-gray-700' : 'text-gray-400'
              }`}>
                {step.label}
              </span>
              {isCurrent && (
                <motion.span
                  animate={{ opacity: [0.3, 1, 0.3] }}
                  transition={{ duration: 0.8, repeat: Infinity }}
                  className="text-neolix-500"
                >
                  ...
                </motion.span>
              )}
            </motion.div>
          );
        })}
      </div>

      {/* Content preview */}
      {data && (
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 0.6, y: 0 }}
          transition={{ delay: 0.5 }}
          className="mt-8 bg-white/60 backdrop-blur rounded-xl p-3 w-full max-w-xs"
        >
          <p className="text-xs text-gray-500 mb-1">您的反馈：</p>
          <p className="text-sm text-gray-700 line-clamp-2">"{data.content_raw.slice(0, 50)}{data.content_raw.length > 50 ? '...' : ''}"</p>
        </motion.div>
      )}
    </div>
  );
}
