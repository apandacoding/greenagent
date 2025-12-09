"""Event queue for bridging sync tool calls with async WebSocket streaming."""
import asyncio
import threading
from typing import Dict, Any, Optional
from queue import Queue, Empty
import logging

logger = logging.getLogger(__name__)


class EventQueue:
    """Thread-safe queue for events from sync contexts."""
    
    def __init__(self):
        """Initialize event queue."""
        self._queue: Queue = Queue()
        self._subscribers: list = []
        self._running = False
        self._thread: Optional[threading.Thread] = None
    
    def put(self, event: Dict[str, Any]):
        """Put event in queue (thread-safe, can be called from sync context)."""
        self._queue.put(event)
    
    def subscribe(self, callback):
        """Subscribe async callback to receive events."""
        self._subscribers.append(callback)
        if not self._running:
            self._start_processor()
    
    def unsubscribe(self, callback):
        """Unsubscribe callback from receiving events."""
        if callback in self._subscribers:
            self._subscribers.remove(callback)
            logger.debug(f"[EventQueue] Unsubscribed callback")
    
    def _start_processor(self):
        """Start async event processor in background."""
        if self._running:
            return
        
        self._running = True
        
        def run_processor():
            """Run event processor in new event loop."""
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            async def process_events():
                while self._running:
                    try:
                        # Wait for event with timeout
                        try:
                            event = self._queue.get(timeout=0.1)
                        except Empty:
                            await asyncio.sleep(0.1)
                            continue
                        
                        # Send to all subscribers
                        logger.info(f"[EventQueue] Processing event: {event.get('type', 'unknown')}, subscribers: {len(self._subscribers)}")
                        disconnected_subscribers = []
                        for callback in self._subscribers.copy():  # Copy to avoid modification during iteration
                            try:
                                logger.info(f"[EventQueue] Sending event to subscriber")
                                await callback(event)
                                logger.info(f"[EventQueue] Event sent successfully")
                            except Exception as e:
                                error_str = str(e)
                                # Check if it's a connection/disconnect error
                                if any(keyword in error_str.lower() for keyword in ["disconnect", "connection closed", "closed", "1006", "1012", "clientdisconnected", "close message", "not connected"]):
                                    logger.debug(f"[EventQueue] Subscriber disconnected: {error_str}")
                                    # Mark for removal but don't remove during iteration
                                    disconnected_subscribers.append(callback)
                                else:
                                    logger.error(f"[EventQueue] Error in event subscriber: {e}", exc_info=True)
                        
                        # Remove disconnected subscribers
                        for subscriber in disconnected_subscribers:
                            if subscriber in self._subscribers:
                                self._subscribers.remove(subscriber)
                                logger.debug(f"[EventQueue] Removed disconnected subscriber")
                    except Exception as e:
                        logger.error(f"Error processing event: {e}")
                        await asyncio.sleep(0.1)
            
            try:
                loop.run_until_complete(process_events())
            finally:
                loop.close()
        
        self._thread = threading.Thread(target=run_processor, daemon=True)
        self._thread.start()
    
    def stop(self):
        """Stop event processor."""
        self._running = False


# Global event queue
_event_queue: Optional[EventQueue] = None


def get_event_queue() -> EventQueue:
    """Get global event queue instance."""
    global _event_queue
    if _event_queue is None:
        _event_queue = EventQueue()
    return _event_queue

