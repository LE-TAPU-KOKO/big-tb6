'use client';

import { useRef, useEffect, useState } from 'react';

interface VideoConsultationProps {
  localStream: MediaStream | null;
  remoteStream: MediaStream | null;
  isConnected: boolean;
  sidePanel?: React.ReactNode;
}

export function VideoConsultation({ localStream, remoteStream, isConnected, sidePanel }: VideoConsultationProps) {
  const localVideoRef = useRef<HTMLVideoElement>(null);
  const remoteVideoRef = useRef<HTMLVideoElement>(null);

  useEffect(() => {
    if (localVideoRef.current && localStream) {
      localVideoRef.current.srcObject = localStream;
    }
  }, [localStream]);

  useEffect(() => {
    if (remoteVideoRef.current && remoteStream) {
      remoteVideoRef.current.srcObject = remoteStream;
    }
  }, [remoteStream]);

  return (
    <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 mt-6">
      {/* Main Video Area - User View */}
      <div className="lg:col-span-2">
        <div className="relative aspect-video bg-slate-900 rounded-lg overflow-hidden border border-slate-800 shadow-sm">
          
          {/* Local Video (User) */}
          {localStream ? (
            <video
              ref={localVideoRef}
              autoPlay
              playsInline
              muted
              className="w-full h-full object-cover"
            />
          ) : (
            /* Placeholder when camera off */
            <div className="absolute inset-0 flex items-center justify-center">
              <div className="text-center">
                <div className="w-20 h-20 mx-auto mb-4 bg-slate-800 rounded-lg flex items-center justify-center">
                  <svg className="w-10 h-10 text-slate-200" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" />
                  </svg>
                </div>
                <p className="text-slate-100 text-lg font-medium">Camera off</p>
                <p className="text-slate-400 text-sm mt-1">Enable camera to preview</p>
              </div>
            </div>
          )}
        </div>
      </div>

      {/* AI Placeholder Preview */}
      <div className="lg:col-span-1">
        <div className="relative aspect-video bg-slate-100 rounded-lg overflow-hidden border border-slate-200 shadow-sm">
          <img
            src="/baymax.png"
            alt="Assistant"
            className="w-full h-full object-cover"
          />
          <div className="absolute bottom-2 left-2 bg-white/90 px-2 py-1 rounded-md text-xs text-slate-600 border border-slate-200">
            Status: {isConnected ? 'Listening' : 'Idle'}
          </div>
        </div>
        {sidePanel ? <div className="mt-4">{sidePanel}</div> : null}
      </div>
    </div>
  );
}
