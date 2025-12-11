# Bíró Event Management - WebSocket API

## Overview

This document describes the WebSocket actions available to bíró (referee) users for managing match events in real-time. These features allow undoing, deleting, and clearing events from frames during live match administration.

## Connection

**WebSocket URL:** `ws://localhost:8000/ws/biro/match/<match_id>/`

**Authentication:** Include JWT token as query parameter:
```
ws://localhost:8000/ws/biro/match/123/?token=<your_jwt_token>
```

**Permissions Required:** User must have `is_biro=True` in their profile.

---

## Event Management Actions

### 1. Remove Event by ID

Delete a specific event from the match by its event ID.

**Action:**
```json
{
  "action": "remove_event",
  "event_id": 456
}
```

**Parameters:**
- `event_id` (integer, required): The ID of the event to remove

**Success Response:**
```json
{
  "type": "event_removed",
  "success": true,
  "data": {
    "event_id": 456,
    "frame_ids": [12]
  }
}
```

**Error Response:**
```json
{
  "type": "error",
  "message": "Event not found in this match"
}
```

**Broadcast to Spectators:**
All connected spectators will receive:
```json
{
  "type": "event_removed",
  "data": {
    "event_id": 456,
    "frame_ids": [12]
  }
}
```

---

### 2. Undo Last Event

Remove the most recent event from a specific frame (chronologically by timestamp).

**Action:**
```json
{
  "action": "undo_last_event",
  "frame_id": 12
}
```

**Parameters:**
- `frame_id` (integer, required): The ID of the frame to undo the last event from

**Success Response:**
```json
{
  "type": "event_removed",
  "success": true,
  "data": {
    "event_id": 789,
    "frame_id": 12,
    "event_type": "balls_potted"
  },
  "message": "Last event undone"
}
```

**Error Response:**
```json
{
  "type": "error",
  "message": "No events to undo in this frame"
}
```

**Use Case:** Quick undo of the most recent action (e.g., accidentally logged wrong balls potted).

---

### 3. Remove Multiple Events from Frame

Delete multiple specific events from a frame by their IDs.

**Action:**
```json
{
  "action": "remove_events_from_frame",
  "frame_id": 12,
  "event_ids": [456, 457, 458]
}
```

**Parameters:**
- `frame_id` (integer, required): The ID of the frame
- `event_ids` (array of integers, required): Array of event IDs to remove

**Success Response:**
```json
{
  "type": "events_removed",
  "success": true,
  "data": {
    "frame_id": 12,
    "removed_event_ids": [456, 457, 458],
    "count": 3
  }
}
```

**Broadcast to Spectators:**
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

**Use Case:** Remove multiple incorrect events in one operation.

---

### 4. Clear All Frame Events

Remove all events from a frame (complete reset).

**Action:**
```json
{
  "action": "clear_frame_events",
  "frame_id": 12
}
```

**Parameters:**
- `frame_id` (integer, required): The ID of the frame to clear

**Success Response:**
```json
{
  "type": "frame_events_cleared",
  "success": true,
  "data": {
    "frame_id": 12,
    "cleared_event_ids": [450, 451, 452, 453, 454],
    "count": 5
  }
}
```

**Broadcast to Spectators:**
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

**Use Case:** Completely restart a frame's event log (e.g., major scoring error).

---

## Implementation Examples

### JavaScript/TypeScript Example

```javascript
// Connect to biro WebSocket
const token = localStorage.getItem('jwt_token');
const matchId = 123;
const ws = new WebSocket(`ws://localhost:8000/ws/biro/match/${matchId}/?token=${token}`);

ws.onopen = () => {
  console.log('Connected to biro match admin');
};

ws.onmessage = (event) => {
  const data = JSON.parse(event.data);
  
  switch(data.type) {
    case 'event_removed':
      console.log('Event removed:', data.data);
      // Update UI to remove event
      break;
    
    case 'events_removed':
      console.log('Multiple events removed:', data.data);
      // Update UI to remove multiple events
      break;
    
    case 'frame_events_cleared':
      console.log('Frame cleared:', data.data);
      // Update UI to clear all frame events
      break;
    
    case 'error':
      console.error('Error:', data.message);
      // Show error to user
      break;
  }
};

// Undo last event
function undoLastEvent(frameId) {
  ws.send(JSON.stringify({
    action: 'undo_last_event',
    frame_id: frameId
  }));
}

// Remove specific event
function removeEvent(eventId) {
  ws.send(JSON.stringify({
    action: 'remove_event',
    event_id: eventId
  }));
}

// Remove multiple events
function removeMultipleEvents(frameId, eventIds) {
  ws.send(JSON.stringify({
    action: 'remove_events_from_frame',
    frame_id: frameId,
    event_ids: eventIds
  }));
}

// Clear all events from frame
function clearFrameEvents(frameId) {
  if (confirm('Are you sure you want to clear all events from this frame?')) {
    ws.send(JSON.stringify({
      action: 'clear_frame_events',
      frame_id: frameId
    }));
  }
}
```

### Python Example

```python
import asyncio
import websockets
import json

async def manage_events(match_id, token):
    uri = f"ws://localhost:8000/ws/biro/match/{match_id}/?token={token}"
    
    async with websockets.connect(uri) as websocket:
        # Undo last event
        await websocket.send(json.dumps({
            "action": "undo_last_event",
            "frame_id": 12
        }))
        
        response = await websocket.recv()
        print(f"Response: {response}")

# Run
asyncio.run(manage_events(123, "your_jwt_token"))
```

---

## Important Notes

1. **Permissions:** All event management actions require `is_biro=True` permission. Unauthorized users will be disconnected with code 4003.

2. **Validation:** 
   - Events can only be removed from frames that belong to the current match
   - Non-existent event IDs are silently skipped in batch operations
   - Frame must exist in the current match

3. **Broadcasting:** 
   - All event removals are broadcast to spectators in real-time
   - Both bíró and spectator WebSocket connections receive updates
   - Spectators receive read-only notifications

4. **Cascading Deletion:**
   - Deleting an event removes it from all associated frames
   - The event is permanently deleted from the database
   - This action cannot be undone (no event history/versioning)

5. **Performance:**
   - Batch operations (`remove_events_from_frame`, `clear_frame_events`) are more efficient than individual removals
   - Use `undo_last_event` for simple undo workflows
   - Use `clear_frame_events` for complete resets

---

## Error Codes

| Code | Meaning |
|------|---------|
| 4001 | No authentication token provided |
| 4003 | Insufficient permissions (not a bíró) |
| 1000 | Normal closure |

---

## Best Practices

1. **Undo Workflow:** Implement an "Undo" button in your UI that calls `undo_last_event` for quick corrections.

2. **Event Selection:** Allow bíró to select multiple events in the UI and delete them in one batch using `remove_events_from_frame`.

3. **Confirmation Dialogs:** Always show confirmation dialogs before calling `clear_frame_events` to prevent accidental data loss.

4. **Real-time Sync:** Listen to broadcast events to keep all connected clients in sync, including the bíró's own UI.

5. **Error Handling:** Display user-friendly error messages when operations fail.

6. **Visual Feedback:** Show loading states during event removal and success/error notifications after completion.

---

## Related Documentation

- See `API_DOCUMENTATION.md` for REST API event management
- See `WEBSOCKET_SPECTATOR_API.md` for spectator WebSocket API
- See `README.md` for general project information
