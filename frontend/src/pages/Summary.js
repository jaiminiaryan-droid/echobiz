import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { useNavigate } from 'react-router-dom';
import { ArrowLeft, TrendingUp, TrendingDown, IndianRupee } from 'lucide-react';
import { toast } from 'sonner';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

export default function Summary({ token }) {
  const [summary, setSummary] = useState(null);
  const [loading, setLoading] = useState(true);
  const navigate = useNavigate();

  useEffect(() => {
    fetchSummary();
  }, []);

  const fetchSummary = async () => {
    try {
      const response = await axios.get(`${API}/summary`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      setSummary(response.data);
    } catch (error) {
      toast.error('Failed to load summary');
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-4 border-orange-600 border-t-transparent mx-auto mb-4"></div>
          <p className="text-stone-600 font-medium">Loading...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen pb-12">
      <div className="max-w-md mx-auto p-6">
        <div className="flex items-center gap-4 mb-8">
          <button
            data-testid="back-button"
            onClick={() => navigate('/')}
            className="p-3 rounded-full bg-stone-200 hover:bg-stone-300 active:scale-95 transition-all"
          >
            <ArrowLeft className="h-5 w-5 text-stone-700" />
          </button>
          <div>
            <h1 className="text-3xl font-extrabold text-stone-900 tracking-tight">
              Today's Summary
            </h1>
            <p className="text-sm text-stone-600 font-medium">{summary?.date}</p>
          </div>
        </div>

        <div className="space-y-4">
          <div className="bg-stone-900 text-white p-8 rounded-2xl shadow-warm-lg relative overflow-hidden">
            <div className="absolute top-0 right-0 w-32 h-32 bg-orange-600 rounded-full blur-3xl opacity-20"></div>
            <div className="relative z-10">
              <div className="flex items-center gap-2 mb-2">
                <IndianRupee className="h-5 w-5" />
                <p className="text-sm font-bold uppercase tracking-wider opacity-80">
                  Net Profit
                </p>
              </div>
              <p data-testid="profit-amount" className="text-5xl font-extrabold tracking-tight">
                {summary?.profit >= 0 ? '+' : ''}₹{summary?.profit.toFixed(0)}
              </p>
            </div>
          </div>

          <div className="bg-white p-6 rounded-2xl shadow-warm border border-stone-100">
            <div className="flex items-center justify-between mb-3">
              <div className="flex items-center gap-2">
                <div className="p-2 rounded-full bg-emerald-100">
                  <TrendingUp className="h-5 w-5 text-emerald-700" />
                </div>
                <p className="text-base font-bold text-stone-700">Total Sales</p>
              </div>
              <p data-testid="sales-amount" className="text-2xl font-extrabold text-emerald-700">
                ₹{summary?.sales.toFixed(0)}
              </p>
            </div>
          </div>

          <div className="bg-white p-6 rounded-2xl shadow-warm border border-stone-100">
            <div className="flex items-center justify-between mb-3">
              <div className="flex items-center gap-2">
                <div className="p-2 rounded-full bg-rose-100">
                  <TrendingDown className="h-5 w-5 text-rose-700" />
                </div>
                <p className="text-base font-bold text-stone-700">Total Expenses</p>
              </div>
              <p data-testid="expenses-amount" className="text-2xl font-extrabold text-rose-700">
                ₹{summary?.expenses.toFixed(0)}
              </p>
            </div>
          </div>
        </div>

        <button
          data-testid="refresh-button"
          onClick={fetchSummary}
          className="w-full mt-6 py-4 rounded-full bg-orange-600 hover:bg-orange-700 active:scale-95 transition-all text-white font-bold text-lg shadow-lg"
        >
          Refresh Summary
        </button>
      </div>
    </div>
  );
}