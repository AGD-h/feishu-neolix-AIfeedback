import { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { WifiOff, RefreshCw, Home, AlertTriangle, Phone, Copy, Check, Headphones } from 'lucide-react';

interface ErrorPageProps {
  message: string;
  failCount: number;
  onRetry: () => void;
  onBack: () => void;
}

const ADMIN_PHONE = import.meta.env.VITE_ADMIN_PHONE || '';
const ADMIN_WECHAT = import.meta.env.VITE_ADMIN_WECHAT || '';
const HAS_ADMIN_CONTACT = ADMIN_PHONE || ADMIN_WECHAT;

export default function ErrorPage({ message, failCount, onRetry, onBack }: ErrorPageProps) {
  const [copied, setCopied] = useState<string | null>(null);
  const showAdminHint = failCount >= 3 && HAS_ADMIN_CONTACT;

  const handleCopy = (text: string, key: string) => {
    navigator.clipboard?.writeText(text).then(() => {
      setCopied(key);
      setTimeout(() => setCopied(null), 2000);
    }).catch(() => {
      const ta = document.createElement('textarea');
      ta.value = text;
      document.body.appendChild(ta);
      ta.select();
      document.execCommand('copy');
      document.body.removeChild(ta);
      setCopied(key);
      setTimeout(() => setCopied(null), 2000);
    });
  };

  return (
    <div className="flex-1 flex flex-col items-center justify-center px-6">
      <motion.div
        initial={{ scale: 0 }}
        animate={{ scale: 1 }}
        transition={{ type: 'spring', stiffness: 200, damping: 15 }}
        className="w-24 h-24 bg-red-100 rounded-full flex items-center justify-center mb-5"
      >
        <WifiOff className="w-12 h-12 text-red-500" />
      </motion.div>

      <motion.h2
        initial={{ opacity: 0, y: 10 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.15 }}
        className="text-xl font-bold text-gray-800 mb-2"
      >
        提交失败
      </motion.h2>

      <motion.p
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ delay: 0.25 }}
        className="text-gray-500 text-sm text-center mb-4 leading-relaxed"
      >
        {message || '网络连接异常，请检查网络设置后重试'}
      </motion.p>

      {failCount > 0 && !showAdminHint && (
        <motion.div
          initial={{ opacity: 0, scale: 0.9 }}
          animate={{ opacity: 1, scale: 1 }}
          transition={{ delay: 0.3 }}
          className="text-xs text-gray-400 mb-4"
        >
          已重试 {failCount} 次
        </motion.div>
      )}

      {/* 本地保存提示 */}
      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ delay: 0.35 }}
        className="bg-yellow-50 border border-yellow-200 rounded-xl p-3 mb-4 w-full max-w-sm"
      >
        <div className="flex items-start gap-2">
          <AlertTriangle className="w-4 h-4 text-yellow-600 flex-shrink-0 mt-0.5" />
          <p className="text-xs text-yellow-800 leading-relaxed">
            您的反馈内容已保存在本地，不会丢失。请检查网络后重新提交。
          </p>
        </div>
      </motion.div>

      {/* 连续失败3次后显示联系管理员提示 */}
      <AnimatePresence>
        {showAdminHint && (
          <motion.div
            initial={{ opacity: 0, y: 10, scale: 0.95 }}
            animate={{ opacity: 1, y: 0, scale: 1 }}
            exit={{ opacity: 0, y: -10 }}
            transition={{ delay: 0.4, type: 'spring', stiffness: 200, damping: 20 }}
            className="w-full max-w-sm mb-6 bg-red-50 border border-red-200 rounded-xl p-4"
          >
            <div className="flex items-start gap-2.5">
              <div className="w-8 h-8 bg-red-100 rounded-full flex items-center justify-center flex-shrink-0">
                <Headphones className="w-4 h-4 text-red-600" />
              </div>
              <div className="flex-1 min-w-0">
                <p className="text-sm font-semibold text-red-800 mb-1">
                  建议联系人工客服
                </p>
                <p className="text-xs text-red-600/80 leading-relaxed mb-3">
                  已连续失败 {failCount} 次，可能是网络或服务器问题，您可以直接联系管理员处理：
                </p>
                <div className="space-y-2">
                  {ADMIN_PHONE && (
                    <button
                      type="button"
                      onClick={() => handleCopy(ADMIN_PHONE, 'phone')}
                      className="w-full flex items-center justify-between bg-white rounded-lg px-3 py-2.5 border border-red-100 active:bg-red-50 transition-colors"
                      aria-label={`复制客服电话 ${ADMIN_PHONE}`}
                    >
                      <div className="flex items-center gap-2">
                        <Phone className="w-4 h-4 text-red-500" />
                        <span className="text-sm text-gray-700 font-medium">{ADMIN_PHONE}</span>
                      </div>
                      {copied === 'phone' ? (
                        <Check className="w-4 h-4 text-green-500" aria-hidden="true" />
                      ) : (
                        <Copy className="w-3.5 h-3.5 text-gray-400" aria-hidden="true" />
                      )}
                    </button>
                  )}
                  {ADMIN_WECHAT && (
                    <button
                      type="button"
                      onClick={() => handleCopy(ADMIN_WECHAT, 'wechat')}
                      className="w-full flex items-center justify-between bg-white rounded-lg px-3 py-2.5 border border-red-100 active:bg-red-50 transition-colors"
                      aria-label={`复制客服微信号 ${ADMIN_WECHAT}`}
                    >
                      <div className="flex items-center gap-2">
                        <span className="w-4 h-4 text-green-500 text-center leading-4 text-sm" aria-hidden="true">💬</span>
                        <span className="text-sm text-gray-700 font-medium">微信: {ADMIN_WECHAT}</span>
                      </div>
                      {copied === 'wechat' ? (
                        <Check className="w-4 h-4 text-green-500" aria-hidden="true" />
                      ) : (
                        <Copy className="w-3.5 h-3.5 text-gray-400" aria-hidden="true" />
                      )}
                    </button>
                  )}
                </div>
              </div>
            </div>
          </motion.div>
        )}
      </AnimatePresence>

      <motion.div
        initial={{ opacity: 0, y: 10 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.5 }}
        className="w-full max-w-sm space-y-3"
      >
        <button
          onClick={onRetry}
          className="w-full bg-gradient-to-r from-neolix-600 to-neolix-500 text-white font-semibold py-4 rounded-2xl shadow-lg shadow-neolix-500/20 flex items-center justify-center gap-2 active:scale-[0.98] transition-transform touch-target"
        >
          <RefreshCw className={`w-5 h-5 ${showAdminHint ? '' : ''}`} />
          <span>重新提交</span>
        </button>
        <button
          onClick={onBack}
          className="w-full bg-white text-gray-600 font-medium py-3 rounded-xl border border-gray-200 flex items-center justify-center gap-2 active:scale-[0.98] transition-transform touch-target"
        >
          <Home className="w-5 h-5" />
          <span>返回首页</span>
        </button>
      </motion.div>
    </div>
  );
}
