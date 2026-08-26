import { Truck, Sparkles } from 'lucide-react';

export default function Header() {
  return (
    <header className="bg-gradient-to-r from-neolix-600 to-neolix-500 text-white shadow-lg safe-top">
      {/* 窄屏(375px)下极限压缩：px-2.5 gap-1.5 py-2，确保左右都不溢出 */}
      <div className="px-2.5 sm:px-4 py-2 sm:py-3 flex items-center justify-between gap-1.5 sm:gap-2">
        {/* 左：新石器品牌 —— gap进一步缩小，标题字号375px下text-[13px]确保能放下5个字 */}
        <div className="flex items-center gap-1 sm:gap-2 min-w-0 flex-1">
          <Truck className="w-[18px] h-[18px] sm:w-6 sm:h-6 flex-shrink-0" />
          <span className="font-semibold text-[13px] sm:text-base md:text-lg tracking-wide truncate leading-tight">
            新石器无人车
          </span>
        </div>
        {/* 右：飞书 AI 驱动徽章 —— 375px下px-1.5 py-0.5 text-[9px]极限压缩 */}
        <div className="flex items-center gap-0.5 sm:gap-1.5 bg-white/15 backdrop-blur px-1.5 py-0.5 sm:px-2.5 sm:py-1 rounded-full border border-white/20 flex-shrink-0">
          <Sparkles className="w-2.5 h-2.5 sm:w-3.5 sm:h-3.5 text-yellow-200 flex-shrink-0" />
          <span className="text-[9px] sm:text-sm font-medium opacity-95 whitespace-nowrap leading-tight">
            飞书 AI 驱动
          </span>
        </div>
      </div>
    </header>
  );
}
