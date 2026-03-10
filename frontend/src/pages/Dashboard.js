import React, { useState } from 'react';
import axios from 'axios';
import { useNavigate } from 'react-router-dom';
import { Mic, TrendingUp, Package, History, LogOut, Send } from 'lucide-react';
import { toast } from 'sonner';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

export default function Dashboard({ token, setToken }) {
  const [command, setCommand] = useState('');
  const [loading, setLoading] = useState(false);
  const [listening, setListening] = useState(false);
  const navigate = useNavigate();

  const handleCommand = async () => {
    if (!command.trim()) return;
    setLoading(true);

    try {
      const response = await axios.post(
        `${API}/command`,
        { command },
        { headers: { Authorization: `Bearer ${token}` } }
      );
      toast.success(response.data.message);
      setCommand('');
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Something went wrong');
    } finally {
      setLoading(false);
    }
  };

  const handleLogout = () => {
    setToken(null);
    navigate('/login');
  };

  const quickCommands = [
    { text: 'Sold 5 tables for 1000 each', icon: '🛒' },
    { text: 'Bought raw material for 3000', icon: '💵' },
    { text: 'Customer paid 5000 in cash', icon: '💳' },
  ];

  return (
    <div className="min-h-screen pb-32">
      <div className="gradient-glow fixed inset-0 pointer-events-none" />
      
      <div className="max-w-md mx-auto p-6 relative z-10">
        <div className="flex items-center justify-between mb-8">
          <div>
            <h1 className="text-3xl font-extrabold text-stone-900 tracking-tight">
              EchoBiz
            </h1>
            <p className="text-stone-600 font-medium">Your Digital Munim</p>
          </div>
          <button
            data-testid="logout-button"
            onClick={handleLogout}
            className="p-3 rounded-full bg-stone-200 hover:bg-stone-300 active:scale-95 transition-all"
          >
            <LogOut className="h-5 w-5 text-stone-700" />
          </button>
        </div>

        <div className="bg-white rounded-2xl shadow-warm-lg p-6 mb-6">
          <div className="relative">
            <textarea
              data-testid="command-input"
              value={command}
              onChange={(e) => setCommand(e.target.value)}
              placeholder="Speak or type your command...\n\ne.g. Sold 5 tables for 1000 each"
              className="w-full min-h-[140px] text-xl font-medium text-stone-800 bg-transparent border-2 border-stone-200 rounded-xl p-4 focus:ring-0 focus:border-orange-500 outline-none resize-none placeholder:text-stone-300"
              onKeyDown={(e) => {
                if (e.key === 'Enter' && !e.shiftKey) {
                  e.preventDefault();
                  handleCommand();
                }
              }}
            />
          </div>

          <div className="flex gap-3 mt-4">
            <button
              data-testid="mic-button"
              onClick={() => {
                setListening(!listening);
                toast.info('Voice input coming soon!');
              }}
              className={`flex-1 py-4 rounded-full flex items-center justify-center gap-2 font-bold text-lg transition-all active:scale-95 ${
                listening
                  ? 'bg-red-500 text-white animate-pulse-slow'
                  : 'bg-orange-600 text-white hover:bg-orange-700'
              }`}
            >
              <Mic className="h-6 w-6" />
              {listening ? 'Listening...' : 'Speak'}
            </button>
            <button
              data-testid="send-button"
              onClick={handleCommand}
              disabled={loading || !command.trim()}
              className="px-6 py-4 rounded-full bg-teal-700 hover:bg-teal-800 active:scale-95 transition-all text-white disabled:opacity-50 disabled:cursor-not-allowed"
            >
              <Send className="h-6 w-6" />
            </button>
          </div>
        </div>

        <div className="mb-6">
          <h2 className="text-sm font-bold text-stone-500 uppercase tracking-wider mb-3">
            Quick Commands
          </h2>
          <div className="space-y-2">
            {quickCommands.map((cmd, idx) => (
              <button
                key={idx}
                data-testid={`quick-command-${idx}`}
                onClick={() => setCommand(cmd.text)}
                className="w-full p-4 rounded-xl bg-white border border-stone-200 hover:border-orange-300 hover:bg-orange-50 active:scale-95 transition-all text-left"
              >
                <p className="text-base font-medium text-stone-700">
                  {cmd.text}
                </p>
              </button>
            ))}
          </div>
        </div>

        <div className="grid grid-cols-2 gap-4">
          <button
            data-testid="summary-nav-button"
            onClick={() => navigate('/summary')}
            className="flex flex-col items-center justify-center p-6 bg-white border border-stone-100 shadow-warm rounded-2xl active:bg-stone-50 active:scale-95 transition-all gap-3 h-32"
          >
            <TrendingUp className="h-8 w-8 text-orange-600" />
            <span className="text-base font-bold text-stone-800">Summary</span>
          </button>

          <button
            data-testid="inventory-nav-button"
            onClick={() => navigate('/inventory')}
            className="flex flex-col items-center justify-center p-6 bg-white border border-stone-100 shadow-warm rounded-2xl active:bg-stone-50 active:scale-95 transition-all gap-3 h-32"
          >
            <Package className="h-8 w-8 text-teal-700" />
            <span className="text-base font-bold text-stone-800">Inventory</span>
          </button>

          <button
            data-testid="history-nav-button"
            onClick={() => navigate('/history')}
            className="flex flex-col items-center justify-center p-6 bg-white border border-stone-100 shadow-warm rounded-2xl active:bg-stone-50 active:scale-95 transition-all gap-3 h-32 col-span-2"
          >
            <History className="h-8 w-8 text-stone-600" />
            <span className="text-base font-bold text-stone-800">Transaction History</span>
          </button>
        </div>
      </div>
    </div>
  );
}