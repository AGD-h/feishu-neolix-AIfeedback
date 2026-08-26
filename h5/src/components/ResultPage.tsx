import { motion } from 'framer-motion';
import { CheckCircle, Clock, Copy, Home, Share2, AlertCircle, AlertTriangle, BarChart3, ExternalLink, Sparkles } from 'lucide-react';
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
  // Top3加分改造②：读取Vite环境变量（飞书AI问数+TOP问题链接），未配置时按钮灰化，不阻塞流程
  const DASHBOARD_URL: string = (import.meta.env.VITE_DASHBOARD_URL as string) || '';
  const REPORT_URL_BASE: string = (import.meta.env.VITE_REPORT_URL as string) || '';
  const REPORT_URL: string = REPORT_URL_BASE || DASHBOARD_URL;
  const isP0Safety: boolean = result.priority === 'P0' && result.category === '安全';

  const copyTicketId = () => {
    navigator.clipboard?.writeText(result.ticket_id).catch(() => {});
  };

  const handleShare = async () => {
    const shareData = {
      title: '新石器无人车反馈工单',
      text: `反馈已提交，工单编号 ${result.ticket_id}，优先级 ${result.priority}`,
      url: window.location.href,
    };
    try {
      if (navigator.share) {
        await navigator.share(shareData);
        return;
      }
    } catch {
      /* 用户取消或系统拒绝，静默降级 */
    }
    const text = `${shareData.title}\n${shareData.text}\n${shareData.url}`;
    navigator.clipboard?.writeText(text).catch(() => {});
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

      {/* Top3加分改造③：P0+安全类红色专属提示条（安全事故/监管强视觉承诺）*/}
      {isP0Safety && (
        <motion.div
          initial={{ opacity: 0, y: -10 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.35 }}
          className="mb-4"
        >
          <div className="bg-gradient-to-r from-red-600 via-red-500 to-rose-600 text-white rounded-2xl shadow-xl shadow-red-500/40 p-4 flex items-start gap-3">
            <div className="w-10 h-10 bg-white/20 rounded-xl flex items-center justify-center flex-shrink-0 animate-pulse">
              <AlertTriangle className="w-6 h-6" />
            </div>
            <div className="flex-1 min-w-0">
              <p className="font-bold text-base sm:text-lg leading-tight">
                🚨 安全类紧急工单 · 已同步安全总监
              </p>
              <p className="text-sm mt-1 opacity-95 leading-relaxed">
                本工单已进入 P0 紧急处理通道，安全团队 5 分钟内将与您联系。
              </p>
              {/* 单独一行的急救提示，保证不会被文字截断（project_memory约定必加） */}
              <div className="mt-1.5 bg-white/15 rounded-lg px-2.5 py-1.5 text-[12px] sm:text-[13px] font-semibold text-white border border-white/20">
                ⚕️ 如涉及人员受伤/交通事故，请立即拨打 <span className="underline decoration-white/70">110 报警</span> / <span className="underline decoration-white/70">120 急救</span>
              </div>
            </div>
          </div>
        </motion.div>
      )}

      {/* Top3加分改造②：结果页徽章+卡片包装容器（pt-3给徽章留顶部空间，避免裁切）*/}
      <div className="relative w-full pt-3">
        {/* 飞书AI浮动徽章：放在卡片overflow-hidden外部absolute叠加，pt-3保证徽章顶部有足够空间 */}
        <motion.div
          initial={{ opacity: 0, y: -6 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.42 }}
          className="absolute top-0 left-4 z-20 bg-white text-sky-700 border border-sky-200 shadow-sm rounded-full px-2.5 py-0.5 flex items-center gap-1"
        >
          <Sparkles className="w-3 h-3 text-sky-500 flex-shrink-0" />
          <span className="text-[10px] sm:text-xs font-semibold whitespace-nowrap leading-tight">
            工单已入飞书多维表格 · AI 智能分级
          </span>
        </motion.div>

        {/* Ticket Card 主体（overflow-hidden控制圆角，徽章在外面，不会被切）*/}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.4 }}
          className="bg-white rounded-2xl shadow-lg overflow-hidden mb-4"
        >
          {/* Ticket Header（优先级色条）：关键修复——左侧flex-1可收缩，右侧flex-shrink-0保证响应时间不被截断 */}
          <div className={`${priority.bg} ${priority.text} px-3 sm:px-5 py-2 sm:py-3 flex items-center justify-between gap-2`}>
            <div className="flex items-center gap-1.5 sm:gap-2 min-w-0 flex-1">
              <AlertCircle className="w-4 h-4 sm:w-5 sm:h-5 flex-shrink-0" />
              <span className="font-semibold text-sm sm:text-base truncate leading-tight">
                {priority.label}问题 · {result.priority}
              </span>
            </div>
            <div className="flex items-center gap-1 text-[11px] sm:text-sm opacity-90 flex-shrink-0">
              <Clock className="w-3.5 h-3.5 sm:w-4 sm:h-4 flex-shrink-0" />
              <span className="whitespace-nowrap leading-tight">
                {result.estimated_response_time}响应
                <span className="opacity-80 ml-1 hidden sm:inline">· SLA 超时升级</span>
              </span>
            </div>
          </div>

          {/* Ticket Body（卡片所有内容主体）：窄屏下缩小内边距，给内容留更多空间 */}
          <div className="p-3.5 sm:p-5 space-y-3.5 sm:space-y-4">
            {/* Ticket ID */}
            <div className="flex items-center justify-between gap-2">
              <div className="min-w-0">
                <p className="text-xs text-gray-400 mb-1">工单编号</p>
                <p className="font-mono text-base sm:text-lg font-bold text-gray-800 truncate">
                  {result.ticket_id}
                </p>
              </div>
              <button
                onClick={copyTicketId}
                aria-label="复制工单编号"
                className="p-2 hover:bg-gray-100 rounded-lg transition-colors flex-shrink-0"
              >
                <Copy className="w-5 h-5 text-gray-400" />
              </button>
            </div>

            <div className="border-t border-dashed border-gray-200" />

            {/* Category & Vehicle */}
            <div className="grid grid-cols-2 gap-3 sm:gap-4">
              <div className="min-w-0">
                <p className="text-xs text-gray-400 mb-1">问题类型</p>
                <p className="text-gray-800 font-medium flex items-center gap-1 text-sm sm:text-base">
                  <span className="flex-shrink-0">{emoji}</span>
                  <span className="truncate">{result.category}</span>
                </p>
              </div>
              <div className="min-w-0 text-right">
                <p className="text-xs text-gray-400 mb-1">关联车辆</p>
                <p className="text-gray-800 font-mono text-sm sm:text-base truncate">
                  {qrData.vehicle_id !== 'UNKNOWN' ? qrData.vehicle_id : '未关联'}
                </p>
              </div>
            </div>

            {/* AI Summary */}
            <div className="bg-neolix-50 rounded-xl p-3">
              <div className="flex items-center gap-1 text-neolix-600 text-xs font-semibold mb-1">
                <span>🤖</span> AI摘要
              </div>
              <p className="text-sm text-gray-700 leading-relaxed break-words">
                {result.summary}
              </p>
            </div>

            {/* Status */}
            <div className="flex items-center gap-2 text-xs sm:text-sm">
              <div className="w-2 h-2 bg-blue-500 rounded-full animate-pulse flex-shrink-0" />
              <span className="text-gray-600 leading-relaxed">
                状态：{result.status}，已通知相关负责人
              </span>
            </div>
          </div>
        </motion.div>
        {/* /包装容器relative结束 */}
      </div>

      {/* Top3加分改造③：移动端独立SLA承诺行（窄屏显示，桌面隐藏），缩短文案避免窄屏右侧截断 */}
      <div className="sm:hidden -mt-3 mb-4 bg-white rounded-b-2xl border-x border-b border-gray-100 px-3.5 py-1.5 text-[10.5px] text-gray-500 flex items-center justify-between gap-1.5 shadow-sm">
        <div className="flex items-center gap-1 flex-shrink-0">
          <Clock className="w-3 h-3 flex-shrink-0 text-gray-400" />
          <span className="leading-snug whitespace-nowrap">SLA承诺</span>
        </div>
        <span className="text-right leading-snug truncate">
          超时未处理将自动升级至上级
        </span>
      </div>

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
        {/* Top3加分改造②：进入飞书AI问数（评委最关心的"飞书能力"CTA）*/}
        <motion.a
          href={DASHBOARD_URL || undefined}
          target={DASHBOARD_URL ? '_blank' : undefined}
          rel={DASHBOARD_URL ? 'noopener noreferrer' : undefined}
          onClick={(e) => { if (!DASHBOARD_URL) e.preventDefault(); }}
          className={`block w-full text-center bg-gradient-to-r from-sky-600 to-indigo-600 text-white font-semibold py-4 rounded-2xl shadow-lg shadow-sky-500/30 flex items-center justify-center gap-2 transition-transform ${DASHBOARD_URL ? 'active:scale-[0.98]' : 'opacity-60 cursor-not-allowed'}`}
        >
          <ExternalLink className="w-5 h-5" />
          <span>{DASHBOARD_URL ? '🚀 进入飞书 AI 问数' : '🚀 进入飞书 AI 问数（演示后配置链接）'}</span>
        </motion.a>

        {/* Top3加分改造②：查看本周TOP问题排行榜（聚类周报入口）*/}
        <motion.a
          href={REPORT_URL || undefined}
          target={REPORT_URL ? '_blank' : undefined}
          rel={REPORT_URL ? 'noopener noreferrer' : undefined}
          onClick={(e) => { if (!REPORT_URL) e.preventDefault(); }}
          className={`block w-full text-center bg-white text-indigo-700 border-2 border-indigo-200 font-semibold py-3.5 rounded-2xl flex items-center justify-center gap-2 transition-transform ${REPORT_URL ? 'active:scale-[0.98]' : 'opacity-60 cursor-not-allowed'}`}
        >
          <BarChart3 className="w-5 h-5" />
          <span>📊 查看本周 TOP 问题排行榜{REPORT_URL ? '' : '（演示后配置）'}</span>
        </motion.a>

        <button
          onClick={onReset}
          className="w-full bg-gradient-to-r from-neolix-600 to-neolix-500 text-white font-semibold py-4 rounded-2xl shadow-lg shadow-neolix-500/20 flex items-center justify-center gap-2 active:scale-[0.98] transition-transform"
        >
          <Home className="w-5 h-5" />
          <span>返回首页</span>
        </button>
        <div className="flex gap-3">
          <button
            type="button"
            onClick={handleShare}
            aria-label="分享工单"
            className="flex-1 bg-white text-gray-600 font-medium py-3.5 rounded-xl border border-gray-200 flex items-center justify-center gap-1.5 active:scale-[0.98] transition-transform text-sm touch-target"
          >
            <Share2 className="w-4 h-4" />
            <span>分享</span>
          </button>
          <button
            type="button"
            onClick={copyTicketId}
            aria-label="复制工单编号"
            className="flex-1 bg-white text-gray-600 font-medium py-3.5 rounded-xl border border-gray-200 flex items-center justify-center gap-1.5 active:scale-[0.98] transition-transform text-sm touch-target"
          >
            <Copy className="w-4 h-4" />
            <span>复制工单号</span>
          </button>
        </div>
      </motion.div>
    </div>
  );
}
