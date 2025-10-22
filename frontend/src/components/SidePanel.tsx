import { ReactNode } from 'react';

interface SidePanelProps {
  isOpen: boolean;
  onClose: () => void;
  title: string;
  children: ReactNode;
}

export default function SidePanel({ isOpen, onClose, title, children }: SidePanelProps) {
  return (
    <div
      className={`h-screen bg-white border-l-2 border-gray-300 shadow-2xl transition-all duration-300 ease-in-out overflow-y-auto ${
        isOpen ? 'w-full md:w-2/3 lg:w-1/2' : 'w-0'
      }`}
      style={{ minWidth: isOpen ? '400px' : '0' }}
    >
      {isOpen && (
        <>
          {/* Header */}
          <div className="sticky top-0 bg-gradient-to-r from-green-600 to-emerald-600 text-white px-6 py-4 flex items-center justify-between shadow-md z-10">
            <h2 className="text-xl font-semibold">{title}</h2>
            <button
              onClick={onClose}
              className="p-2 hover:bg-white/20 rounded-lg transition-colors"
              aria-label="Close panel"
            >
              <svg
                className="w-6 h-6"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M6 18L18 6M6 6l12 12"
                />
              </svg>
            </button>
          </div>

          {/* Content */}
          <div className="p-6">{children}</div>
        </>
      )}
    </div>
  );
}

