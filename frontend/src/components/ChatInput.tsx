import { useState, type FormEvent } from 'react';

interface ChatInputProps {
  onSend: (message: string) => void;
  disabled?: boolean;
}

export default function ChatInput({ onSend, disabled = false }: ChatInputProps) {
  const [input, setInput] = useState('');

  const handleSubmit = (e: FormEvent) => {
    e.preventDefault();
    if (input.trim() && !disabled) {
      onSend(input.trim());
      setInput('');
    }
  };

  return (
    <form onSubmit={handleSubmit} className="border-t border-border bg-card p-4 shadow-lg">
      <div className="flex gap-3">
        <input
          type="text"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          placeholder="Ask me about flights..."
          disabled={disabled}
          className="flex-1 px-4 py-3 border border-input bg-background rounded-xl focus:outline-none focus:ring-2 focus:ring-ring focus:border-transparent disabled:bg-muted disabled:cursor-not-allowed transition-all text-foreground placeholder:text-muted-foreground"
        />
        <button
          type="submit"
          disabled={disabled || !input.trim()}
          className="px-6 py-3 bg-primary text-primary-foreground rounded-xl hover:bg-primary/90 disabled:bg-muted disabled:text-muted-foreground disabled:cursor-not-allowed transition-all font-medium shadow-md hover:shadow-lg disabled:shadow-none"
        >
          <span className="flex items-center gap-2">
            <span>Send</span>
            <span>→</span>
          </span>
        </button>
      </div>
    </form>
  );
}

