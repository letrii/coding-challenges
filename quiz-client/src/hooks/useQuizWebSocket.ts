import { useEffect, useRef, useState, useCallback } from 'react';
import { WebSocketService } from '../services/WebSocketService';
import { WebSocketMessage } from '../types/quiz';

interface UseQuizWebSocketProps {
  sessionId: string;
  userId: string;
  onMessage: (message: WebSocketMessage) => void;
  onConnect?: () => void;
  onDisconnect?: () => void;
}

export const useQuizWebSocket = ({
                                   sessionId,
                                   userId,
                                   onMessage,
                                   onConnect,
                                   onDisconnect,
                                 }: UseQuizWebSocketProps) => {
  const [isConnected, setIsConnected] = useState(false);
  const wsRef = useRef<WebSocketService | null>(null);
  const isInitialized = useRef(false);

  const handleConnect = useCallback(() => {
    console.log('[WS] Connected successfully');
    setIsConnected(true);
    onConnect?.();
  }, [onConnect]);

  const handleDisconnect = useCallback(() => {
    console.log('[WS] Disconnected');
    setIsConnected(false);
    onDisconnect?.();
  }, [onDisconnect]);

  const handleMessage = useCallback((data: WebSocketMessage) => {
    console.log('[WS] Received:', data);
    onMessage(data);
  }, [onMessage]);

  useEffect(() => {
    if (isInitialized.current) {
      console.log('[WS] Already initialized, skipping...');
      return;
    }

    console.log('[WS] Initializing WebSocket service...');
    isInitialized.current = true;

    const wsUrl = `ws://${window.location.hostname}:8000/api/v1/quizzes/sessions/${sessionId}/ws/${userId}`;
    wsRef.current = new WebSocketService(wsUrl, {
      pingInterval: 30000,
      reconnectDelay: 3000
    });

    wsRef.current.on('connected', handleConnect);
    wsRef.current.on('disconnected', handleDisconnect);
    wsRef.current.on('message', handleMessage);

    wsRef.current.connect();

    return () => {
      console.log('[WS] Cleaning up WebSocket service...');
      if (wsRef.current) {
        wsRef.current.removeAllListeners();
        wsRef.current.disconnect();
        wsRef.current = null;
      }
      isInitialized.current = false;
    };
  }, []); // Empty dependency array to run only once

  const sendMessage = useCallback((message: unknown) => {
    return wsRef.current?.send(message) ?? false;
  }, []);

  const reconnect = useCallback(() => {
    console.log('[WS] Manual reconnect triggered');
    wsRef.current?.connect();
  }, []);

  return { isConnected, sendMessage, reconnect };
};