import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { useNavigate } from 'react-router-dom';
import { ArrowLeft, TrendingUp, TrendingDown, CreditCard, AlertCircle } from 'lucide-react';
import { toast } from 'sonner';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

export default function History({ token }) {
  const [transactions, setTransactions] = useState([]);
  const [loading, setLoading] = useState(true);
  const navigate = useNavigate();

  useEffect(() => {
    fetchTransactions();
  }, []);

  const fetchTransactions = async () => {
    try {
      const response = await axios.get(`${API}/transactions`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      setTransactions(response.data);
    } catch (error) {
      toast.error('Failed to load history');
    } finally {
      setLoading(false);
    }
  };

  const getTransactionIcon = (type) => {
    switch (type) {
      case 'sale':
        return <TrendingUp className="h-5 w-5 text-emerald-700" />;
      case 'expense':
        return <TrendingDown className="h-5 w-5 text-rose-700" />;
      case 'payment':
        return <CreditCard className="h-5 w-5 text-blue-700" />;
      default:
        return <AlertCircle className="h-5 w-5 text-stone-500" />;
    }
  };

  const getTransactionColor = (type) => {
    switch (type) {
      case 'sale':
        return 'bg-emerald-100';
      case 'expense':
        return 'bg-rose-100';
      case 'payment':
        return 'bg-blue-100';
      default:
        return 'bg-stone-100';
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
              History
            </h1>
            <p className="text-sm text-stone-600 font-medium">
              Recent {transactions.length} transactions
            </p>
          </div>
        </div>

        {transactions.length === 0 ? (
          <div className="bg-white rounded-2xl shadow-warm p-12 text-center">
            <div className="inline-flex items-center justify-center h-16 w-16 rounded-full bg-stone-100 mb-4">
              <AlertCircle className="h-8 w-8 text-stone-400" />
            </div>
            <p className="text-lg font-bold text-stone-700 mb-2">No transactions yet</p>
            <p className="text-stone-500">Start recording your first transaction</p>
          </div>
        ) : (
          <div className="space-y-3">
            {transactions.map((txn, idx) => (
              <div
                key={idx}
                data-testid={`transaction-item-${idx}`}
                className="flex justify-between items-center p-5 bg-white rounded-xl border border-stone-100 shadow-warm"
              >
                <div className="flex items-center gap-4">
                  <div className={`p-3 rounded-full ${getTransactionColor(txn.type)}`}>
                    {getTransactionIcon(txn.type)}
                  </div>
                  <div>
                    <p className="text-base font-bold text-stone-800 capitalize">
                      {txn.type}
                    </p>
                    <p className="text-sm text-stone-500">
                      {txn.product || txn.category || txn.customer || txn.mode || 'Transaction'}
                    </p>
                    {txn.quantity && (
                      <p className="text-xs text-stone-400">
                        Qty: {txn.quantity} @ ₹{txn.price_per_unit}
                      </p>
                    )}
                  </div>
                </div>
                <div className="text-right">
                  <p className={`text-xl font-extrabold ${
                    txn.type === 'sale' || txn.type === 'payment'
                      ? 'text-emerald-700'
                      : 'text-rose-700'
                  }`}>
                    {txn.type === 'sale' || txn.type === 'payment' ? '+' : '-'}₹{txn.total.toFixed(0)}
                  </p>
                  {txn.profit_loss !== undefined && txn.profit_loss !== null && (
                    <p className={`text-xs font-bold ${
                      txn.profit_loss >= 0 ? 'text-emerald-600' : 'text-rose-600'
                    }`}>
                      {txn.profit_loss >= 0 ? 'Profit' : 'Loss'}: ₹{Math.abs(txn.profit_loss).toFixed(0)}
                    </p>
                  )}
                  <p className="text-xs text-stone-500">{txn.date}</p>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}