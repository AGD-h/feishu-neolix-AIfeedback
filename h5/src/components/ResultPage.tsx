import { motion } from 'framer-motion';
import { CheckCircle, Clock, Copy, Home, Share2, AlertCircle } from 'lucide-react';
import type { FeedbackResult, QRCodeData } from '../types';

interface ResultPageProps {
  result: FeedbackResult;
  qrData: QRCodeData;
  onReset: () => void;
  categoryEmoji: Record<string, string>;
  priorityColors: Record<string, { bg: string; text: string; label: string }>;
}

export default function ResultPage({ result, qrData, onReset, categoryEmoji, priorityColors }: ResultPageProps) {
  const priority = priorityColors[result.priority];
  const emoji = categoryEmoji[result.category] || '📋';

  const copyTicketId = () => {
    navigator.clipboard.writeText(result.ticket_id).catch(() => {});
  };

  return (
    <div className="flex-1 flex flex-col px-5 py-6 overflow-y-auto">
      {/* Success Animation */}
      <motion.div
        initial={{ scale: 0 }}
        animate={{ scale: 1 }}
        transition={{ type: 'spring', stiffness: 200, damping: 15, delay: 0.1 }}
        className="flex flex-col items-center mb-6"
      >
        <div className="relative">
          <div className="w-24 h-24 bg-gradient-to-br from-green-400 to-green-600 rounded-full flex items-center justify-center shadow-xl shadow-green-500/30">
            <svg className="w-12 h-12 text-white" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="3">
              <motion.path
                initial={{ pathLength: 0 }}
                animate={{ pathLength: 1 }}
                transition={{ duration: 0.5, delay: 0.3, ease: 'easeOut' }}
                strokeLinecap="round"
                strokeLinejoin="round"
                d="M5 13l4 4L19 7"
              />
            </svg>
          </div>
          {/* Confetti dots */}
          {[...Array(6)].map((_, i) => (
            <motion.div
              key={i}
              initial={{ scale: 0, x: 0, y: 0 }}
              animate={{
                scale: [0, 1, 0],
                x: Math.cos(i * 60 * Math.PI / 180) * 50,
                y: Math.sin(i * 60 * Math.PI / 180) * 50,
              }}
              transition={{ duration: 0.8, delay: 0.4 }}
              className={`absolute top-1/2 left-1/2 w-2 h-2 rounded-full ${
                ['bg-green-400', 'bg-blue-400', 'bg-yellow-400', 'bg-pink-400', 'bg-purple-400', 'bg-orange-400'][i]
              }`}
              style={{ marginLeft: -4, marginTop: -4 }}
            />
          ))}
        </div>
        <motion.h2
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.3 }}
          className="text-2xl font-bold text-gray-800 mt-4"
        >
          反馈提交成功！
        </motion.h2>
        <motion.p
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 0.5 }}
          className="text-gray-500 text-sm mt-1"
        >
          AI已完成智能分析，工单已自动分派
        </motion.p>
      </motion.div>

      {/* Ticket Card */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.4 }}
        className="bg-white rounded-2xl shadow-lg overflow-hidden mb-4"
      >
        {/* Ticket Header */}
        <div className={`${priority.bg} ${priority.text} px-5 py-3 flex items-center justify-between`}>
          <div className="flex items-center gap-2">
            <AlertCircle className="w-5 h-5" />
            <span className="font-semibold">{priority.label}问题 · {result.priority}</span>
          </div>
          <div className="flex items-center gap-1 text-sm opacity-90">
            <Clock className="w-4 h-4" />
            <span>{result.estimated_response_time}响应</span>
          </div>
        </div>

        <div className="p-5 space-y-4">
          {/* Ticket ID */}
          <div className="flex items-center justify-between">
            <div>
              <p className="text-xs text-gray-400 mb-1">工单编号</p>
              <p className="font-mono text-lg font-bold text-gray-800">{result.ticket_id}</p>
            </div>
            <button
              onClick={copyTicketId}
              className="p-2 hover:bg-gray-100 rounded-lg transition-colors"
            >
              <Copy className="w-5 h-5 text-gray-400" />
            </button>
          </div>

          <div className="border-t border-dashed border-gray-200" />

          {/* Category & Vehicle */}
          <div className="grid grid-cols-2 gap-4">
            <div>
              <p className="text-xs text-gray-400 mb-1">问题类型</p>
              <p className="text-gray-800 font-medium flex items-center gap-1">
                <span>{emoji}</span> {result.category}
              </p>
            </div>
            <div>
              <p className="text-xs text-gray-400 mb-1">关联车辆</p>
              <p className="text-gray-800 font-medium">
                {qrData.vehicle_id !== 'UNKNOWN' ? qrData.vehicle_id : '未关联'}
              </p>
            </div>
          </div>

          {/* AI Summary */}
          <div className="bg-neolix-50 rounded-xl p-3">
            <div className="flex items-center gap-1 text-neolix-600 text-xs font-semibold mb-1">
              <span>🤖</span> AI摘要
            </div>
            <p className="text-sm text-gray-700 leading-relaxed">{result.summary}</p>
          </div>

          {/* Status */}
          <div className="flex items-center gap-2 text-sm">
            <div className="w-2 h-2 bg-blue-500 rounded-full animate-pulse" />
            <span className="text-gray-600">状态：{result.status}，已通知相关负责人</span>
          </div>
        </div>
      </motion.div>

      {/* Info Notice */}
      <motion.div
        initial={{ opacity: 0, y: 10 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.6 }}
        className="bg-blue-50 border border-blue-200 rounded-xl p-4 mb-6"
      >
        <p className="text-sm text-blue-800 leading-relaxed">
          <strong>温馨提示：</strong>您可以保存工单号查询处理进度。紧急问题工作人员将在{result.estimated_response_time}联系您，请保持电话畅通。
        </p>
      </motion.div>

      {/* Action Buttons */}
      <motion.div
        initial={{ opacity: 0, y: 10 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.7 }}
        className="mt-auto space-y-3"
      >
        <button
          onClick={onReset}
          className="w-full bg-gradient-to-r from-neolix-600 to-neolix-500 text-white font-semibold py-4 rounded-2xl shadow-lg shadow-neolix-500/20 flex items-center justify-center gap-2 active:scale-[0.98] transition-transform"
        >
          <Home className="w-5 h-5" />
          <span>返回首页</span>
        </button>
        <div className="flex gap-3">
          <button className="flex-1 bg-white text-gray-600 font-medium py-3 rounded-xl border border-gray-200 flex items-center justify-center gap-1.5 active:scale-[0.98] transition-transform text-sm">
            <Share2 className="w-4 h-4" />
            <span>分享</span>
          </button>
          <button className="flex-1 bg-white text-gray-600 font-medium py-3 rounded-xl border border-gray-200 flex items-center justify-center gap-1.5 active:scale-[0.98] transition-transform text-sm">
            <Copy className="w-4 h-4" />
            <span>复制工单号</span>
          </button>
        </div>
      </motion.div>
    </div>
  );
}
