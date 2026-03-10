import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { useNavigate } from 'react-router-dom';
import { ArrowLeft, Package, AlertCircle, Plus } from 'lucide-react';
import { toast } from 'sonner';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

export default function Inventory({ token }) {
  const [inventory, setInventory] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showAddForm, setShowAddForm] = useState(false);
  const [formData, setFormData] = useState({
    product: '',
    quantity: '',
    purchase_price: ''
  });
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

  const handleSeedInventory = async () => {
    try {
      const response = await axios.post(`${API}/inventory/seed`, {}, {
        headers: { Authorization: `Bearer ${token}` },
      });
      toast.success(response.data.message);
      fetchInventory();
    } catch (error) {
      toast.error('Failed to seed inventory');
    }
  };

  const handleAddStock = async (e) => {
    e.preventDefault();
    try {
      const response = await axios.post(
        `${API}/inventory/add`,
        {
          product: formData.product,
          quantity: parseInt(formData.quantity),
          purchase_price: parseFloat(formData.purchase_price)
        },
        { headers: { Authorization: `Bearer ${token}` } }
      );
      toast.success(response.data.message);
      setShowAddForm(false);
      setFormData({ product: '', quantity: '', purchase_price: '' });
      fetchInventory();
    } catch (error) {
      toast.error('Failed to add stock');
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
          <div className="flex-1">
            <h1 className="text-3xl font-extrabold text-stone-900 tracking-tight">
              Inventory
            </h1>
            <p className="text-sm text-stone-600 font-medium">
              {inventory.length} {inventory.length === 1 ? 'item' : 'items'}
            </p>
          </div>
          <button
            data-testid="add-stock-button"
            onClick={() => setShowAddForm(!showAddForm)}
            className="p-3 rounded-full bg-orange-600 hover:bg-orange-700 active:scale-95 transition-all"
          >
            <Plus className="h-5 w-5 text-white" />
          </button>
        </div>

        {showAddForm && (
          <div className="bg-white rounded-2xl shadow-warm p-6 mb-6">
            <h2 className="text-lg font-bold text-stone-900 mb-4">Add Stock</h2>
            <form onSubmit={handleAddStock} className="space-y-4">
              <div>
                <label className="block text-sm font-semibold text-stone-700 mb-2">
                  Product Name
                </label>
                <input
                  type="text"
                  value={formData.product}
                  onChange={(e) => setFormData({ ...formData, product: e.target.value })}
                  className="w-full px-4 py-3 rounded-xl border-2 border-stone-200 focus:border-orange-500 focus:ring-0 outline-none transition-colors font-medium"
                  placeholder="e.g., Rice, Sugar"
                  required
                />
              </div>
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-semibold text-stone-700 mb-2">
                    Quantity
                  </label>
                  <input
                    type="number"
                    value={formData.quantity}
                    onChange={(e) => setFormData({ ...formData, quantity: e.target.value })}
                    className="w-full px-4 py-3 rounded-xl border-2 border-stone-200 focus:border-orange-500 focus:ring-0 outline-none transition-colors font-medium"
                    placeholder="10"
                    required
                  />
                </div>
                <div>
                  <label className="block text-sm font-semibold text-stone-700 mb-2">
                    Purchase Price (₹)
                  </label>
                  <input
                    type="number"
                    step="0.01"
                    value={formData.purchase_price}
                    onChange={(e) => setFormData({ ...formData, purchase_price: e.target.value })}
                    className="w-full px-4 py-3 rounded-xl border-2 border-stone-200 focus:border-orange-500 focus:ring-0 outline-none transition-colors font-medium"
                    placeholder="50"
                    required
                  />
                </div>
              </div>
              <div className="flex gap-3">
                <button
                  type="submit"
                  className="flex-1 py-3 rounded-full bg-orange-600 hover:bg-orange-700 active:scale-95 transition-all text-white font-bold"
                >
                  Add Stock
                </button>
                <button
                  type="button"
                  onClick={() => setShowAddForm(false)}
                  className="px-6 py-3 rounded-full bg-stone-200 hover:bg-stone-300 active:scale-95 transition-all text-stone-700 font-bold"
                >
                  Cancel
                </button>
              </div>
            </form>
          </div>
        )}

        {inventory.length === 0 ? (
          <div className="bg-white rounded-2xl shadow-warm p-12 text-center">
            <div className="inline-flex items-center justify-center h-16 w-16 rounded-full bg-stone-100 mb-4">
              <AlertCircle className="h-8 w-8 text-stone-400" />
            </div>
            <p className="text-lg font-bold text-stone-700 mb-2">No inventory yet</p>
            <p className="text-stone-500 mb-4">Add some initial stock to get started</p>
            <button
              data-testid="seed-inventory-button"
              onClick={handleSeedInventory}
              className="px-6 py-3 rounded-full bg-orange-600 hover:bg-orange-700 active:scale-95 transition-all text-white font-bold"
            >
              Add Sample Groceries
            </button>
          </div>
        ) : (
          <div className="space-y-3">
            {inventory.map((item, idx) => (
              <div
                key={idx}
                data-testid={`inventory-item-${idx}`}
                className="p-6 bg-white rounded-xl border border-stone-100 shadow-warm"
              >
                <div className="flex justify-between items-start mb-3">
                  <div className="flex items-center gap-4">
                    <div className="p-3 rounded-full bg-teal-100">
                      <Package className="h-6 w-6 text-teal-700" />
                    </div>
                    <div>
                      <p className="text-lg font-bold text-stone-800 capitalize">
                        {item.product}
                      </p>
                      <p className="text-sm text-stone-500">
                        Purchase: ₹{item.purchase_price}/unit
                      </p>
                    </div>
                  </div>
                  <div className="text-right">
                    <p className="text-2xl font-extrabold text-stone-900">
                      {item.quantity}
                    </p>
                    <p className="text-xs text-stone-500">units</p>
                  </div>
                </div>
                <div className="pt-3 border-t border-stone-100">
                  <p className="text-xs text-stone-600">
                    Total Value: ₹{(item.quantity * item.purchase_price).toFixed(0)}
                  </p>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}