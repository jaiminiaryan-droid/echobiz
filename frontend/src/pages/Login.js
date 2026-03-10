import React, { useState } from 'react';
import axios from 'axios';
import { useNavigate } from 'react-router-dom';
import { Store } from 'lucide-react';
import { toast } from 'sonner';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

export default function Login({ setToken }) {
  const [isLogin, setIsLogin] = useState(true);
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [loading, setLoading] = useState(false);
  const navigate = useNavigate();

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);

    try {
      const endpoint = isLogin ? '/auth/login' : '/auth/register';
      const response = await axios.post(`${API}${endpoint}`, {
        username,
        password,
      });

      setToken(response.data.token);
      toast.success(isLogin ? 'Welcome back!' : 'Account created!');
      navigate('/');
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Something went wrong');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex flex-col items-center justify-center p-6 bg-gradient-to-br from-stone-50 via-orange-50 to-stone-100">
      <div className="w-full max-w-md">
        <div className="text-center mb-8">
          <div className="inline-flex items-center justify-center h-20 w-20 rounded-full bg-orange-600 mb-4 shadow-warm-lg">
            <Store className="h-10 w-10 text-white" />
          </div>
          <h1 className="text-4xl font-extrabold text-stone-900 mb-2 tracking-tight">
            EchoBiz
          </h1>
          <p className="text-lg text-stone-600 font-medium">
            Your Digital Munim
          </p>
        </div>

        <div className="bg-white rounded-2xl shadow-warm-lg p-8">
          <div className="flex gap-2 mb-6">
            <button
              data-testid="login-tab"
              onClick={() => setIsLogin(true)}
              className={`flex-1 py-3 px-4 rounded-xl font-semibold transition-all ${ 
                isLogin
                  ? 'bg-orange-600 text-white shadow-md'
                  : 'bg-stone-100 text-stone-600 hover:bg-stone-200'
              }`}
            >
              Login
            </button>
            <button
              data-testid="register-tab"
              onClick={() => setIsLogin(false)}
              className={`flex-1 py-3 px-4 rounded-xl font-semibold transition-all ${
                !isLogin
                  ? 'bg-orange-600 text-white shadow-md'
                  : 'bg-stone-100 text-stone-600 hover:bg-stone-200'
              }`}
            >
              Register
            </button>
          </div>

          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <label className="block text-sm font-semibold text-stone-700 mb-2">
                Username
              </label>
              <input
                data-testid="username-input"
                type="text"
                value={username}
                onChange={(e) => setUsername(e.target.value)}
                className="w-full px-4 py-3 rounded-xl border-2 border-stone-200 focus:border-orange-500 focus:ring-0 outline-none transition-colors text-lg font-medium"
                required
              />
            </div>

            <div>
              <label className="block text-sm font-semibold text-stone-700 mb-2">
                Password
              </label>
              <input
                data-testid="password-input"
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                className="w-full px-4 py-3 rounded-xl border-2 border-stone-200 focus:border-orange-500 focus:ring-0 outline-none transition-colors text-lg font-medium"
                required
              />
            </div>

            <button
              data-testid="submit-button"
              type="submit"
              disabled={loading}
              className="w-full py-4 rounded-full bg-orange-600 hover:bg-orange-700 active:scale-95 transition-all text-white font-bold text-lg shadow-lg disabled:opacity-50 disabled:cursor-not-allowed mt-6"
            >
              {loading ? 'Please wait...' : isLogin ? 'Login' : 'Create Account'}
            </button>
          </form>
        </div>

        <div className="mt-6 text-center text-sm text-stone-500">
          <p>Manage your shop ledger with voice commands</p>
        </div>
      </div>
    </div>
  );
}