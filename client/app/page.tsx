'use client';

import { useState, useCallback, useEffect } from 'react';
import { StreamVideo, StreamVideoClient, StreamCall, SpeakerLayout, CallControls, Call } from '@stream-io/video-react-sdk';
import '@stream-io/video-react-sdk/dist/css/styles.css';
import { ConnectionStatus } from '@/components/ConnectionStatus';
import { TranscriptPanel, TranscriptMessage } from '@/components/TranscriptPanel';

// Get API base URL
const apiBase = process.env.NEXT_PUBLIC_API_BASE || 'http://localhost:8000';
const xrayUploadEndpoint = process.env.NEXT_PUBLIC_XRAY_UPLOAD_ENDPOINT || `${apiBase}/upload_xray`;
const apiKey = process.env.NEXT_PUBLIC_STREAM_API_KEY || 'YOUR_STREAM_KEY';

export default function Home() {
  const [client, setClient] = useState<StreamVideoClient | null>(null);
  const [call, setCall] = useState<Call | null>(null);
  const [connectionStatus, setConnectionStatus] = useState<'disconnected' | 'connecting' | 'connected' | 'error'>('disconnected');
  const [messages, setMessages] = useState<TranscriptMessage[]>([]);

  const [xrayFile, setXrayFile] = useState<File | null>(null);
  const [xrayUploading, setXrayUploading] = useState(false);
  const [xrayUploadStatus, setXrayUploadStatus] = useState<string | null>(null);
  const [xrayUploadError, setXrayUploadError] = useState<string | null>(null);
  const [xrayPreviewUrl, setXrayPreviewUrl] = useState<string | null>(null);
  const [xrayStatusIndex, setXrayStatusIndex] = useState(0);
  const xrayStatusMessages = ['Scanning image parameters...', 'Analyzing indicators...', 'Validating quality...', 'Finalizing triage...'];

  const addMessage = useCallback((speaker: 'user' | 'bot', text: string) => {
    const trimmed = text.trim();
    if (!trimmed) return;
    const newMessage: TranscriptMessage = {
      id: `${Date.now()}-${Math.random().toString(36).slice(2, 7)}`,
      speaker,
      text: trimmed,
      timestamp: new Date().toISOString(),
    };
    setMessages((prev) => [...prev, newMessage]);
  }, []);

  const startSession = async () => {
    if (connectionStatus === 'connected' || connectionStatus === 'connecting') return;
    setConnectionStatus('connecting');

    try {
      // 1. Get Token and Call ID from backend
      const roomResponse = await fetch(`${apiBase}/create-room`, { method: 'POST' });
      if (!roomResponse.ok) throw new Error('Failed to create Stream room');
      const roomData = await roomResponse.json();
      const callId = roomData.url;
      const token = roomData.token;

      // 2. Initialize Stream Client
      const newClient = new StreamVideoClient({ apiKey, token, user: { id: 'tb-screener-user', name: 'Patient' } });
      setClient(newClient);

      // 3. Create and Join Call
      const newCall = newClient.call('default', callId);
      await newCall.join({ create: true });
      setCall(newCall);

      // 4. Start Bot via Backend
      const startResponse = await fetch(`${apiBase}/start-bot`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ room_url: callId, token }),
      });
      if (!startResponse.ok) throw new Error('Failed to start AI Agent');

      setConnectionStatus('connected');

      // SSE subscription
      const eventsUrl = `${apiBase}/events`;
      const eventSource = new EventSource(eventsUrl);
      eventSource.onmessage = (evt) => {
        try {
          const payload = JSON.parse(evt.data);
          const text = payload?.text ?? '';
          if (text) addMessage('bot', text);
        } catch (e) {
          console.error(e);
        }
      };

    } catch (err) {
      console.error(err);
      setConnectionStatus('error');
    }
  };

  const stopSession = async () => {
    if (call) {
      try {
        await call.leave();
      } catch (err) {
        console.warn("Call already left", err);
      }
      setCall(null);
    }
    if (client) {
      try {
        await client.disconnectUser();
      } catch (err) {
        console.warn("Client already disconnected", err);
      }
      setClient(null);
    }
    setConnectionStatus('disconnected');
    setMessages([]);
  };

  const uploadXray = async () => {
    if (!xrayFile) return;
    setXrayUploading(true);
    setXrayUploadStatus(null);
    setXrayUploadError(null);

    try {
      const formData = new FormData();
      formData.append('file', xrayFile);
      const response = await fetch(xrayUploadEndpoint, { method: 'POST', body: formData });
      if (!response.ok) throw new Error('Upload failed');
      const data = await response.json();
      setXrayUploadStatus(`Uploaded: ${data.path}`);
      setXrayFile(null);
    } catch (error) {
      setXrayUploadError(error instanceof Error ? error.message : 'Upload failed');
    } finally {
      setXrayUploading(false);
    }
  };

  useEffect(() => {
    if (!xrayFile) { setXrayPreviewUrl(null); return; }
    const url = URL.createObjectURL(xrayFile);
    setXrayPreviewUrl(url);
    return () => URL.revokeObjectURL(url);
  }, [xrayFile]);

  useEffect(() => {
    if (!xrayUploading) { setXrayStatusIndex(0); return; }
    const interval = setInterval(() => { setXrayStatusIndex((prev) => (prev + 1) % xrayStatusMessages.length); }, 2000);
    return () => clearInterval(interval);
  }, [xrayUploading, xrayStatusMessages.length]);

  return (
    <div className="min-h-screen bg-slate-50 font-sans">
      <header className="fixed top-0 left-0 right-0 z-50 bg-white border-b border-slate-200">
        <div className="absolute left-20 top-0 h-16 flex items-center">
          <span className="text-xl font-medium text-slate-900">BigTB6</span>
        </div>
        <div className="absolute right-0 top-0 h-16 px-4 sm:px-6 lg:px-8 flex items-center gap-3">
          <button
            onClick={connectionStatus === 'connected' ? stopSession : startSession}
            className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors ${connectionStatus === 'connected' ? 'bg-slate-100 text-slate-700 hover:bg-slate-200' : 'bg-[#099c8f] text-white hover:bg-[#07897d]'
              }`}
          >
            {connectionStatus === 'connected' ? 'Disconnect' : 'Connect'}
          </button>
          <ConnectionStatus status={connectionStatus} />
        </div>
      </header>
      <main className="pt-20 pb-20 max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">

        {/* Stream Video Context */}
        {client && call ? (
          <StreamVideo client={client}>
            <div className="str-video">
              <StreamCall call={call}>
                <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 mt-6">

                  {/* Main View */}
                  <div className="lg:col-span-2 relative aspect-video bg-slate-900 rounded-lg overflow-hidden border border-slate-800 shadow-sm flex flex-col">
                    <SpeakerLayout />
                    <div className="absolute bottom-4 left-0 right-0 flex justify-center">
                      <CallControls />
                    </div>
                  </div>

                  {/* Side Panel (Upload) */}
                  <div className="lg:col-span-1">
                    <div className="rounded-lg border border-slate-200 bg-white p-4 shadow-sm mb-4">
                      <div className="text-sm font-medium text-slate-900">Chest X-ray Upload</div>
                      <p className="mt-1 text-xs text-slate-600">Upload an X-ray image for analysis.</p>
                      <div className="mt-3 relative">
                        <input
                          type="file"
                          accept="image/*"
                          onChange={(e) => setXrayFile(e.target.files?.[0] ?? null)}
                          className="block w-full text-xs text-slate-600 file:mr-3 file:rounded-lg file:bg-slate-100 file:px-3 file:py-2 file:border-0 hover:file:bg-slate-200 mb-2"
                        />
                        <button
                          onClick={uploadXray}
                          disabled={!xrayFile || xrayUploading}
                          className="w-full px-3 py-2 rounded-lg bg-[#099c8f] text-white text-xs font-medium hover:bg-[#07897d] disabled:opacity-60 disabled:cursor-not-allowed"
                        >
                          Upload
                        </button>
                      </div>
                      {xrayUploadStatus && <p className="mt-2 text-xs text-emerald-700">{xrayUploadStatus}</p>}
                    </div>

                    <div className="rounded-lg border border-slate-200 bg-white p-4 shadow-sm">
                      <div className="text-sm font-medium text-slate-900">Image Analysis Panel</div>
                      <p className="mt-1 text-xs text-slate-600 mb-2">Use your camera for AI anemia detection.</p>
                      <img src="/baymax.png" alt="Assistant avatar" className="w-20 h-20 rounded-full mx-auto" />
                    </div>
                  </div>

                </div>
              </StreamCall>
            </div>
          </StreamVideo>
        ) : (
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 mt-6">
            <div className="lg:col-span-2 relative aspect-video bg-slate-900 rounded-lg flex items-center justify-center border border-slate-800">
              <p className="text-slate-100 font-medium">Click Connect to Start Video Screening</p>
            </div>
          </div>
        )}

        <TranscriptPanel messages={messages} />
      </main>

    </div>
  );
}
