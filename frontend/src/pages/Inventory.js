import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { useNavigate } from 'react-router-dom';
import { ArrowLeft, Package, AlertCircle } from 'lucide-react';
import { toast } from 'sonner';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

export default function Inventory({ token }) {
  const [inventory, setInventory] = useState([]);
  const [loading, setLoading] = useState(true);
  const navigate = useNavigate();

  useEffect(() => {
    fetchInventory();
  }, []);

  const fetchInventory = async () => {
    try {
      const response = await axios.get(`${API}/inventory`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      setInventory(response.data);
    } catch (error) {
      toast.error('Failed to load inventory');
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
              Inventory
            </h1>
            <p className="text-sm text-stone-600 font-medium">
              {inventory.length} {inventory.length === 1 ? 'item' : 'items'}
            </p>
          </div>
        </div>

        {inventory.length === 0 ? (
          <div className="bg-white rounded-2xl shadow-warm p-12 text-center">
            <div className="inline-flex items-center justify-center h-16 w-16 rounded-full bg-stone-100 mb-4">
              <AlertCircle className="h-8 w-8 text-stone-400" />
            </div>
            <p className="text-lg font-bold text-stone-700 mb-2">No inventory yet</p>
            <p className="text-stone-500">Start recording sales to track inventory</p>
          </div>
        ) : (
          <div className="space-y-3">
            {inventory.map((item, idx) => (
              <div
                key={idx}
                data-testid={`inventory-item-${idx}`}
                className="flex justify-between items-center p-6 bg-white rounded-xl border border-stone-100 shadow-warm"
              >
                <div className="flex items-center gap-4">
                  <div className="p-3 rounded-full bg-teal-100">
                    <Package className="h-6 w-6 text-teal-700" />
                  </div>
                  <div>
                    <p className="text-lg font-bold text-stone-800 capitalize">
                      {item.product}
                    </p>
                    <p className="text-sm text-stone-500">Stock</p>
                  </div>
                </div>
                <div className="text-right">
                  <p className="text-2xl font-extrabold text-stone-900">
                    {item.quantity}
                  </p>
                  <p className="text-xs text-stone-500">units</p>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}