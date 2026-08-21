import { useState, useEffect, useCallback } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import HomePage from './components/HomePage';
import FeedbackForm from './components/FeedbackForm';
import SubmittingPage from './components/SubmittingPage';
import ResultPage from './components/ResultPage';
import ErrorPage from './components/ErrorPage';
import Header from './components/Header';
import DebugPanel from './components/DebugPanel';
import { submitFeedback } from './api';
import { logger } from './utils/logger';
import type { AppPage, FeedbackSubmitData, FeedbackResult, QRCodeData } from './types';

function parseQRFromURL(): QRCodeData {
  const params = new URLSearchParams(window.location.search);
  return {
    vehicle_id: params.get('vid') || params.get('vehicle_id') || 'UNKNOWN',
    vehicle_model: params.get('model') || '新石器X3',
    city: params.get('city') || '',
    location: params.get('loc') || '',
  };
}

const categoryEmoji: Record<string, string> = {
  '安全': '🚨',
  '故障': '🔧',
  '体验': '💬',
  '投诉': '⚠️',
  '建议': '💡',
};

const priorityColors: Record<string, { bg: string; text: string; label: string }> = {
  'P0': { bg: 'bg-red-500', text: 'text-white', label: '紧急' },
  'P1': { bg: 'bg-orange-500', text: 'text-white', label: '高优' },
  'P2': { bg: 'bg-yellow-400', text: 'text-yellow-950', label: '普通' },
  'P3': { bg: 'bg-green-500', text: 'text-white', label: '低优' },
};

export default function App() {
  const [page, setPage] = useState<AppPage>('home');
  const [qrData, setQrData] = useState<QRCodeData>({ vehicle_id: 'UNKNOWN' });
  const [submitData, setSubmitData] = useState<FeedbackSubmitData | null>(null);
  const [result, setResult] = useState<FeedbackResult | null>(null);
  const [errorMsg, setErrorMsg] = useState<string>('');
  const [failCount, setFailCount] = useState(0);

  useEffect(() => {
    const data = parseQRFromURL();
    setQrData(data);
    logger.info('App', '应用初始化完成', {
      url: window.location.href,
      vehicle_id: data.vehicle_id,
      model: data.vehicle_model,
      city: data.city,
      user_agent: /Mobi|Android|iPhone/i.test(navigator.userAgent) ? '移动端' : '桌面端',
      viewport: `${window.innerWidth}x${window.innerHeight}`,
      dpr: window.devicePixelRatio,
    });
  }, []);

  const navigateTo = useCallback((newPage: AppPage, from?: string) => {
    logger.info('Nav', `页面跳转: ${from || page} → ${newPage}`);
    setPage(newPage);
  }, [page]);

  const handleSubmit = async (data: FeedbackSubmitData, isRetry = false) => {
    // 组装最终 payload：把二维码解析出的 city / user_tier 信息注入，透传给后端（submit.ts buildFields 需要 city 字段）
    const payload: FeedbackSubmitData = {
      ...data,
      city: qrData.city || '',                          // 二维码解析出的城市（北京/上海/苏州等），写入 Schema city 字段
      user_tier_hint: '收件人',                         // 一车一码默认是收件人扫码场景，给后端兜底参考
    };

    logger.info('Form', isRetry ? '🔄 用户重试提交反馈' : '🔘 用户点击「提交反馈」按钮', {
      content_preview: payload.content_raw.slice(0, 50) + (payload.content_raw.length > 50 ? '...' : ''),
      content_length: payload.content_raw.length,
      category: payload.category || '(未选择，将AI自动识别)',
      contact_provided: !!(payload.contact_name || payload.contact_phone),
      vehicle_id: payload.vehicle_id,
      city: payload.city || '(二维码未包含城市，将默认留空)',
      ...(isRetry && { retry_attempt: failCount + 1 }),
    });

    setSubmitData(payload);  // 存的是最终 payload，重试时不会丢 city
    navigateTo('submitting', 'form');

    try {
      logger.info('Form', '⏳ 开始调用API提交...');
      const aiResult = await submitFeedback(payload);
      logger.success('Form', '✅ 提交流程全部完成', {
        ticket_id: aiResult.ticket_id,
        category: aiResult.category,
        priority: aiResult.priority,
      });
      setResult(aiResult);
      setFailCount(0);
      navigateTo('result', 'submitting');
    } catch (err) {
      const msg = err instanceof Error ? err.message : String(err);
      const newFailCount = failCount + 1;
      setFailCount(newFailCount);
      logger.error('Form', `❌ 提交失败（连续第 ${newFailCount} 次）`, msg);
      if (newFailCount >= 3) {
        logger.warn('Form', '⚠️ 连续失败已达3次，建议联系管理员');
      }
      setErrorMsg(msg || '网络连接异常，请检查网络后重试');
      navigateTo('error', 'submitting');
    }
  };

  const handleReset = () => {
    logger.info('Nav', '🔘 用户点击「返回首页」，重置状态');
    setPage('home');
    setSubmitData(null);
    setResult(null);
    setErrorMsg('');
    setFailCount(0);
  };

  const handleRetry = () => {
    logger.info('Form', '🔘 用户点击「重新提交」');
    if (submitData) {
      handleSubmit(submitData, true);
    } else {
      navigateTo('form', 'error');
    }
  };

  return (
    <div className="min-h-screen min-h-dvh flex flex-col relative">
      <Header />
      <main className="flex-1 flex flex-col overflow-y-auto overflow-x-hidden safe-bottom">
        <AnimatePresence mode="wait">
          <motion.div
            key={page}
            initial={{ opacity: 0, x: 20 }}
            animate={{ opacity: 1, x: 0 }}
            exit={{ opacity: 0, x: -20 }}
            transition={{ duration: 0.3, ease: 'easeInOut' }}
            className="flex-1 flex flex-col"
          >
            {page === 'home' && (
              <HomePage qrData={qrData} onStart={() => navigateTo('form', 'home')} />
            )}
            {page === 'form' && (
              <FeedbackForm
                qrData={qrData}
                onSubmit={handleSubmit}
                onBack={() => navigateTo('home', 'form')}
              />
            )}
            {page === 'submitting' && (
              <SubmittingPage data={submitData} />
            )}
            {page === 'result' && result && (
              <ResultPage
                result={result}
                qrData={qrData}
                onReset={handleReset}
                categoryEmoji={categoryEmoji}
                priorityColors={priorityColors}
              />
            )}
            {page === 'error' && (
              <ErrorPage message={errorMsg} failCount={failCount} onRetry={handleRetry} onBack={handleReset} />
            )}
          </motion.div>
        </AnimatePresence>
      </main>
      <DebugPanel />
    </div>
  );
}
