# Billiard Backend API Documentation

## Base URL
```
http://localhost:8000/api/
```

## Authentication

### Login
**POST** `/api/login/`

Request:
```json
{
  "username": "user",
  "password": "password"
}
```

Response:
```json
{
  "access": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "refresh": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "user": {
    "id": 1,
    "user": {
      "id": 1,
      "username": "user",
      "first_name": "First",
      "last_name": "Last",
      "email": "user@example.com"
    },
    "pfpURL": null,
    "is_biro": true
  }
}
```

### Using JWT Token
Include the access token in the Authorization header:
```
Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGc...
```

---

## Public Endpoints (No Auth Required)

### Tournaments

#### List All Tournaments
**GET** `/api/tournaments/`

Response: Array of tournament objects (lightweight)

#### Get Tournament Details
**GET** `/api/tournaments/<tournament_id>/`

Response: Full tournament object with phases, groups, and matches

### Matches

#### List All Matches
**GET** `/api/matches/`

Query Parameters:
- `tournament_id` (optional): Filter by tournament

Response: Array of match objects

#### Get Match Details
**GET** `/api/matches/<match_id>/`

Response: Full match object with frames and events

---

## Authenticated Endpoints

### Profile

#### Get My Profile
**GET** `/api/profile/`

Headers: `Authorization: Bearer <token>`

Response: Profile object

#### Get User Profile
**GET** `/api/profile/<user_id>/`

Headers: `Authorization: Bearer <token>`

Response: Profile object

---

## Bíró Administration Endpoints
All endpoints require `Authorization: Bearer <token>` and `is_biro=true`

### Tournaments

#### List/Create Tournaments
**GET** `/api/biro/tournaments/`
- Returns all tournaments with full details

**POST** `/api/biro/tournaments/`
```json
{
  "name": "Championship 2025",
  "gameMode": "8ball",
  "location": "Budapest",
  "startDate": "2025-01-15",
  "endDate": "2025-01-20"
}
```

#### Get/Update/Delete Tournament
**GET** `/api/biro/tournaments/<tournament_id>/`
- Get tournament details

**PUT** `/api/biro/tournaments/<tournament_id>/`
```json
{
  "name": "Updated Championship Name",
  "gameMode": "snooker",
  "location": "New Location",
  "startDate": "2025-02-01",
  "endDate": "2025-02-05"
}
```

**DELETE** `/api/biro/tournaments/<tournament_id>/`
- Delete tournament

### Phases

#### List/Create Phases
**GET** `/api/biro/tournaments/<tournament_id>/phases/`
- Returns all phases for tournament

**POST** `/api/biro/tournaments/<tournament_id>/phases/`
```json
{
  "order": 1,
  "eliminationSystem": "group"
}
```
*eliminationSystem options: "group", "elimination"*

#### Get/Update/Delete Phase
**GET** `/api/biro/phases/<phase_id>/`

**PUT** `/api/biro/phases/<phase_id>/`
```json
{
  "order": 2,
  "eliminationSystem": "elimination"
}
```

**DELETE** `/api/biro/phases/<phase_id>/`

### Groups

#### List/Create Groups
**GET** `/api/biro/phases/<phase_id>/groups/`
- Returns all groups for phase

**POST** `/api/biro/phases/<phase_id>/groups/`
```json
{
  "name": "Group A"
}
```

#### Get/Update/Delete Group
**GET** `/api/biro/groups/<group_id>/`

**PUT** `/api/biro/groups/<group_id>/`
```json
{
  "name": "Group B"
}
```

**DELETE** `/api/biro/groups/<group_id>/`

### Matches

#### List/Create Matches
**GET** `/api/biro/matches/`

Query Parameters:
- `phase_id` (optional): Filter by phase
- `group_id` (optional): Filter by group

**POST** `/api/biro/matches/`
```json
{
  "phase_id": 1,
  "group_id": 1,
  "player1_id": 1,
  "player2_id": 2,
  "match_date": "2025-01-15 14:00:00",
  "frames_to_win": 5
}
```

#### Get/Update/Delete Match
**GET** `/api/biro/matches/<match_id>/`

**PUT** `/api/biro/matches/<match_id>/`
```json
{
  "player1_id": 3,
  "player2_id": 4,
  "match_date": "2025-01-16 15:00:00",
  "frames_to_win": 7,
  "broadcastURL": "https://youtube.com/live/..."
}
```

**DELETE** `/api/biro/matches/<match_id>/`

### Frames

#### List/Create Frames
**GET** `/api/biro/matches/<match_id>/frames/`
- Returns all frames for match

**POST** `/api/biro/matches/<match_id>/frames/`
```json
{
  "frame_number": 1,
  "winner_id": 1
}
```
*winner_id is optional*

#### Get/Update/Delete Frame
**GET** `/api/biro/frames/<frame_id>/`

