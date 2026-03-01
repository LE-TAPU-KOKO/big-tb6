'use client';

interface ConnectionStatusProps {
  status: 'disconnected' | 'connecting' | 'connected' | 'error';
}

export function ConnectionStatus({ status }: ConnectionStatusProps) {
  const statusConfig = {
    disconnected: { 
      color: 'bg-slate-400', 
      text: 'Disconnected', 
      textColor: 'text-slate-600'
    },
    connecting: { 
      color: 'bg-amber-400', 
      text: 'Connecting...', 
      textColor: 'text-amber-700'
    },
    connected: { 
      color: 'bg-[#099c8f]', 
      text: 'Connected', 
      textColor: 'text-[#0a7f75]'
    },
    error: { 
      color: 'bg-red-500', 
      text: 'Error', 
      textColor: 'text-red-600'
    }
  };
  
  const config = statusConfig[status];
  
  return (
    <div className="flex items-center gap-2">
      <div className={`w-2.5 h-2.5 rounded-full ${config.color}`} />
      <span className={`text-sm font-medium ${config.textColor}`}>{config.text}</span>
    </div>
  );
}
