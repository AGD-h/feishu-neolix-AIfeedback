import { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { ArrowLeft, Send, AlertTriangle, ChevronDown, ChevronUp, User, Phone, MapPin } from 'lucide-react';
import type { QRCodeData, FeedbackSubmitData, FeedbackCategory, ContactAllowed } from '../types';

interface FeedbackFormProps {
  qrData: QRCodeData;
  onSubmit: (data: FeedbackSubmitData) => void;
  onBack: () => void;
}

const categories: { value: FeedbackCategory; label: string; emoji: string; desc: string; color: string }[] = [
  { value: '安全', label: '安全问题', emoji: '🚨', desc: '碰撞/危险/事故隐患', color: 'border-red-400 bg-red-50 text-red-700' },
  { value: '故障', label: '车辆故障', emoji: '🔧', desc: '无法使用/打不开/趴窝', color: 'border-orange-400 bg-orange-50 text-orange-700' },
  { value: '投诉', label: '服务投诉', emoji: '⚠️', desc: '不满/要求处理/赔偿', color: 'border-orange-400 bg-orange-50 text-orange-700' },
  { value: '体验', label: '体验问题', emoji: '💬', desc: '取件慢/位置不准/麻烦', color: 'border-yellow-400 bg-yellow-50 text-yellow-700' },
  { value: '建议', label: '改进建议', emoji: '💡', desc: '想法/优化/新增功能', color: 'border-green-400 bg-green-50 text-green-700' },
];

const quickIssues = [
  '柜门打不开',
  '车辆不动了',
  '取件码无效',
  '车没到指定位置',
  '联系不上客服',
  '柜门关不上',
];

const PHONE_RE = /^1\d{10}$/;

export default function FeedbackForm({ qrData, onSubmit, onBack }: FeedbackFormProps) {
  const [content, setContent] = useState('');
  const [category, setCategory] = useState<FeedbackCategory | ''>('');
  const [contactName, setContactName] = useState('');
  const [contactPhone, setContactPhone] = useState('');
  const [location, setLocation] = useState(qrData.location || '');
  // contact_allowed 严格三态：'是'/'否'/''（空串=用户未表态）
  const [contactAllowed, setContactAllowed] = useState<ContactAllowed>('');
  const [showAdvanced, setShowAdvanced] = useState(false);
  const [contentError, setContentError] = useState(false);
  const [phoneError, setPhoneError] = useState(false);

  const handleQuickIssue = (issue: string) => {
    setContent(issue + '，');
    setContentError(false);
  };

  const handleSubmit = () => {
    let hasError = false;
    if (content.trim().length < 5) {
      setContentError(true);
      hasError = true;
    } else {
      setContentError(false);
    }
    if (contactPhone.trim() && !PHONE_RE.test(contactPhone.trim())) {
      setPhoneError(true);
      setShowAdvanced(true);
      hasError = true;
    } else {
      setPhoneError(false);
    }
    if (hasError) return;
    onSubmit({
      vehicle_id: qrData.vehicle_id,
      content_raw: content.trim(),
      category: category || undefined,
      contact_name: contactName || undefined,
      contact_phone: contactPhone || undefined,
      contact_allowed: contactAllowed,
      location_detail: location || undefined,
    });
  };

  return (
    <div className="flex-1 flex flex-col px-5 py-4 overflow-y-auto">
      {/* Back Button */}
      <button
        onClick={onBack}
        className="flex items-center gap-1 text-gray-500 hover:text-gray-700 mb-4 self-start"
      >
        <ArrowLeft className="w-5 h-5" />
        <span className="text-sm">返回</span>
      </button>

      {/* Vehicle Badge */}
      {qrData.vehicle_id !== 'UNKNOWN' && (
        <motion.div
          initial={{ opacity: 0, scale: 0.95 }}
          animate={{ opacity: 1, scale: 1 }}
          className="bg-neolix-50 border border-neolix-200 rounded-xl px-4 py-2 mb-4 flex items-center gap-2"
        >
          <span className="text-lg">🚗</span>
          <span className="text-sm text-neolix-700">
            车辆 <span className="font-semibold">{qrData.vehicle_id}</span>
            {qrData.city && <span> · {qrData.city}</span>}
          </span>
        </motion.div>
      )}

      {/* Content Section */}
      <motion.div
        initial={{ opacity: 0, y: 10 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.1 }}
        className="mb-4"
      >
        <label htmlFor="feedback-content" className="block text-sm font-semibold text-gray-700 mb-2">
          请描述您遇到的问题 <span className="text-red-500">*</span>
        </label>
        <div className="relative">
          <textarea
            id="feedback-content"
            value={content}
            onChange={(e) => { setContent(e.target.value); setContentError(false); }}
            placeholder="例如：柜门打不开，已经等了5分钟了，急着取件……"
            aria-invalid={contentError}
            aria-describedby={contentError ? 'feedback-content-error' : undefined}
            className={`w-full h-32 p-4 rounded-2xl border-2 text-gray-800 placeholder-gray-400 resize-none transition-colors ${
              contentError ? 'border-red-400 bg-red-50' : 'border-gray-200 bg-white focus:border-neolix-500'
            }`}
            maxLength={500}
          />
          <span className="absolute bottom-3 right-3 text-xs text-gray-400">
            {content.length}/500
          </span>
        </div>
        {contentError && (
          <motion.p
            id="feedback-content-error"
            role="alert"
            initial={{ opacity: 0, height: 0 }}
            animate={{ opacity: 1, height: 'auto' }}
            className="text-red-500 text-xs mt-1 flex items-center gap-1"
          >
            <AlertTriangle className="w-3 h-3" />
            请至少描述5个字以上的问题
          </motion.p>
        )}
      </motion.div>

      {/* Quick Issues */}
      <motion.div
        initial={{ opacity: 0, y: 10 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.15 }}
        className="mb-4"
      >
        <p className="text-xs text-gray-500 mb-2">快速选择：</p>
        <div className="flex flex-wrap gap-2">
          {quickIssues.map((issue) => (
            <button
              key={issue}
              onClick={() => handleQuickIssue(issue)}
              className="px-3 py-1.5 bg-gray-100 hover:bg-neolix-100 hover:text-neolix-700 text-gray-600 rounded-full text-sm transition-colors active:scale-95"
            >
              {issue}
            </button>
          ))}
        </div>
      </motion.div>

      {/* Category Selection */}
      <motion.div
        initial={{ opacity: 0, y: 10 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.2 }}
        className="mb-4"
      >
        <label className="block text-sm font-semibold text-gray-700 mb-2">
          问题类型 <span className="text-gray-400 font-normal text-xs">（选填，AI会自动识别）</span>
        </label>
        <div className="grid grid-cols-1 gap-2">
          {categories.map((cat) => (
            <button
              key={cat.value}
              onClick={() => setCategory(category === cat.value ? '' : cat.value)}
              className={`p-3 rounded-xl border-2 text-left flex items-center gap-3 transition-all active:scale-[0.98] ${
                category === cat.value
                  ? cat.color + ' border-current shadow-sm'
                  : 'border-gray-200 bg-white text-gray-700 hover:border-gray-300'
              }`}
            >
              <span className="text-2xl">{cat.emoji}</span>
              <div className="flex-1">
                <p className="font-medium text-sm">{cat.label}</p>
                <p className="text-xs opacity-70">{cat.desc}</p>
              </div>
              {category === cat.value && (
                <div className="w-5 h-5 bg-current rounded-full flex items-center justify-center">
                  <svg className="w-3 h-3 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={3} d="M5 13l4 4L19 7" />
                  </svg>
                </div>
              )}
            </button>
          ))}
        </div>
      </motion.div>

      {/* Advanced Options Toggle */}
      <motion.button
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ delay: 0.25 }}
        onClick={() => setShowAdvanced(!showAdvanced)}
        className="flex items-center gap-1 text-sm text-gray-500 mb-3 self-start"
      >
        {showAdvanced ? <ChevronUp className="w-4 h-4" /> : <ChevronDown className="w-4 h-4" />}
        <span>{showAdvanced ? '收起' : '补充联系方式'}（选填）</span>
      </motion.button>

      {/* Advanced Fields */}
      <AnimatePresence>
        {showAdvanced && (
          <motion.div
            initial={{ opacity: 0, height: 0 }}
            animate={{ opacity: 1, height: 'auto' }}
            exit={{ opacity: 0, height: 0 }}
            className="space-y-3 mb-4 overflow-hidden"
          >
            <div className="flex items-center gap-2">
              <label htmlFor="contact-name" className="contents sr-only">
                <User className="w-4 h-4 text-gray-400 flex-shrink-0" />
                您的称呼
              </label>
              <User className="w-4 h-4 text-gray-400 flex-shrink-0" aria-hidden="true" />
              <input
                id="contact-name"
                type="text"
                value={contactName}
                onChange={(e) => setContactName(e.target.value)}
                placeholder="您的称呼"
                aria-label="您的称呼"
                className="flex-1 px-3 py-2.5 rounded-xl border border-gray-200 bg-white text-gray-800 placeholder-gray-400 focus:border-neolix-500 text-sm"
              />
            </div>
            <div className="flex flex-col gap-1">
              <div className="flex items-center gap-2">
                <label htmlFor="contact-phone" className="contents sr-only">
                  <Phone className="w-4 h-4 text-gray-400 flex-shrink-0" />
                  联系电话（方便我们联系您处理）
                </label>
                <Phone className="w-4 h-4 text-gray-400 flex-shrink-0" aria-hidden="true" />
                <input
                  id="contact-phone"
                  type="tel"
                  value={contactPhone}
                  onChange={(e) => { setContactPhone(e.target.value); setPhoneError(false); }}
                  placeholder="联系电话（方便我们联系您处理）"
                  aria-label="联系电话"
                  aria-invalid={phoneError}
                  aria-describedby={phoneError ? 'contact-phone-error' : undefined}
                  inputMode="numeric"
                  autoComplete="tel"
                  className={`flex-1 px-3 py-2.5 rounded-xl border bg-white text-gray-800 placeholder-gray-400 focus:border-neolix-500 text-sm transition-colors ${
                    phoneError ? 'border-red-400 bg-red-50' : 'border-gray-200'
                  }`}
                />
              </div>
              {phoneError && (
                <motion.p
                  id="contact-phone-error"
                  role="alert"
                  initial={{ opacity: 0, height: 0 }}
                  animate={{ opacity: 1, height: 'auto' }}
                  className="text-red-500 text-xs pl-6 flex items-center gap-1"
                >
                  <AlertTriangle className="w-3 h-3" />
                  手机号格式不正确，请输入11位以1开头的号码
                </motion.p>
              )}
            </div>
            <div className="flex items-center gap-2">
              <label htmlFor="location-detail" className="contents sr-only">
                <MapPin className="w-4 h-4 text-gray-400 flex-shrink-0" />
                具体位置（如：XX小区3号门）
              </label>
              <MapPin className="w-4 h-4 text-gray-400 flex-shrink-0" aria-hidden="true" />
              <input
                id="location-detail"
                type="text"
                value={location}
                onChange={(e) => setLocation(e.target.value)}
                placeholder="具体位置（如：XX小区3号门）"
                aria-label="具体位置"
                className="flex-1 px-3 py-2.5 rounded-xl border border-gray-200 bg-white text-gray-800 placeholder-gray-400 focus:border-neolix-500 text-sm"
              />
            </div>
            {/* 联系意愿：三态（是/否/未选择），空串表示用户未表态不写入 */}
            <div className="flex flex-col gap-1.5">
              <p className="text-sm text-gray-600 px-1">希望工作人员联系您了解详情吗？</p>
              <div className="flex items-center gap-3">
                <button
                  type="button"
                  onClick={() => setContactAllowed(contactAllowed === '是' ? '' : '是')}
                  className={`flex-1 px-3 py-2 rounded-xl border text-sm transition-all ${
                    contactAllowed === '是'
                      ? 'border-neolix-500 bg-neolix-50 text-neolix-700 font-semibold shadow-inner'
                      : 'border-gray-200 bg-white text-gray-600 hover:border-gray-300'
                  }`}
                >
                  ✅ 允许联系
                </button>
                <button
                  type="button"
                  onClick={() => setContactAllowed(contactAllowed === '否' ? '' : '否')}
                  className={`flex-1 px-3 py-2 rounded-xl border text-sm transition-all ${
                    contactAllowed === '否'
                      ? 'border-gray-500 bg-gray-100 text-gray-700 font-semibold shadow-inner'
                      : 'border-gray-200 bg-white text-gray-600 hover:border-gray-300'
                  }`}
                >
                  🙅 不希望打扰
                </button>
              </div>
              {contactAllowed === '' && (
                <p className="text-[11px] text-gray-400 px-1">未选择则视为暂不表态，工作人员不会主动联系</p>
              )}
            </div>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Submit Button */}
      <div className="mt-auto pt-4">
        <button
          onClick={handleSubmit}
          disabled={content.trim().length < 5}
          className="w-full bg-gradient-to-r from-neolix-600 to-neolix-500 disabled:from-gray-300 disabled:to-gray-400 text-white font-semibold py-4 rounded-2xl shadow-lg shadow-neolix-500/20 disabled:shadow-none flex items-center justify-center gap-2 active:scale-[0.98] transition-all"
        >
          <Send className="w-5 h-5" />
          <span>提交反馈</span>
        </button>
      </div>
    </div>
  );
}