**PUT** `/api/biro/frames/<frame_id>/`
```json
{
  "frame_number": 2,
  "winner_id": 2
}
```
*Set winner_id to null to clear winner*

**DELETE** `/api/biro/frames/<frame_id>/`

### Match Events

#### Create Match Event
**POST** `/api/biro/frames/<frame_id>/events/`
```json
{
  "eventType": "balls_potted",
  "player_id": 1,
  "ball_ids": [1, 2, 3],
  "details": "Additional details",
  "turn_number": 5
}
```

Event Types:
- `start` - Frame start
- `end` - Frame end
- `next_player` - Next player's turn
- `score_update` - Score update
- `balls_potted` - Balls potted
- `faul` - Foul
- `faul_and_next_player` - Foul and next player
- `cue_ball_left_table` - Cue ball left table
- `cue_ball_gets_positioned` - Cue ball positioning

### Profiles

#### List All Profiles
**GET** `/api/biro/profiles/`
- Returns all profiles for player selection in admin interface

---

## WebSocket Endpoints

### Live Match Viewer
```
ws://localhost:8000/ws/match/<match_id>/
```

Connect to receive real-time match updates. No authentication required.

Messages received:
- `match_state` - Initial state on connection
- `match_update` - Match data updated
- `frame_update` - Frame data updated
- `event_created` - New event created

Send ping:
```json
{
  "type": "ping"
}
```

### Bíró Match Administration
```
ws://localhost:8000/ws/biro/match/<match_id>/?token=<jwt_token>
```

Requires bíró authentication via query parameter.

Actions you can send:
```json
{
  "action": "create_event",
  "event_data": {
    "eventType": "balls_potted",
    "player_id": 1,
    "ball_ids": [1, 2],
    "details": "...",
    "turn_number": 1
  }
}
```

```json
{
  "action": "start_frame",
  "frame_data": {
    "frame_number": 1
  }
}
```

```json
{
  "action": "end_frame",
  "frame_id": 1,
  "winner_id": 1
}
```

```json
{
  "action": "update_match",
  "updates": {
    "match_date": "2025-01-15 15:00:00",
    "frames_to_win": 7
  }
}
```

```json
{
  "action": "remove_event",
  "event_id": 123
}
```

```json
{
  "action": "set_ball_groups",
  "frame_id": 1,
  "player1_ball_group": "full",
  "player2_ball_group": "striped"
}
```
*Ball groups: "full" (solid balls 1-7) or "striped" (striped balls 9-15)*

Messages received:
- `event_removed` - Event has been deleted
  ```json
  {
    "type": "event_removed",
    "data": {
      "event_id": 123
    }
  }
  ```
- `ball_groups_set` - Ball groups updated
  ```json
  {
    "type": "ball_groups_set",
    "success": true,
    "data": {
      "id": 1,
      "frame_number": 1,
      "player1_ball_group": "full",
      "player2_ball_group": "striped",
      ...
    }
  }
  ```

---

## Error Responses

All endpoints return appropriate HTTP status codes:
- `200` - Success
- `201` - Created
- `204` - No Content (successful deletion)
- `400` - Bad Request
- `401` - Unauthorized
- `403` - Forbidden (not bíró)
- `404` - Not Found
- `500` - Internal Server Error

Error response format:
```json
{
  "error": "Error message description"
}
```

---

## Data Models

### Profile
```json
{
  "id": 1,
  "user": {
    "id": 1,
    "username": "user",
    "first_name": "First",
    "last_name": "Last",
    "email": "user@example.com"
  },
  "pfpURL": "https://...",
  "is_biro": true
}
```

### Tournament
```json
{
  "id": 1,
  "name": "Championship 2025",
  "startDate": "2025-01-15",
  "endDate": "2025-01-20",
  "location": "Budapest",
  "gameMode": "8ball",
  "phases": [...]
}
```

### Phase
```json
{
  "id": 1,
  "order": 1,
  "eliminationSystem": "group",
  "groups": [...],
  "matches": [...]
}
```

### Group
```json
{
  "id": 1,
  "name": "Group A",
  "matches": [...]
}
```

### Match
```json
{
  "id": 1,
  "phase": 1,
  "group": 1,
  "player1": {...},
  "player2": {...},
  "match_date": "2025-01-15T14:00:00",
  "frames_to_win": 5,
  "match_frames": [...]
}
```

### Frame
```json
{
  "id": 1,
  "frame_number": 1,
  "events": [...],
  "winner": {...},
  "player1_ball_group": "full",
  "player2_ball_group": "striped"
}
```
*Ball groups: "full" (solid), "striped", or null if not yet assigned*

### MatchEvent
```json
{
  "id": 1,
  "eventType": "balls_potted",
  "timestamp": "2025-01-15T14:30:45",
  "details": "",
  "turn_number": 5,
  "player": {...},
  "ball_ids": [1, 2, 3]
}
```
