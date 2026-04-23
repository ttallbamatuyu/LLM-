"use client";

import React, { useState, useEffect } from 'react';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, AreaChart, Area } from 'recharts';
import { Send, Shield, Zap, RefreshCw, AlertTriangle, Key, TrendingDown, Moon, Sun, Leaf } from 'lucide-react';
import ReactMarkdown from 'react-markdown';
import { useTheme } from 'next-themes';

type CostEntry = { time: string; originalCost: number; proxyCost: number; saved: number; model: string; carbonSaved: number };

export default function Dashboard() {
  const [openaiKey, setOpenaiKey] = useState('');
  const [geminiKey, setGeminiKey] = useState('');
  const [activeTab, setActiveTab] = useState('dashboard');
  const { theme, setTheme } = useTheme();
  const [mounted, setMounted] = useState(false);

  useEffect(() => {
    setMounted(true);
  }, []);

  // Chat Simulator State
  const [prompt, setPrompt] = useState('');
  const [chatLog, setChatLog] = useState<{ role: string, content: string, meta?: any }[]>([]);
  const [isLoading, setIsLoading] = useState(false);

  // 실시간 비용 추적
  const [costHistory, setCostHistory] = useState<CostEntry[]>([]);

  const addCostEntry = (meta: any) => {
    if (!meta || meta.isError) return;
    const now = new Date();
    const timeStr = `${now.getHours().toString().padStart(2,'0')}:${now.getMinutes().toString().padStart(2,'0')}:${now.getSeconds().toString().padStart(2,'0')}`;
    const saved = meta.estimated_cost_saved || 0;
    const originalCost = saved + 0.03; // 프록시 없이 최상위 모델을 쓴 예상 비용
    const proxyCost = meta.cache_hit ? 0 : 0.03 - saved * 0.5;
    
    // 단순 탄소 배출 모델: API 호출 한 번당 대형 모델은 0.5g CO2, 소형/캐시는 0.05g 발생 가정
    const carbonSaved = meta.cache_hit ? 0.5 : (saved > 0 ? 0.45 : 0);

    setCostHistory(prev => [...prev, {
      time: timeStr,
      originalCost: Math.round(originalCost * 100) / 100,
      proxyCost: Math.round(Math.max(proxyCost, 0.001) * 100) / 100,
      saved: Math.round(saved * 100) / 100,
      model: meta.routed_to || 'unknown',
      carbonSaved: carbonSaved
    }]);
  };

  const totalSaved = costHistory.reduce((sum, e) => sum + e.saved, 0);
  const totalCarbonSaved = costHistory.reduce((sum, e) => sum + e.carbonSaved, 0);
  const totalCalls = costHistory.length;

  const handleChatSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!prompt.trim()) return;

    if (!openaiKey && !geminiKey) {
        alert("최소 한 개 이상의 API Key(OpenAI 또는 Gemini)를 BYOK 영역에 입력해주세요!");
        return;
    }

    const newMessage = { role: 'user', content: prompt };
    setChatLog(prev => [...prev, newMessage]);
    setPrompt('');
    setIsLoading(true);

    try {
      const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
      const res = await fetch(`${API_URL}/v1/chat/completions`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-Openai-Key': openaiKey,
          'X-Gemini-Key': geminiKey,
        },
        body: JSON.stringify({
          messages: [...chatLog, newMessage]
        })
      });

      if (!res.ok) {
         const data = await res.json();
         throw new Error(data.detail || 'API Request Failed');
      }

      setIsLoading(false); // 연결 성공 시 로딩바 끄기
      
      let currentContent = '';
      let metaData: any = undefined;
      setChatLog(prev => [...prev, { role: 'assistant', content: '', meta: undefined }]);

      const reader = res.body?.getReader();
      const decoder = new TextDecoder("utf-8");

      if (reader) {
        while (true) {
          const { done, value } = await reader.read();
          if (done) break;
          const chunk = decoder.decode(value, { stream: true });
          const lines = chunk.split('\n');
          
          for (const line of lines) {
            if (line.startsWith('data: ')) {
              const dataStr = line.replace('data: ', '');
              try {
                const parsed = JSON.parse(dataStr);
                if (parsed.meta_only) {
                   metaData = parsed.meta;
                } else if (parsed.meta) {
                   // From cache (all at once)
                   currentContent = parsed.content;
                   metaData = parsed.meta;
                } else if (parsed.content) {
                   currentContent += parsed.content;
                }
                
                // 타자 치듯 실시간 UI 업데이트
                setChatLog(prev => {
                    const newLog = [...prev];
                    newLog[newLog.length - 1] = { 
                        role: 'assistant', 
                        content: currentContent, 
                        meta: metaData 
                    };
                    return newLog;
                });
              } catch (e) {}
            }
          }
        }
      }
      // 스트리밍 완료 후 비용 데이터를 차트에 반영
      if (metaData) addCostEntry(metaData);
    } catch (err: any) {
      setChatLog(prev => [...prev, {
        role: 'assistant',
        content: `Error: ${err.message}`,
        meta: { isError: true }
      }]);
      setIsLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-slate-50 dark:bg-slate-900 text-slate-900 dark:text-slate-100 p-4 md:p-8 font-sans transition-colors selection:bg-indigo-100 selection:text-indigo-900">
      <div className="max-w-6xl mx-auto">
        <header className="mb-10 flex flex-col md:flex-row md:justify-between md:items-end border-b border-slate-200 dark:border-slate-800 pb-6">
          <div>
            <h1 className="text-3xl md:text-4xl font-extrabold tracking-tight text-slate-900 dark:text-white">AI Gateway Dashboard <span className="text-indigo-600 dark:text-indigo-400">V4</span></h1>
            <p className="text-slate-500 dark:text-slate-400 mt-2 font-medium">Enterprise AI Governance & Optimization Platform</p>
          </div>
          <div className="flex flex-col sm:flex-row items-center gap-4 mt-6 md:mt-0">
              {mounted && (
                <button
                  onClick={() => setTheme(theme === 'dark' ? 'light' : 'dark')}
                  className="p-2 rounded-full bg-slate-200 dark:bg-slate-800 text-slate-600 dark:text-slate-300 hover:bg-slate-300 dark:hover:bg-slate-700 transition-colors"
                >
                  {theme === 'dark' ? <Sun className="w-5 h-5" /> : <Moon className="w-5 h-5" />}
                </button>
              )}
              <div className="flex bg-white dark:bg-slate-800 shadow-sm border border-slate-200 dark:border-slate-700 rounded-xl p-1">
                  <button 
                      className={`px-6 py-2.5 rounded-lg text-sm font-semibold transition-all duration-200 ${activeTab === 'dashboard' ? 'bg-slate-900 dark:bg-slate-700 text-white shadow-md' : 'text-slate-500 dark:text-slate-400 hover:text-slate-900 dark:hover:text-white hover:bg-slate-50 dark:hover:bg-slate-800'}`}
                      onClick={() => setActiveTab('dashboard')}
                  >
                      Analytics
                  </button>
                  <button 
                      className={`px-6 py-2.5 rounded-lg text-sm font-semibold transition-all duration-200 flex items-center ml-1 ${activeTab === 'playground' ? 'bg-indigo-600 text-white shadow-md' : 'text-slate-500 dark:text-slate-400 hover:text-slate-900 dark:hover:text-white hover:bg-slate-50 dark:hover:bg-slate-800'}`}
                      onClick={() => setActiveTab('playground')}
                  >
                      <Zap className="w-4 h-4 mr-2" />
                      Playground
                  </button>
              </div>
          </div>
        </header>

        {activeTab === 'dashboard' && (
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8 animate-in slide-in-from-bottom-4 fade-in duration-500">
          <section className="lg:col-span-1 bg-white dark:bg-slate-800 rounded-2xl p-8 border border-slate-200 dark:border-slate-700 shadow-sm">
            <h2 className="text-lg font-bold mb-2 text-slate-900 dark:text-white flex items-center"><Key className="w-5 h-5 mr-2 text-indigo-500"/> Bring Your Own Key</h2>
            <p className="text-sm text-slate-500 dark:text-slate-400 mb-8 leading-relaxed">Enter your API keys to enable intelligent routing. Keys are stored locally in your browser session.</p>
            
            <div className="space-y-5">
              <div>
                <label className="block text-sm font-semibold text-slate-700 dark:text-slate-300 mb-1.5">OpenAI API Key</label>
                <input 
                  type="password" 
                  value={openaiKey}
                  onChange={(e) => setOpenaiKey(e.target.value)}
                  className="w-full bg-slate-50 dark:bg-slate-900 border border-slate-300 dark:border-slate-600 rounded-xl py-2.5 px-4 text-slate-900 dark:text-white placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 transition-shadow"
                  placeholder="sk-..."
                />
              </div>
              <div>
                <label className="block text-sm font-semibold text-slate-700 dark:text-slate-300 mb-1.5">Gemini API Key</label>
                <input 
                  type="password" 
                  value={geminiKey}
                  onChange={(e) => setGeminiKey(e.target.value)}
                  className="w-full bg-slate-50 dark:bg-slate-900 border border-slate-300 dark:border-slate-600 rounded-xl py-2.5 px-4 text-slate-900 dark:text-white placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-emerald-500 focus:border-emerald-500 transition-shadow"
                  placeholder="AIzaSy..."
                />
              </div>
              <div className="p-5 bg-indigo-50/50 dark:bg-indigo-900/20 rounded-xl border border-indigo-100 dark:border-indigo-800/50 mt-6">
                <h3 className="text-xs font-bold text-indigo-900 dark:text-indigo-300 mb-3 uppercase tracking-wider">V4 Active Features</h3>
                <ul className="text-sm font-medium text-indigo-700 dark:text-indigo-400 space-y-3">
                    <li className="flex items-center"><Shield className="w-4 h-4 text-indigo-500 mr-2.5"/> Context-Preserving Masking</li>
                    <li className="flex items-center"><RefreshCw className="w-4 h-4 text-blue-500 mr-2.5"/> Self-Healing Router</li>
                    <li className="flex items-center"><Leaf className="w-4 h-4 text-emerald-500 mr-2.5"/> Carbon Footprint Tracker</li>
                </ul>
              </div>
            </div>
          </section>

          <section className="lg:col-span-2 bg-white dark:bg-slate-800 rounded-2xl p-8 border border-slate-200 dark:border-slate-700 shadow-sm flex flex-col">
            <div className="flex justify-between items-center mb-4">
              <h2 className="text-lg font-bold flex items-center text-slate-900 dark:text-white">
                <span className="relative flex h-3 w-3 mr-3">
                  <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75"></span>
                  <span className="relative inline-flex rounded-full h-3 w-3 bg-emerald-500"></span>
                </span>
                Live API Cost & ESG Tracking
              </h2>
              <div className="flex gap-3">
                <div className="bg-emerald-50 dark:bg-emerald-900/20 border border-emerald-200 dark:border-emerald-800/50 rounded-lg px-3 py-2 text-center">
                  <p className="text-[10px] font-bold text-emerald-600 dark:text-emerald-400 uppercase">CO2 Reduced</p>
                  <p className="text-lg font-extrabold text-emerald-700 dark:text-emerald-300">{totalCarbonSaved.toFixed(2)}g</p>
                </div>
                <div className="bg-indigo-50 dark:bg-indigo-900/20 border border-indigo-200 dark:border-indigo-800/50 rounded-lg px-3 py-2 text-center">
                  <p className="text-[10px] font-bold text-indigo-600 dark:text-indigo-400 uppercase">Total Saved</p>
                  <p className="text-lg font-extrabold text-indigo-700 dark:text-indigo-300">${totalSaved.toFixed(2)}</p>
                </div>
              </div>
            </div>
            <div className="flex-1 w-full min-h-[300px]">
              {costHistory.length === 0 ? (
                <div className="flex flex-col items-center justify-center h-full text-slate-400 space-y-3">
                  <TrendingDown className="w-12 h-12 text-slate-300" />
                  <p className="text-sm font-bold text-slate-500">No data yet</p>
                  <p className="text-xs text-slate-400 max-w-xs text-center">Go to Playground and send some prompts. Cost data will appear here in real-time.</p>
                </div>
              ) : (
                <ResponsiveContainer width="100%" height="100%">
                  <AreaChart data={costHistory}>
                    <defs>
                      <linearGradient id="colorOriginal" x1="0" y1="0" x2="0" y2="1">
                        <stop offset="5%" stopColor="#ef4444" stopOpacity={0.15}/>
                        <stop offset="95%" stopColor="#ef4444" stopOpacity={0}/>
                      </linearGradient>
                      <linearGradient id="colorProxy" x1="0" y1="0" x2="0" y2="1">
                        <stop offset="5%" stopColor="#10b981" stopOpacity={0.15}/>
                        <stop offset="95%" stopColor="#10b981" stopOpacity={0}/>
                      </linearGradient>
                    </defs>
                    <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" vertical={false} />
                    <XAxis dataKey="time" stroke="#64748b" axisLine={false} tickLine={false} dy={10} fontSize={11} />
                    <YAxis stroke="#64748b" tickFormatter={(v) => `$${v}`} axisLine={false} tickLine={false} dx={-10} fontSize={11} />
                    <Tooltip 
                      contentStyle={{ backgroundColor: '#fff', border: '1px solid #e2e8f0', borderRadius: '12px', boxShadow: '0 4px 12px rgb(0 0 0 / 0.1)', fontSize: '12px', fontWeight: '600' }} 
                    />
                    <Area type="monotone" dataKey="originalCost" name="Without Proxy" stroke="#ef4444" strokeWidth={2.5} fill="url(#colorOriginal)" dot={{r: 3}} />
                    <Area type="monotone" dataKey="proxyCost" name="With Proxy" stroke="#10b981" strokeWidth={2.5} fill="url(#colorProxy)" dot={{r: 3}} />
                  </AreaChart>
                </ResponsiveContainer>
              )}
            </div>
          </section>
        </div>
        )}

        {activeTab === 'playground' && (
        <div className="bg-white dark:bg-slate-800 rounded-2xl border border-slate-200 dark:border-slate-700 shadow-sm flex flex-col h-[75vh] animate-in slide-in-from-bottom-4 fade-in duration-500 overflow-hidden">
           <div className="bg-slate-50 dark:bg-slate-900/50 border-b border-slate-200 dark:border-slate-700 p-5 flex justify-between items-center">
              <h2 className="text-lg font-bold flex items-center text-slate-900 dark:text-white">
                  <Zap className="w-5 h-5 text-indigo-500 mr-2.5"/> API Routing Simulator
              </h2>
              <div className="text-xs font-semibold px-3 py-1.5 rounded-full flex items-center bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 shadow-sm">
                  {openaiKey || geminiKey ? (
                      <><span className="w-2 h-2 rounded-full bg-emerald-500 mr-2"></span> <span className="text-slate-600 dark:text-slate-300">Keys Loaded</span></>
                  ) : (
                      <><span className="w-2 h-2 rounded-full bg-red-500 mr-2"></span> <span className="text-slate-600 dark:text-slate-300">Keys Missing</span></>
                  )}
              </div>
           </div>

           <div className="flex-1 overflow-y-auto p-6 space-y-6 bg-slate-50/50 dark:bg-slate-900">
              {chatLog.length === 0 && (
                  <div className="flex flex-col items-center justify-center h-full text-center text-slate-500 dark:text-slate-400 space-y-4">
                      <div className="w-16 h-16 bg-white dark:bg-slate-800 shadow-sm border border-slate-200 dark:border-slate-700 rounded-full flex items-center justify-center mb-2">
                        <Zap className="w-8 h-8 text-indigo-500" />
                      </div>
                      <p className="text-lg font-bold text-slate-700 dark:text-slate-300">Try asking a question to test the routing!</p>
                      <p className="text-sm font-medium text-slate-500 dark:text-slate-400 max-w-md">The Gateway will analyze your prompt, mask sensitive data, and stream the optimal response while reporting ESG metrics.</p>
                  </div>
              )}
              {chatLog.map((msg, idx) => (
                  <div key={idx} className={`flex flex-col ${msg.role === 'user' ? 'items-end' : 'items-start'}`}>
                      <div className={`max-w-[85%] p-4 rounded-2xl text-[15px] leading-relaxed shadow-sm font-medium prose prose-sm dark:prose-invert ${msg.role === 'user' ? 'bg-indigo-600 text-white rounded-br-sm' : 'bg-white dark:bg-slate-800 text-slate-800 dark:text-slate-100 rounded-bl-sm border border-slate-200 dark:border-slate-700'}`}>
                          {msg.role === 'assistant' ? (
                            <ReactMarkdown>{msg.content}</ReactMarkdown>
                          ) : (
                            msg.content
                          )}
                      </div>
                      {msg.meta && !msg.meta.isError && (
                          <div className="flex flex-wrap mt-2 gap-2 text-[11px] font-bold">
                              <span className="bg-white dark:bg-slate-800 text-slate-500 dark:text-slate-400 px-2.5 py-1.5 rounded-md border border-slate-200 dark:border-slate-700 shadow-sm">
                                  Routed to: <span className="text-indigo-600 dark:text-indigo-400 ml-1">{msg.meta.routed_to}</span>
                              </span>
                              <span className="bg-white dark:bg-slate-800 text-slate-500 dark:text-slate-400 px-2.5 py-1.5 rounded-md border border-slate-200 dark:border-slate-700 shadow-sm">
                                  Cost Saved: <span className="text-emerald-600 dark:text-emerald-400 ml-1">${msg.meta.estimated_cost_saved}</span>
                              </span>
                              {msg.meta.cache_hit && (
                                  <span className="bg-amber-50 dark:bg-amber-900/20 text-amber-700 dark:text-amber-400 px-2.5 py-1.5 rounded-md border border-amber-200 dark:border-amber-800/50 shadow-sm flex items-center">
                                      <Zap className="w-3 h-3 mr-1"/> Cache Hit
                                  </span>
                              )}
                              {msg.meta.is_masked && (
                                  <span className="bg-rose-50 dark:bg-rose-900/20 text-rose-700 dark:text-rose-400 px-2.5 py-1.5 rounded-md border border-rose-200 dark:border-rose-800/50 shadow-sm flex items-center">
                                      <Shield className="w-3 h-3 mr-1"/> Data Masked
                                  </span>
                              )}
                          </div>
                      )}
                  </div>
              ))}
              {isLoading && (
                   <div className="flex items-start">
                      <div className="bg-white dark:bg-slate-800 p-4 rounded-2xl rounded-bl-sm border border-slate-200 dark:border-slate-700 shadow-sm text-slate-500 dark:text-slate-400 flex items-center text-sm font-bold">
                          <RefreshCw className="w-4 h-4 animate-spin mr-3 text-indigo-500" /> Gateway Analyzing & Routing...
                      </div>
                   </div>
              )}
           </div>

           <div className="p-5 bg-white dark:bg-slate-800 border-t border-slate-200 dark:border-slate-700">
              <form onSubmit={handleChatSubmit} className="flex gap-4">
                  <input 
                      type="text" 
                      value={prompt}
                      onChange={(e) => setPrompt(e.target.value)}
                      placeholder="Message the Enterprise Proxy..."
                      className="flex-1 bg-slate-50 dark:bg-slate-900 border border-slate-300 dark:border-slate-600 rounded-xl px-5 py-3.5 text-slate-900 dark:text-white placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:bg-white dark:focus:bg-slate-800 transition-all shadow-sm"
                  />
                  <button 
                      type="submit" 
                      disabled={isLoading || (!openaiKey && !geminiKey)}
                      className="bg-indigo-600 hover:bg-indigo-700 disabled:opacity-50 disabled:hover:bg-indigo-600 disabled:cursor-not-allowed text-white px-6 py-3.5 rounded-xl font-bold transition-colors flex items-center shadow-sm"
                  >
                      <Send className="w-5 h-5 mr-2" /> Send
                  </button>
              </form>
           </div>
        </div>
        )}
      </div>
    </div>
  );
}
