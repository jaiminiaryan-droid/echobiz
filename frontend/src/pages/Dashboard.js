import React, { useState, useEffect, useRef } from 'react';
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
  const [recording, setRecording] = useState(false);
  const [summary, setSummary] = useState({ sales: 0, expenses: 0, profit: 0 });
  const navigate = useNavigate();
  const recognitionRef = useRef(null);
  const mediaRecorderRef = useRef(null);
  const audioChunksRef = useRef([]);

  useEffect(() => {
    fetchTodaySummary();
  }, []);

  const fetchTodaySummary = async () => {
    try {
      const response = await axios.get(`${API}/summary`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      setSummary(response.data);
    } catch (error) {
      console.error('Failed to load summary:', error);
    }
  };

  useEffect(() => {
    if ('webkitSpeechRecognition' in window || 'SpeechRecognition' in window) {
      const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
      recognitionRef.current = new SpeechRecognition();
      recognitionRef.current.continuous = false;
      recognitionRef.current.interimResults = false;
      recognitionRef.current.lang = 'en-IN';

      recognitionRef.current.onresult = (event) => {
        const transcript = event.results[0][0].transcript;
        setCommand(transcript);
        setListening(false);
        toast.success('Voice captured!');
      };

      recognitionRef.current.onerror = (event) => {
        console.error('Speech recognition error:', event.error);
        setListening(false);
        if (event.error === 'no-speech') {
          toast.error('No speech detected. Please try again.');
        } else if (event.error === 'not-allowed') {
          toast.error('Microphone access denied. Please enable it in browser settings.');
        } else {
          toast.error('Voice recognition error. Please try again.');
        }
      };

      recognitionRef.current.onend = () => {
        setListening(false);
      };
    }
  }, []);

  const toggleVoiceInput = async () => {
    if (recording) {
      // Stop recording
      if (mediaRecorderRef.current && mediaRecorderRef.current.state === 'recording') {
        mediaRecorderRef.current.stop();
      }
      return;
    }

    try {
      // Request microphone permission
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      
      // Create MediaRecorder
      const mediaRecorder = new MediaRecorder(stream, {
        mimeType: 'audio/webm;codecs=opus'
      });
      mediaRecorderRef.current = mediaRecorder;
      audioChunksRef.current = [];

      // Collect audio data
      mediaRecorder.ondataavailable = (event) => {
        if (event.data.size > 0) {
          audioChunksRef.current.push(event.data);
        }
      };

      // When recording stops
      mediaRecorder.onstop = async () => {
        setRecording(false);
        setLoading(true);

        // Create audio blob
        const audioBlob = new Blob(audioChunksRef.current, { type: 'audio/webm' });
        
        // Send to backend
        const formData = new FormData();
        formData.append('audio', audioBlob, 'recording.webm');

        try {
          const response = await axios.post(`${API}/voice`, formData, {
            headers: {
              'Authorization': `Bearer ${token}`,
              'Content-Type': 'multipart/form-data'
            }
          });

          // Set transcribed text and auto-submit
          setCommand(response.data.text);
          toast.success(response.data.message || 'Voice processed!');
          
          // Auto-process the command
          if (response.data.text) {
            setTimeout(() => {
              handleCommand();
            }, 500);
          }
        } catch (error) {
          toast.error(error.response?.data?.detail || 'Voice processing failed');
        } finally {
          setLoading(false);
        }

        // Stop all tracks
        stream.getTracks().forEach(track => track.stop());
      };

      // Start recording
      mediaRecorder.start();
      setRecording(true);
      setListening(false);
      toast.info('🎤 Recording... Speak now!');

      // Auto-stop after 10 seconds
      setTimeout(() => {
        if (mediaRecorder.state === 'recording') {
          mediaRecorder.stop();
        }
      }, 10000);

    } catch (error) {
      console.error('Microphone error:', error);
      if (error.name === 'NotAllowedError') {
        toast.error('Microphone permission denied. Please allow access in browser settings.');
      } else {
        toast.error('Could not access microphone');
      }
      setRecording(false);
    }
  };

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
      fetchTodaySummary();
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
    { text: 'Sold 5 rice for 60 each', icon: '🌾' },
    { text: 'Sold 10 sugar for 50 each', icon: '🍬' },
    { text: 'Bought shop supplies for 500', icon: '💰' },
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
              onClick={toggleVoiceInput}
              disabled={loading}
              className={`flex-1 py-4 rounded-full flex items-center justify-center gap-2 font-bold text-lg transition-all active:scale-95 ${
                recording
                  ? 'bg-red-500 text-white animate-pulse-slow'
                  : 'bg-orange-600 text-white hover:bg-orange-700'
              } ${loading ? 'opacity-50 cursor-not-allowed' : ''}`}
            >
              <Mic className="h-6 w-6" />
              {recording ? 'Recording...' : loading ? 'Processing...' : 'Speak'}
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

        <div className="bg-stone-900 text-white p-6 rounded-2xl shadow-warm-lg mb-6 relative overflow-hidden">
          <div className="absolute top-0 right-0 w-32 h-32 bg-orange-600 rounded-full blur-3xl opacity-20"></div>
          <div className="relative z-10">
            <p className="text-xs font-bold uppercase tracking-wider opacity-80 mb-4">
              Today's Business
            </p>
            <div className="grid grid-cols-3 gap-4">
              <div>
                <p className="text-xs opacity-70 mb-1">Sales</p>
                <p data-testid="dashboard-sales" className="text-xl font-extrabold text-emerald-400">
                  ₹{summary.sales.toFixed(0)}
                </p>
              </div>
              <div>
                <p className="text-xs opacity-70 mb-1">Expenses</p>
                <p data-testid="dashboard-expenses" className="text-xl font-extrabold text-rose-400">
                  ₹{summary.expenses.toFixed(0)}
                </p>
              </div>
              <div>
                <p className="text-xs opacity-70 mb-1">Profit</p>
                <p data-testid="dashboard-profit" className={`text-xl font-extrabold ${
                  summary.profit >= 0 ? 'text-emerald-300' : 'text-rose-300'
                }`}>
                  {summary.profit >= 0 ? '+' : ''}₹{summary.profit.toFixed(0)}
                </p>
              </div>
            </div>
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