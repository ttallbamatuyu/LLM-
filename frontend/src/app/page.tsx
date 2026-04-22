"use client";

import React, { useState } from 'react';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';
import { Send, Shield, Zap, RefreshCw, AlertTriangle, Key } from 'lucide-react';

const mockData = [
  { time: '10:00', originalCost: 0.12, routingCost: 0.03, saved: 0.09 },
  { time: '11:00', originalCost: 0.45, routingCost: 0.15, saved: 0.30 },
  { time: '12:00', originalCost: 0.30, routingCost: 0.05, saved: 0.25 },
  { time: '13:00', originalCost: 0.80, routingCost: 0.20, saved: 0.60 },
  { time: '14:00', originalCost: 0.50, routingCost: 0.10, saved: 0.40 },
];

export default function Dashboard() {
  const [openaiKey, setOpenaiKey] = useState('');
  const [geminiKey, setGeminiKey] = useState('');
  const [activeTab, setActiveTab] = useState('dashboard');

  // Chat Simulator State
  const [prompt, setPrompt] = useState('');
  const [chatLog, setChatLog] = useState<{ role: string, content: string, meta?: any }[]>([]);
  const [isLoading, setIsLoading] = useState(false);

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
      const res = await fetch('http://localhost:8000/v1/chat/completions', {
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
    <div className="min-h-screen bg-slate-50 text-slate-900 p-4 md:p-8 font-sans transition-colors selection:bg-indigo-100 selection:text-indigo-900">
      <div className="max-w-6xl mx-auto">
        <header className="mb-10 flex flex-col md:flex-row md:justify-between md:items-end border-b border-slate-200 pb-6">
          <div>
            <h1 className="text-3xl md:text-4xl font-extrabold tracking-tight text-slate-900">AI Gateway Dashboard <span className="text-indigo-600">V3</span></h1>
            <p className="text-slate-500 mt-2 font-medium">Enterprise-grade LLM Proxy with Security & Caching</p>
          </div>
          <div className="flex bg-white shadow-sm border border-slate-200 rounded-xl p-1 mt-6 md:mt-0">
              <button 
                  className={`px-6 py-2.5 rounded-lg text-sm font-semibold transition-all duration-200 ${activeTab === 'dashboard' ? 'bg-slate-900 text-white shadow-md' : 'text-slate-500 hover:text-slate-900 hover:bg-slate-50'}`}
                  onClick={() => setActiveTab('dashboard')}
              >
                  Analytics
              </button>
              <button 
                  className={`px-6 py-2.5 rounded-lg text-sm font-semibold transition-all duration-200 flex items-center ml-1 ${activeTab === 'playground' ? 'bg-indigo-600 text-white shadow-md' : 'text-slate-500 hover:text-slate-900 hover:bg-slate-50'}`}
                  onClick={() => setActiveTab('playground')}
              >
                  <Zap className="w-4 h-4 mr-2" />
                  Playground
              </button>
          </div>
        </header>

        {activeTab === 'dashboard' && (
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8 animate-in slide-in-from-bottom-4 fade-in duration-500">
          <section className="lg:col-span-1 bg-white rounded-2xl p-8 border border-slate-200 shadow-sm">
            <h2 className="text-lg font-bold mb-2 text-slate-900 flex items-center"><Key className="w-5 h-5 mr-2 text-indigo-500"/> Bring Your Own Key</h2>
            <p className="text-sm text-slate-500 mb-8 leading-relaxed">Enter your API keys to enable intelligent routing. Keys are stored locally in your browser session.</p>
            
            <div className="space-y-5">
              <div>
                <label className="block text-sm font-semibold text-slate-700 mb-1.5">OpenAI API Key</label>
                <input 
                  type="password" 
                  value={openaiKey}
                  onChange={(e) => setOpenaiKey(e.target.value)}
                  className="w-full bg-slate-50 border border-slate-300 rounded-xl py-2.5 px-4 text-slate-900 placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 transition-shadow"
                  placeholder="sk-..."
                />
              </div>
              <div>
                <label className="block text-sm font-semibold text-slate-700 mb-1.5">Gemini API Key</label>
                <input 
                  type="password" 
                  value={geminiKey}
                  onChange={(e) => setGeminiKey(e.target.value)}
                  className="w-full bg-slate-50 border border-slate-300 rounded-xl py-2.5 px-4 text-slate-900 placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-emerald-500 focus:border-emerald-500 transition-shadow"
                  placeholder="AIzaSy..."
                />
              </div>
              <div className="p-5 bg-indigo-50/50 rounded-xl border border-indigo-100 mt-6">
                <h3 className="text-xs font-bold text-indigo-900 mb-3 uppercase tracking-wider">V3 Active Features</h3>
                <ul className="text-sm font-medium text-indigo-700 space-y-3">
                    <li className="flex items-center"><Shield className="w-4 h-4 text-indigo-500 mr-2.5"/> PII & Internal Data Scrubbing</li>
                    <li className="flex items-center"><RefreshCw className="w-4 h-4 text-blue-500 mr-2.5"/> Intelligent Fallback Routing</li>
                    <li className="flex items-center"><Zap className="w-4 h-4 text-amber-500 mr-2.5"/> Semantic Vector Caching</li>
                </ul>
              </div>
            </div>
          </section>

          <section className="lg:col-span-2 bg-white rounded-2xl p-8 border border-slate-200 shadow-sm flex flex-col">
            <div className="flex justify-between items-center mb-8">
              <h2 className="text-lg font-bold flex items-center text-slate-900">
                <span className="relative flex h-3 w-3 mr-3">
                  <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75"></span>
                  <span className="relative inline-flex rounded-full h-3 w-3 bg-emerald-500"></span>
                </span>
                Real-time API Cost Comparison
              </h2>
            </div>
            <div className="flex-1 w-full min-h-[300px]">
              <ResponsiveContainer width="100%" height="100%">
                <LineChart data={mockData}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" vertical={false} />
                  <XAxis dataKey="time" stroke="#64748b" axisLine={false} tickLine={false} dy={10} fontSize={12} />
                  <YAxis stroke="#64748b" tickFormatter={(value) => `$${value}`} axisLine={false} tickLine={false} dx={-10} fontSize={12} />
                  <Tooltip 
                    contentStyle={{ backgroundColor: '#ffffff', border: '1px solid #e2e8f0', borderRadius: '12px', color: '#0f172a', boxShadow: '0 4px 6px -1px rgb(0 0 0 / 0.1)', fontSize: '13px', fontWeight: '500' }} 
                  />
                  <Line type="monotone" dataKey="originalCost" name="Cost Without Proxy" stroke="#ef4444" strokeWidth={3} dot={{r: 4, strokeWidth: 2}} activeDot={{r: 6}} />
                  <Line type="monotone" dataKey="routingCost" name="Cost With Proxy" stroke="#10b981" strokeWidth={3} dot={{r: 4, strokeWidth: 2}} activeDot={{r: 6}} />
                </LineChart>
              </ResponsiveContainer>
            </div>
          </section>
        </div>
        )}

        {activeTab === 'playground' && (
        <div className="bg-white rounded-2xl border border-slate-200 shadow-sm flex flex-col h-[75vh] animate-in slide-in-from-bottom-4 fade-in duration-500 overflow-hidden">
           <div className="bg-slate-50 border-b border-slate-200 p-5 flex justify-between items-center">
              <h2 className="text-lg font-bold flex items-center text-slate-900">
                  <Zap className="w-5 h-5 text-indigo-500 mr-2.5"/> API Routing Simulator
              </h2>
              <div className="text-xs font-semibold px-3 py-1.5 rounded-full flex items-center bg-white border border-slate-200 shadow-sm">
                  {openaiKey || geminiKey ? (
                      <><span className="w-2 h-2 rounded-full bg-emerald-500 mr-2"></span> <span className="text-slate-600">Keys Loaded</span></>
                  ) : (
                      <><span className="w-2 h-2 rounded-full bg-red-500 mr-2"></span> <span className="text-slate-600">Keys Missing</span></>
                  )}
              </div>
           </div>

           <div className="flex-1 overflow-y-auto p-6 space-y-6 bg-slate-50/50">
              {chatLog.length === 0 && (
                  <div className="flex flex-col items-center justify-center h-full text-center text-slate-500 space-y-4">
                      <div className="w-16 h-16 bg-white shadow-sm border border-slate-200 rounded-full flex items-center justify-center mb-2">
                        <Zap className="w-8 h-8 text-indigo-500" />
                      </div>
                      <p className="text-lg font-bold text-slate-700">Try asking a question to test the routing!</p>
                      <p className="text-sm font-medium text-slate-500 max-w-md">The Gateway will analyze your prompt, mask sensitive data (e.g. "NEBULA", "PROJECT4"), and stream the optimal response.</p>
                  </div>
              )}
              {chatLog.map((msg, idx) => (
                  <div key={idx} className={`flex flex-col ${msg.role === 'user' ? 'items-end' : 'items-start'}`}>
                      <div className={`max-w-[75%] p-4 rounded-2xl text-[15px] leading-relaxed shadow-sm font-medium ${msg.role === 'user' ? 'bg-indigo-600 text-white rounded-br-sm' : 'bg-white text-slate-800 rounded-bl-sm border border-slate-200'}`}>
                          {msg.content}
                      </div>
                      {msg.meta && !msg.meta.isError && (
                          <div className="flex flex-wrap mt-2 gap-2 text-[11px] font-bold">
                              <span className="bg-white text-slate-500 px-2.5 py-1.5 rounded-md border border-slate-200 shadow-sm">
                                  Routed to: <span className="text-indigo-600 ml-1">{msg.meta.routed_to}</span>
                              </span>
                              <span className="bg-white text-slate-500 px-2.5 py-1.5 rounded-md border border-slate-200 shadow-sm">
                                  Cost Saved: <span className="text-emerald-600 ml-1">${msg.meta.estimated_cost_saved}</span>
                              </span>
                              {msg.meta.cache_hit && (
                                  <span className="bg-amber-50 text-amber-700 px-2.5 py-1.5 rounded-md border border-amber-200 shadow-sm flex items-center">
                                      <Zap className="w-3 h-3 mr-1"/> Cache Hit
                                  </span>
                              )}
                              {msg.meta.is_masked && (
                                  <span className="bg-rose-50 text-rose-700 px-2.5 py-1.5 rounded-md border border-rose-200 shadow-sm flex items-center">
                                      <Shield className="w-3 h-3 mr-1"/> Data Masked
                                  </span>
                              )}
                          </div>
                      )}
                  </div>
              ))}
              {isLoading && (
                   <div className="flex items-start">
                      <div className="bg-white p-4 rounded-2xl rounded-bl-sm border border-slate-200 shadow-sm text-slate-500 flex items-center text-sm font-bold">
                          <RefreshCw className="w-4 h-4 animate-spin mr-3 text-indigo-500" /> Gateway Analyzing & Routing...
                      </div>
                   </div>
              )}
           </div>

           <div className="p-5 bg-white border-t border-slate-200">
              <form onSubmit={handleChatSubmit} className="flex gap-4">
                  <input 
                      type="text" 
                      value={prompt}
                      onChange={(e) => setPrompt(e.target.value)}
                      placeholder="Message the Enterprise Proxy..."
                      className="flex-1 bg-slate-50 border border-slate-300 rounded-xl px-5 py-3.5 text-slate-900 placeholder-slate-400 font-medium focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:bg-white transition-all shadow-sm"
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
