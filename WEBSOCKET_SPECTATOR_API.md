# WebSocket Spectator API

## Overview

This document describes the WebSocket API for spectators (viewers) who want to watch live match updates in real-time. Spectators have read-only access and receive broadcasts of all match events, frame updates, and administrative changes.

## Connection

**WebSocket URL:** `ws://localhost:8000/ws/match/<match_id>/`

**No Authentication Required:** Spectator connections are public and do not require authentication.

**Example:**
```
ws://localhost:8000/ws/match/123/
```

---

## Connection Flow

### 1. Connect

When you connect to the WebSocket, you'll immediately receive the current match state:

```json
{
  "type": "match_state",
  "data": {
    "id": 123,
    "player1": {
      "id": 1,
      "display_name": "Player One",
      "full_name": "John Doe"
    },
    "player2": {
      "id": 2,
      "display_name": "Player Two",
      "full_name": "Jane Smith"
    },
    "frames_to_win": 5,
    "match_frames": [
      {
        "id": 12,
        "frame_number": 1,
        "winner": null,
        "events": [...]
      }
    ]
  }
}
```

### 2. Keep-Alive (Ping/Pong)

Send ping messages to keep the connection alive:

**Send:**
```json
{
  "type": "ping"
}
```

**Receive:**
```json
{
  "type": "pong"
}
```

---

## Broadcast Events

Spectators receive the following broadcast events in real-time:

### 1. Match Update

Sent when match details are updated (e.g., frames_to_win, broadcast URL).

```json
{
  "type": "match_update",
  "data": {
    "id": 123,
    "frames_to_win": 5,
    "broadcastURL": "https://youtube.com/watch?v=..."
  }
}
```

### 2. Frame Update

Sent when a frame is created, updated, or ended.

```json
{
  "type": "frame_update",
  "data": {
    "id": 12,
    "frame_number": 1,
    "winner": {
      "id": 1,
      "display_name": "Player One"
    },
    "player1_ball_group": "full",
    "player2_ball_group": "striped",
    "events": [...]
  }
}
```

### 3. Event Created

Sent when a new match event occurs (balls potted, foul, etc.).

```json
{
  "type": "event_created",
  "data": {
    "id": 456,
    "eventType": "balls_potted",
    "timestamp": "2025-11-17T14:30:00Z",
    "player": {
      "id": 1,
      "display_name": "Player One"
    },
    "ball_ids": ["1", "2"],
    "turn_number": 5
  }
}
```

### 4. Event Removed

Sent when a single event is removed by bíró.

```json
{
  "type": "event_removed",
  "data": {
    "event_id": 456,
    "frame_ids": [12]
  }
}
```

### 5. Events Removed (Multiple)

Sent when multiple events are removed in one action.

```json
{
  "type": "events_removed",
  "data": {
    "frame_id": 12,
    "removed_event_ids": [456, 457, 458],
    "count": 3
  }
}
```

### 6. Frame Events Cleared

Sent when all events are cleared from a frame.

```json
{
  "type": "frame_events_cleared",
  "data": {
    "frame_id": 12,
    "cleared_event_ids": [450, 451, 452, 453, 454],
    "count": 5
  }
}
```

---

## Implementation Examples

### JavaScript/TypeScript Example

```javascript
class MatchSpectator {
  constructor(matchId) {
    this.matchId = matchId;
    this.ws = null;
    this.reconnectAttempts = 0;
    this.maxReconnectAttempts = 5;
  }

  connect() {
    this.ws = new WebSocket(`ws://localhost:8000/ws/match/${this.matchId}/`);
    
    this.ws.onopen = () => {
      console.log('Connected to match');
      this.reconnectAttempts = 0;
      this.startPingInterval();
    };

    this.ws.onmessage = (event) => {
      const data = JSON.parse(event.data);
      this.handleMessage(data);
    };

    this.ws.onerror = (error) => {
      console.error('WebSocket error:', error);
    };

    this.ws.onclose = () => {
      console.log('Disconnected from match');
      this.stopPingInterval();
      this.attemptReconnect();
    };
  }

  handleMessage(data) {
    switch(data.type) {
      case 'match_state':
        this.updateMatchState(data.data);
        break;
      
      case 'match_update':
        this.updateMatchDetails(data.data);
        break;
      
      case 'frame_update':
        this.updateFrame(data.data);
        break;
      
      case 'event_created':
        this.addEvent(data.data);
        break;
      
      case 'event_removed':
        this.removeEvent(data.data.event_id);
        break;
      
      case 'events_removed':
        this.removeMultipleEvents(data.data.removed_event_ids);
        break;
      
      case 'frame_events_cleared':
        this.clearFrameEvents(data.data.frame_id);
        break;
      
      case 'pong':
        // Keep-alive response
        break;
    }
  }

  startPingInterval() {
    this.pingInterval = setInterval(() => {
      if (this.ws.readyState === WebSocket.OPEN) {
        this.ws.send(JSON.stringify({ type: 'ping' }));
      }
    }, 30000); // Ping every 30 seconds
  }

  stopPingInterval() {
    if (this.pingInterval) {
      clearInterval(this.pingInterval);
    }
  }

  attemptReconnect() {
    if (this.reconnectAttempts < this.maxReconnectAttempts) {
      this.reconnectAttempts++;
      const delay = Math.min(1000 * Math.pow(2, this.reconnectAttempts), 30000);
      console.log(`Reconnecting in ${delay}ms...`);
      setTimeout(() => this.connect(), delay);
    }
  }

  updateMatchState(matchData) {
    console.log('Initial match state:', matchData);
    // Update your UI with initial match data
  }

  updateMatchDetails(matchData) {
    console.log('Match updated:', matchData);
    // Update match details in UI
  }

  updateFrame(frameData) {
    console.log('Frame updated:', frameData);
    // Update frame in UI
  }

  addEvent(eventData) {
    console.log('New event:', eventData);
    // Add event to UI
  }

  removeEvent(eventId) {
    console.log('Event removed:', eventId);
    // Remove event from UI
  }

  removeMultipleEvents(eventIds) {
    console.log('Multiple events removed:', eventIds);
    // Remove multiple events from UI
  }

  clearFrameEvents(frameId) {
    console.log('Frame events cleared:', frameId);
    // Clear all events for frame in UI
  }

  disconnect() {
    this.stopPingInterval();
    if (this.ws) {
      this.ws.close();
    }
  }
}

