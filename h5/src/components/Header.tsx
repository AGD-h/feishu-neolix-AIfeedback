import { Truck } from 'lucide-react';

export default function Header() {
  return (
    <header className="bg-gradient-to-r from-neolix-600 to-neolix-500 text-white shadow-lg safe-top">
      <div className="px-4 py-3 flex items-center justify-center gap-2">
        <Truck className="w-6 h-6" />
        <span className="font-semibold text-lg tracking-wide">新石器无人车</span>
      </div>
    </header>
  );
}
