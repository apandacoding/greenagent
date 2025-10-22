import { useEffect, useRef, useState } from 'react';
import type { Message } from '../types/chat';

const WS_URL = 'ws://localhost:8000/ws';

export default function useWebSocket() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [isConnected, setIsConnected] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const wsRef = useRef<WebSocket | null>(null);

  useEffect(() => {
    // Connect to WebSocket
    const ws = new WebSocket(WS_URL);
    wsRef.current = ws;

    ws.onopen = () => {
      console.log('WebSocket connected');
      setIsConnected(true);
    };

    ws.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        
        // Handle different message types
        if (data.type === 'message' && data.content) {
          const newMessage: Message = {
            id: Date.now().toString(),
            role: 'assistant',
            content: data.content,
            timestamp: new Date(),
          };
          setMessages((prev) => [...prev, newMessage]);
          setIsLoading(false);
        } else if (data.type === 'error') {
          console.error('WebSocket error:', data.error);
          setIsLoading(false);
        }
      } catch (error) {
        console.error('Failed to parse message:', error);
        setIsLoading(false);
      }
    };

    ws.onerror = (error) => {
      console.error('WebSocket error:', error);
      setIsConnected(false);
      setIsLoading(false);
    };

    ws.onclose = () => {
      console.log('WebSocket disconnected');
      setIsConnected(false);
      setIsLoading(false);
    };

    // Cleanup on unmount
    return () => {
      ws.close();
    };
  }, []);

  const sendMessage = (content: string) => {
    if (!wsRef.current || wsRef.current.readyState !== WebSocket.OPEN) {
      console.error('WebSocket is not connected');
      return;
    }

    // Add user message to chat
    const userMessage: Message = {
      id: Date.now().toString(),
      role: 'user',
      content,
      timestamp: new Date(),
    };
    setMessages((prev) => [...prev, userMessage]);
    setIsLoading(true);

    // Send to server
    wsRef.current.send(JSON.stringify({ message: content }));
  };

  return {
    messages,
    isConnected,
    isLoading,
    sendMessage,
  };
}