// Usage
const spectator = new MatchSpectator(123);
spectator.connect();

// Clean up when leaving the page
window.addEventListener('beforeunload', () => {
  spectator.disconnect();
});
```

### React Hook Example

```javascript
import { useEffect, useState, useRef } from 'react';

function useMatchSpectator(matchId) {
  const [matchState, setMatchState] = useState(null);
  const [connected, setConnected] = useState(false);
  const wsRef = useRef(null);

  useEffect(() => {
    const ws = new WebSocket(`ws://localhost:8000/ws/match/${matchId}/`);
    wsRef.current = ws;

    ws.onopen = () => {
      setConnected(true);
    };

    ws.onmessage = (event) => {
      const data = JSON.parse(event.data);
      
      switch(data.type) {
        case 'match_state':
          setMatchState(data.data);
          break;
        
        case 'event_created':
          setMatchState(prev => ({
            ...prev,
            match_frames: prev.match_frames.map(frame => 
              frame.id === data.data.frame_id
                ? { ...frame, events: [...frame.events, data.data] }
                : frame
            )
          }));
          break;
        
        case 'event_removed':
          setMatchState(prev => ({
            ...prev,
            match_frames: prev.match_frames.map(frame => ({
              ...frame,
              events: frame.events.filter(e => e.id !== data.data.event_id)
            }))
          }));
          break;
        
        // Handle other message types...
      }
    };

    ws.onclose = () => {
      setConnected(false);
    };

    // Cleanup
    return () => {
      ws.close();
    };
  }, [matchId]);

  return { matchState, connected };
}

// Component usage
function MatchViewer({ matchId }) {
  const { matchState, connected } = useMatchSpectator(matchId);

  if (!connected) return <div>Connecting...</div>;
  if (!matchState) return <div>Loading match...</div>;

  return (
    <div>
      <h1>{matchState.player1.display_name} vs {matchState.player2.display_name}</h1>
      {/* Render match data */}
    </div>
  );
}
```

---

## Event Types Reference

Match events that can be broadcast:

| Event Type | Description |
|------------|-------------|
| `start` | Frame started |
| `end` | Frame ended |
| `next_player` | Turn switched to next player |
| `score_update` | Score updated |
| `balls_potted` | Balls successfully potted |
| `faul` | Foul committed |
| `faul_and_next_player` | Foul committed and turn switched |
| `cue_ball_left_table` | Cue ball left the table |
| `cue_ball_gets_positioned` | Cue ball being positioned |

---

## Connection States

| State | Description |
|-------|-------------|
| CONNECTING (0) | The connection is not yet open |
| OPEN (1) | The connection is open and ready to communicate |
| CLOSING (2) | The connection is in the process of closing |
| CLOSED (3) | The connection is closed or couldn't be opened |

---

## Best Practices

1. **Reconnection Logic:** Implement exponential backoff for reconnection attempts
2. **Keep-Alive:** Send ping messages every 30-60 seconds to maintain connection
3. **UI Updates:** Update UI incrementally based on events rather than re-fetching entire state
4. **Error Handling:** Handle connection errors gracefully and inform users
5. **Memory Management:** Clean up WebSocket connections when components unmount
6. **Buffering:** Consider buffering rapid events for smoother UI updates
7. **Offline Detection:** Show connection status to users

---

## Related Documentation

- See `BIRO_EVENT_MANAGEMENT.md` for bíró (referee) WebSocket actions
- See `API_DOCUMENTATION.md` for REST API endpoints
- See `README.md` for general project information
