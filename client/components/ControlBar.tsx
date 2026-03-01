'use client';

interface ControlBarProps {
  micEnabled: boolean;
  cameraEnabled: boolean;
  screenSharing: boolean;
  isConnected: boolean;
  onToggleMic: () => void;
  onToggleCamera: () => void;
  onToggleScreenShare: () => void;
  onEndCall: () => void;
}

export function ControlBar({
  micEnabled,
  cameraEnabled,
  screenSharing,
  isConnected,
  onToggleMic,
  onToggleCamera,
  onToggleScreenShare,
  onEndCall,
}: ControlBarProps) {
  return (
    <div className="fixed bottom-0 left-0 right-0 bg-white border-t border-slate-200 z-50">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
        <div className="flex items-center justify-center gap-3 sm:gap-4">
          {/* Microphone Toggle */}
          <button 
            onClick={onToggleMic}
            disabled={!isConnected}
            className={`group p-3 rounded-lg border border-slate-200 transition-colors duration-150 disabled:opacity-50 disabled:cursor-not-allowed ${
              micEnabled 
                ? 'bg-white text-slate-700 hover:bg-slate-50' 
                : 'bg-red-50 text-red-700 hover:bg-red-100'
            }`}
            aria-label={micEnabled ? 'Mute microphone' : 'Unmute microphone'}
            title={micEnabled ? 'Mute' : 'Unmute'}
          >
            {micEnabled ? (
              <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 11a7 7 0 01-7 7m0 0a7 7 0 01-7-7m7 7v4m0 0H8m4 0h4m-4-8a3 3 0 01-3-3V5a3 3 0 116 0v6a3 3 0 01-3 3z" />
              </svg>
            ) : (
              <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5.586 15H4a1 1 0 01-1-1v-4a1 1 0 011-1h1.586l4.707-4.707C10.923 3.663 12 4.109 12 5v14c0 .891-1.077 1.337-1.707.707L5.586 15z" />
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 14l2-2m0 0l2-2m-2 2l-2-2m2 2l2 2" />
              </svg>
            )}
          </button>

          {/* Camera Toggle */}
          <button 
            onClick={onToggleCamera}
            disabled={!isConnected}
            className={`group p-3 rounded-lg border border-slate-200 transition-colors duration-150 disabled:opacity-50 disabled:cursor-not-allowed ${
              cameraEnabled 
                ? 'bg-white text-slate-700 hover:bg-slate-50' 
                : 'bg-red-50 text-red-700 hover:bg-red-100'
            }`}
            aria-label={cameraEnabled ? 'Turn off camera' : 'Turn on camera'}
            title={cameraEnabled ? 'Turn off camera' : 'Turn on camera'}
          >
            {cameraEnabled ? (
              <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 10l4.553-2.276A1 1 0 0121 8.618v6.764a1 1 0 01-1.447.894L15 14M5 18h8a2 2 0 002-2V8a2 2 0 00-2-2H5a2 2 0 00-2 2v8a2 2 0 002 2z" />
              </svg>
            ) : (
              <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M18.364 18.364A9 9 0 005.636 5.636m12.728 12.728A9 9 0 015.636 5.636m12.728 12.728L5.636 5.636" />
              </svg>
            )}
          </button>

          {/* Screen Share Toggle */}
          <button 
            onClick={onToggleScreenShare}
            disabled={!isConnected}
            className={`group p-3 rounded-lg border border-slate-200 transition-colors duration-150 disabled:opacity-50 disabled:cursor-not-allowed ${
              screenSharing 
                ? 'bg-slate-100 text-slate-700 hover:bg-slate-200' 
                : 'bg-white text-slate-700 hover:bg-slate-50'
            }`}
            aria-label={screenSharing ? 'Stop sharing screen' : 'Share screen'}
            title={screenSharing ? 'Stop sharing' : 'Share screen'}
          >
            {screenSharing ? (
              <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9.75 17L9 20l-1 1h8l-1-1-.75-3M3 13h18M5 17h14a2 2 0 002-2V5a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" />
              </svg>
            ) : (
              <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9.75 17L9 20l-1 1h8l-1-1-.75-3M3 13h18M5 17h14a2 2 0 002-2V5a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" />
              </svg>
            )}
          </button>

        </div>
      </div>
    </div>
  );
}
