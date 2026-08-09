import { motion } from 'framer-motion';
import { MessageSquare, QrCode, Clock, Shield, ChevronRight, MapPin } from 'lucide-react';
import type { QRCodeData } from '../types';

interface HomePageProps {
  qrData: QRCodeData;
  onStart: () => void;
}

export default function HomePage({ qrData, onStart }: HomePageProps) {
  const isScanned = qrData.vehicle_id !== 'UNKNOWN';

  return (
    <div className="flex-1 flex flex-col px-5 py-6 overflow-y-auto">
      {/* Vehicle Info Card */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.5 }}
        className="bg-white rounded-2xl shadow-lg p-5 mb-6"
      >
        <div className="flex items-center gap-3 mb-4">
          <div className="w-14 h-14 bg-gradient-to-br from-neolix-500 to-neolix-600 rounded-2xl flex items-center justify-center shadow-md">
            <span className="text-3xl">🚗</span>
          </div>
          <div className="flex-1">
            <h2 className="text-lg font-bold text-gray-800">
              {isScanned ? qrData.vehicle_model : '新石器无人配送车'}
            </h2>
            {isScanned ? (
              <div className="flex items-center gap-1 text-sm text-gray-500 mt-1">
                <MapPin className="w-3.5 h-3.5" />
                <span>车辆编号：{qrData.vehicle_id}</span>
                {qrData.city && <span className="text-neolix-500"> · {qrData.city}</span>}
              </div>
            ) : (
              <p className="text-sm text-gray-500 mt-1">感谢您使用新石器无人配送服务</p>
            )}
          </div>
        </div>

        {isScanned && (
          <div className="bg-neolix-50 rounded-xl p-3 flex items-center gap-2">
            <QrCode className="w-5 h-5 text-neolix-600 flex-shrink-0" />
            <p className="text-sm text-neolix-700">已扫描车辆二维码，反馈将自动关联本车</p>
          </div>
        )}
      </motion.div>

      {/* Welcome Text */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.5, delay: 0.1 }}
        className="mb-6"
      >
        <h1 className="text-2xl font-bold text-gray-900 mb-2">遇到问题？反馈给我们</h1>
        <p className="text-gray-500 text-sm leading-relaxed">
          您的每一条反馈都将由AI智能分析，自动分级并推送给相关负责人，帮助我们快速改进服务。
        </p>
      </motion.div>

      {/* Features */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.5, delay: 0.2 }}
        className="space-y-3 mb-8"
      >
        {[
          { icon: <MessageSquare className="w-5 h-5" />, title: 'AI智能分析', desc: '自动识别问题类型，无需手动选择', color: 'from-neolix-400 to-neolix-500' },
          { icon: <Clock className="w-5 h-5" />, title: '快速响应', desc: '紧急问题5分钟内到达负责人', color: 'from-neolix-500 to-neolix-600' },
          { icon: <Shield className="w-5 h-5" />, title: '全程追踪', desc: '工单编号实时查询处理进度', color: 'from-neolix-600 to-neolix-700' },
        ].map((feature, i) => (
          <div key={i} className="bg-white/80 backdrop-blur rounded-xl p-4 flex items-center gap-3 shadow-sm">
            <div className={`w-10 h-10 bg-gradient-to-br ${feature.color} rounded-lg flex items-center justify-center text-white shadow-sm`}>
              {feature.icon}
            </div>
            <div className="flex-1">
              <p className="font-semibold text-gray-800 text-sm">{feature.title}</p>
              <p className="text-xs text-gray-500">{feature.desc}</p>
            </div>
          </div>
        ))}
      </motion.div>

      {/* CTA Button */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.5, delay: 0.3 }}
        className="mt-auto"
      >
        <button
          onClick={onStart}
          className="w-full bg-gradient-to-r from-neolix-600 to-neolix-500 text-white font-semibold py-4 rounded-2xl shadow-lg shadow-neolix-500/30 flex items-center justify-center gap-2 active:scale-[0.98] transition-transform"
        >
          <MessageSquare className="w-5 h-5" />
          <span>开始反馈</span>
          <ChevronRight className="w-5 h-5" />
        </button>
        <p className="text-center text-xs text-gray-400 mt-3">
          预计耗时 30 秒 · 您的信息将被严格保密
        </p>
      </motion.div>
    </div>
  );
}
