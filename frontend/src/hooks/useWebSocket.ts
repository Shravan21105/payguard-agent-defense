import { useEffect, useState } from 'react';
import { payguardWs, type WebSocketStatus } from '../services/websocket';
import type { PayguardEvent } from '../types';

export function useWebSocket(categories: string[] | string = 'all') {
  const [connectionState, setConnectionState] = useState<WebSocketStatus>(payguardWs.getStatus());
  const [lastMessage, setLastMessage] = useState<PayguardEvent | null>(null);

  useEffect(() => {
    // Connect to centralized WebSocket service
    payguardWs.connect();

    const unsubscribeStatus = payguardWs.onStatusChange((status) => {
      setConnectionState(status);
    });

    const unsubscribeEvents = payguardWs.subscribe(categories, (event) => {
      setLastMessage(event);
    });

    return () => {
      unsubscribeStatus();
      unsubscribeEvents();
    };
  }, [JSON.stringify(categories)]);

  return {
    isConnected: connectionState === 'CONNECTED',
    connectionState,
    lastMessage,
    subscribe: payguardWs.subscribe.bind(payguardWs),
  };
}
