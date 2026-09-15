'use client';
import { useState, useRef, useEffect } from 'react';
import { Send, Loader2, Bot, User, Wrench } from 'lucide-react';
import { api, type CopilotResponse } from '@/lib/api';

interface Message {
  id: number;
  role: 'user' | 'assistant';
  text: string;
  toolsUsed?: CopilotResponse['tools_used'];
  sources?: string[];
}

const EXAMPLES = [
  'Which shipments need immediate attention?',
  'Why is the highest-risk shipment delayed?',
  'Optimize the fleet assignment.',
  'Which shipments will likely miss their deadline?',
  'What should I do about critical risk shipments?',
];

let msgId = 0;

export default function CopilotPage() {
  const [messages, setMessages] = useState<Message[]>([
    {
      id: ++msgId,
      role: 'assistant',
      text: "Hello! I'm the SupplyChainAI Copilot. I can investigate shipment risks, analyze root causes, optimize fleet assignments, and run simulations. What would you like to know?",
    },
  ]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const send = async (text: string) => {
    if (!text.trim() || loading) return;
    const userMsg: Message = { id: ++msgId, role: 'user', text };
    setMessages((m) => [...m, userMsg]);
    setInput('');
    setLoading(true);

    try {
      const res = await api.copilot(text);
      setMessages((m) => [
        ...m,
        {
          id: ++msgId,
          role: 'assistant',
          text: res.answer,
          toolsUsed: res.tools_used,
          sources: res.sources,
        },
      ]);
    } catch (e) {
      setMessages((m) => [
        ...m,
        { id: ++msgId, role: 'assistant', text: `Error: ${String(e)}` },
      ]);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="flex flex-col h-full">
      {/* Header */}
      <div className="px-6 py-4 border-b border-slate-800 flex-shrink-0">
        <h1 className="text-xl font-bold text-white">AI Supply Chain Copilot</h1>
        <p className="text-sm text-slate-400 mt-0.5">Orchestrates ML prediction, risk analysis, optimization, and simulation tools</p>
      </div>

      {/* Example prompts */}
      {messages.length <= 1 && (
        <div className="px-6 py-4 flex-shrink-0">
          <p className="text-xs text-slate-500 mb-3 font-medium uppercase tracking-wide">Try asking:</p>
          <div className="flex flex-wrap gap-2">
            {EXAMPLES.map((e) => (
              <button
                key={e}
                onClick={() => send(e)}
                className="px-3 py-1.5 bg-slate-800 hover:bg-slate-700 text-slate-300 text-xs rounded-full border border-slate-700 transition-colors"
              >
                {e}
              </button>
            ))}
          </div>
        </div>
      )}

      {/* Messages */}
      <div className="flex-1 overflow-auto px-6 py-4 space-y-4">
        {messages.map((msg) => (
          <div key={msg.id} className={`flex gap-3 ${msg.role === 'user' ? 'flex-row-reverse' : ''}`}>
            <div className={`flex-shrink-0 w-7 h-7 rounded-full flex items-center justify-center ${msg.role === 'user' ? 'bg-blue-600' : 'bg-slate-700'}`}>
              {msg.role === 'user' ? <User className="w-3.5 h-3.5 text-white" /> : <Bot className="w-3.5 h-3.5 text-slate-300" />}
            </div>
            <div className={`max-w-2xl ${msg.role === 'user' ? 'items-end' : 'items-start'} flex flex-col gap-2`}>
              <div className={`rounded-xl px-4 py-3 text-sm leading-relaxed ${
                msg.role === 'user'
                  ? 'bg-blue-600 text-white'
                  : 'bg-slate-800 text-slate-200'
              }`}>
                <MarkdownText text={msg.text} />
              </div>

              {/* Tools used */}
              {msg.toolsUsed && msg.toolsUsed.length > 0 && (
                <div className="flex flex-wrap gap-1.5">
                  {msg.toolsUsed.map((t, i) => (
                    <div key={i} className="flex items-center gap-1 px-2 py-0.5 bg-slate-900 border border-slate-700 rounded-full text-xs text-slate-400">
                      <Wrench className="w-2.5 h-2.5" />
                      <span>{t.tool_name}</span>
                    </div>
                  ))}
                </div>
              )}

              {/* Sources */}
              {msg.sources && msg.sources.length > 0 && (
                <div className="text-xs text-slate-500">
                  Sources: {msg.sources.join(', ')}
                </div>
              )}
            </div>
          </div>
        ))}

        {loading && (
          <div className="flex gap-3">
            <div className="w-7 h-7 rounded-full bg-slate-700 flex items-center justify-center flex-shrink-0">
              <Bot className="w-3.5 h-3.5 text-slate-300" />
            </div>
            <div className="bg-slate-800 rounded-xl px-4 py-3 flex items-center gap-2">
              <Loader2 className="w-4 h-4 animate-spin text-blue-400" />
              <span className="text-sm text-slate-400">Invoking tools...</span>
            </div>
          </div>
        )}
        <div ref={bottomRef} />
      </div>

      {/* Input */}
      <div className="px-6 py-4 border-t border-slate-800 flex-shrink-0">
        <form
          onSubmit={(e) => { e.preventDefault(); send(input); }}
          className="flex gap-3"
        >
          <input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder="Ask about shipments, risks, fleet optimization..."
            disabled={loading}
            className="flex-1 bg-slate-800 border border-slate-700 rounded-xl px-4 py-2.5 text-sm text-slate-200 placeholder:text-slate-500 focus:outline-none focus:border-blue-500 transition-colors"
          />
          <button
            type="submit"
            disabled={!input.trim() || loading}
            className="px-4 py-2.5 bg-blue-600 hover:bg-blue-500 disabled:opacity-50 text-white rounded-xl transition-colors"
          >
            <Send className="w-4 h-4" />
          </button>
        </form>
      </div>
    </div>
  );
}

function MarkdownText({ text }: { text: string }) {
  // Simple markdown: **bold**, bullet lists, line breaks
  const lines = text.split('\n');
  return (
    <div className="space-y-1">
      {lines.map((line, i) => {
        if (line.startsWith('•') || line.startsWith('-')) {
          return (
            <div key={i} className="flex gap-1.5">
              <span className="text-blue-400 flex-shrink-0">•</span>
              <span dangerouslySetInnerHTML={{ __html: boldify(line.slice(1).trim()) }} />
            </div>
          );
        }
        if (line.startsWith('**') && line.includes(':**')) {
          return <p key={i} className="font-semibold text-white mt-2" dangerouslySetInnerHTML={{ __html: boldify(line) }} />;
        }
        if (!line.trim()) return <div key={i} className="h-1" />;
        return <p key={i} dangerouslySetInnerHTML={{ __html: boldify(line) }} />;
      })}
    </div>
  );
}

function boldify(s: string): string {
  return s.replace(/\*\*(.+?)\*\*/g, '<strong class="text-white">$1</strong>');
}
