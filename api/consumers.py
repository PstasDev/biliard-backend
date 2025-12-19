import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from .models import Match, Frame, MatchEvent, Profile
from .serializers import MatchSerializer, FrameSerializer, MatchEventSerializer
from .utils import get_profile_from_token


class LiveMatchConsumer(AsyncWebsocketConsumer):
    """
    WebSocket consumer for broadcasting live match data to spectators
    URL: ws://localhost:8000/ws/match/<match_id>/
    """
    
    async def connect(self):
        print(f"[LiveMatchConsumer] Connection attempt - scope: {self.scope.get('path')}")
        self.match_id = self.scope['url_route']['kwargs']['match_id']
        self.room_group_name = f'match_{self.match_id}'
        
        print(f"[LiveMatchConsumer] Match ID: {self.match_id}, Room: {self.room_group_name}")
        
        # Join room group
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )
        
        await self.accept()
        print(f"[LiveMatchConsumer] Connection accepted for match {self.match_id}")
        
        # Send current match state on connection
        match_data = await self.get_match_data()
        if match_data:
            print(f"[LiveMatchConsumer] Sending initial match state for match {self.match_id}")
            await self.send(text_data=json.dumps({
                'type': 'match_state',
                'data': match_data
            }))
        else:
            print(f"[LiveMatchConsumer] WARNING: No match data found for match {self.match_id}")
    
    async def disconnect(self, close_code):
        print(f"[LiveMatchConsumer] Disconnected from match {self.match_id}, code: {close_code}")
        # Leave room group
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )
    
    async def receive(self, text_data):
        """
        Handle messages from WebSocket (mostly just for ping/pong)
        """
        try:
            data = json.loads(text_data)
            
            if data.get('type') == 'ping':
                await self.send(text_data=json.dumps({
                    'type': 'pong'
                }))
        except json.JSONDecodeError:
            pass
    
    # Receive message from room group
    async def match_update(self, event):
        """
        Broadcast match updates to all connected clients
        """
        await self.send(text_data=json.dumps({
            'type': 'match_update',
            'data': event['data']
        }))
    
    async def frame_update(self, event):
        """
        Broadcast frame updates
        """
        await self.send(text_data=json.dumps({
            'type': 'frame_update',
            'data': event['data']
        }))
    
    async def event_created(self, event):
        """
        Broadcast new match events
        """
        await self.send(text_data=json.dumps({
            'type': 'event_created',
            'data': event['data']
        }))
    
    async def event_removed(self, event):
        """
        Broadcast event removal
        """
        await self.send(text_data=json.dumps({
            'type': 'event_removed',
            'data': event['data']
        }))
    
    async def events_removed(self, event):
        """
        Broadcast multiple events removal
        """
        await self.send(text_data=json.dumps({
            'type': 'events_removed',
            'data': event['data']
        }))
    
    async def frame_events_cleared(self, event):
        """
        Broadcast frame events cleared
        """
        await self.send(text_data=json.dumps({
            'type': 'frame_events_cleared',
            'data': event['data']
        }))
    
    @database_sync_to_async
    def get_match_data(self):
        try:
            match = Match.objects.get(id=self.match_id)
            serializer = MatchSerializer(match)
            return serializer.data
        except Match.DoesNotExist:
            return None


class BiroMatchAdminConsumer(AsyncWebsocketConsumer):
    """
    WebSocket consumer for biro match administration
    URL: ws://localhost:8000/ws/biro/match/<match_id>/
    Requires authentication token in connection query params
    """
    
    async def connect(self):
        print(f"[BiroMatchAdminConsumer] Connection attempt - path: {self.scope.get('path')}")
        print(f"[BiroMatchAdminConsumer] Headers: {dict(self.scope.get('headers', []))}")
        
        # Get token from query params
        query_string = self.scope.get('query_string', b'').decode()
        print(f"[BiroMatchAdminConsumer] Query string: {query_string}")
        
        token = None
        
        for param in query_string.split('&'):
            if param.startswith('token='):
                token = param.split('=')[1]
                break
        
        if not token:
            print(f"[BiroMatchAdminConsumer] ERROR: No token provided in query string")
            await self.close(code=4001)
            return
        
        print(f"[BiroMatchAdminConsumer] Token received: {token[:20]}...")
        
        # Verify biro permissions
        profile = await self.get_profile_from_token(token)
        
        if not profile:
            print(f"[BiroMatchAdminConsumer] ERROR: Invalid token or profile not found")
            await self.close(code=4003)
            return
        
        if not profile.is_biro:
            print(f"[BiroMatchAdminConsumer] ERROR: User {profile.id} is not a biro")
            await self.close(code=4003)
            return
        
        print(f"[BiroMatchAdminConsumer] Authenticated as biro: Profile ID {profile.id}")
        
        self.profile = profile
        self.match_id = self.scope['url_route']['kwargs']['match_id']
        self.room_group_name = f'biro_match_{self.match_id}'
        
        print(f"[BiroMatchAdminConsumer] Match ID: {self.match_id}, Room: {self.room_group_name}")
        
        # Join room group
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )
        
        await self.accept()
        print(f"[BiroMatchAdminConsumer] Connection accepted for match {self.match_id}")
        
        # Send current match state
        match_data = await self.get_match_data()
        if match_data:
            print(f"[BiroMatchAdminConsumer] Sending initial match state")
            await self.send(text_data=json.dumps({
                'type': 'match_state',
                'data': match_data
            }))
        else:
            print(f"[BiroMatchAdminConsumer] WARNING: No match data found for match {self.match_id}")
    
    async def disconnect(self, close_code):
        print(f"[BiroMatchAdminConsumer] Disconnected, code: {close_code}")
        # Leave room group
        if hasattr(self, 'room_group_name'):
            await self.channel_layer.group_discard(
                self.room_group_name,
                self.channel_name
            )
    
    async def receive(self, text_data):
        """
        Handle administrative actions from biro
        """
        try:
            data = json.loads(text_data)
            action = data.get('action')
            print(f"[BiroMatchAdminConsumer] Received action: {action}, data: {data}")
            
            if action == 'create_event':
                # Create new match event
                event_data = data.get('event_data', {})
                event = await self.create_match_event(event_data)
                
                if event:
                    # Broadcast to all spectators
                    await self.channel_layer.group_send(
                        f'match_{self.match_id}',
                        {
                            'type': 'event_created',
                            'data': event
                        }
                    )
                    
                    # Confirm to biro
                    await self.send(text_data=json.dumps({
                        'type': 'event_created',
                        'success': True,
                        'data': event
                    }))
            
            elif action == 'start_frame':
                # Start new frame
                frame_data = data.get('frame_data', {})
                frame = await self.create_frame(frame_data)
                
                if frame:
                    await self.channel_layer.group_send(
                        f'match_{self.match_id}',
                        {
                            'type': 'frame_update',
                            'data': frame
                        }
                    )
            
            elif action == 'end_frame':
                # End current frame
                frame_id = data.get('frame_id')
                winner_id = data.get('winner_id')
                frame = await self.end_frame(frame_id, winner_id)
                
                if frame:
                    await self.channel_layer.group_send(
                        f'match_{self.match_id}',
                        {
                            'type': 'frame_update',
                            'data': frame
                        }
                    )
            
            elif action == 'update_match':
                # Update match details
                match_updates = data.get('updates', {})
                match_data = await self.update_match(match_updates)
                
                if match_data:
                    await self.channel_layer.group_send(
                        f'match_{self.match_id}',
                        {
                            'type': 'match_update',
                            'data': match_data
                        }
                    )
            
            elif action == 'remove_event':
                # Remove/delete a match event by ID
                event_id = data.get('event_id')
                result = await self.remove_match_event(event_id)
                
                if result['success']:
                    # Broadcast event removal to all spectators
                    await self.channel_layer.group_send(
                        f'match_{self.match_id}',
                        {
                            'type': 'event_removed',
                            'data': result['data']
                        }
                    )
                    
                    # Confirm to biro
                    await self.send(text_data=json.dumps({
                        'type': 'event_removed',
                        'success': True,
                        'data': result['data']
                    }))
                else:
                    await self.send(text_data=json.dumps({
                        'type': 'error',
                        'message': result.get('message', 'Failed to remove event')
                    }))
            
            elif action == 'undo_last_event':
                # Undo the last event in a frame
                frame_id = data.get('frame_id')
                result = await self.undo_last_event(frame_id)
                
                if result['success']:
                    # Broadcast event removal to all spectators
                    await self.channel_layer.group_send(
                        f'match_{self.match_id}',
                        {
                            'type': 'event_removed',
                            'data': result['data']
                        }
                    )
                    
                    # Confirm to biro
                    await self.send(text_data=json.dumps({
                        'type': 'event_removed',
                        'success': True,
                        'data': result['data'],
                        'message': 'Last event undone'
                    }))
                else:
                    await self.send(text_data=json.dumps({
                        'type': 'error',
                        'message': result.get('message', 'Failed to undo last event')
                    }))
            
            elif action == 'remove_events_from_frame':
                # Remove multiple events from a frame
                frame_id = data.get('frame_id')
                event_ids = data.get('event_ids', [])
                result = await self.remove_events_from_frame(frame_id, event_ids)
                
                if result['success']:
                    # Broadcast to all spectators
                    await self.channel_layer.group_send(
                        f'match_{self.match_id}',
                        {
                            'type': 'events_removed',
                            'data': result['data']
                        }
                    )
                    
                    # Confirm to biro
                    await self.send(text_data=json.dumps({
                        'type': 'events_removed',
                        'success': True,
                        'data': result['data']
                    }))
                else:
                    await self.send(text_data=json.dumps({
                        'type': 'error',
                        'message': result.get('message', 'Failed to remove events')
                    }))
            
            elif action == 'clear_frame_events':
                # Clear all events from a frame
                frame_id = data.get('frame_id')
                result = await self.clear_frame_events(frame_id)
                
                if result['success']:
                    # Broadcast to all spectators
                    await self.channel_layer.group_send(
                        f'match_{self.match_id}',
                        {
                            'type': 'frame_events_cleared',
                            'data': result['data']
                        }
                    )
                    
                    # Confirm to biro
                    await self.send(text_data=json.dumps({
                        'type': 'frame_events_cleared',
                        'success': True,
                        'data': result['data']
                    }))
                else:
                    await self.send(text_data=json.dumps({
                        'type': 'error',
                        'message': result.get('message', 'Failed to clear frame events')
                    }))
            
            elif action == 'set_ball_groups':
                # Set ball groups for players in a frame
                frame_id = data.get('frame_id')
                player1_group = data.get('player1_ball_group')  # 'full' or 'striped'
                player2_group = data.get('player2_ball_group')  # 'full' or 'striped'
                
                frame_data = await self.set_frame_ball_groups(frame_id, player1_group, player2_group)
                
                if frame_data:
                    # Broadcast to all spectators
                    await self.channel_layer.group_send(
                        f'match_{self.match_id}',
                        {
                            'type': 'frame_update',
                            'data': frame_data
                        }
                    )
                    
                    # Confirm to biro
                    await self.send(text_data=json.dumps({
                        'type': 'ball_groups_set',
                        'success': True,
                        'data': frame_data
                    }))
                else:
                    await self.send(text_data=json.dumps({
                        'type': 'error',
                        'message': 'Failed to set ball groups'
                    }))
        
        except json.JSONDecodeError as e:
            print(f"[BiroMatchAdminConsumer] ERROR: Invalid JSON - {e}")
            await self.send(text_data=json.dumps({
                'type': 'error',
                'message': 'Invalid JSON'
            }))
        except Exception as e:
            print(f"[BiroMatchAdminConsumer] ERROR: {type(e).__name__}: {e}")
            import traceback
            traceback.print_exc()
            await self.send(text_data=json.dumps({
                'type': 'error',
                'message': str(e)
            }))
    
    @database_sync_to_async
    def get_profile_from_token(self, token):
        return get_profile_from_token(token)
    
    @database_sync_to_async
    def get_match_data(self):
        try:
            match = Match.objects.get(id=self.match_id)
            serializer = MatchSerializer(match)
            return serializer.data
        except Match.DoesNotExist:
            return None
    
    @database_sync_to_async
    def create_match_event(self, event_data):
        try:
            # Create match event
            event = MatchEvent.objects.create(
                eventType=event_data.get('eventType'),
                details=event_data.get('details', ''),
                turn_number=event_data.get('turn_number'),
                player_id=event_data.get('player_id'),
                ball_ids=event_data.get('ball_ids', [])
            )
            
            # Add to frame if frame_id provided
            frame_id = event_data.get('frame_id')
            if frame_id:
                frame = Frame.objects.get(id=frame_id)
                frame.events.add(event)
            
            serializer = MatchEventSerializer(event)
            return serializer.data
        except Exception as e:
            return None
    
    @database_sync_to_async
    def create_frame(self, frame_data):
        try:
            match = Match.objects.get(id=self.match_id)
            
            # Check if match is already decided (Best of N logic)
            player1_wins = match.match_frames.filter(winner=match.player1).count()
            player2_wins = match.match_frames.filter(winner=match.player2).count()
            total_frames = match.frames_to_win
            
            # Best of N: Need (N+1)/2 to win if N is odd
            frames_needed_to_win = (total_frames + 1) // 2
            
            # Don't create a new frame if either player has already won
            if player1_wins >= frames_needed_to_win or player2_wins >= frames_needed_to_win:
                return None
            
            # Don't create new frame if match ended in draw (even total frames and tied)
            if total_frames % 2 == 0 and player1_wins + player2_wins >= total_frames:
                return None
            
            frame = Frame.objects.create(
                match=match,
                frame_number=frame_data.get('frame_number', match.match_frames.count() + 1)
            )
            
            serializer = FrameSerializer(frame)
            return serializer.data
        except Exception as e:
            return None
    
    @database_sync_to_async
    def end_frame(self, frame_id, winner_id):
        try:
            frame = Frame.objects.get(id=frame_id)
            if winner_id:
                frame.winner_id = winner_id
                frame.save()
            
            serializer = FrameSerializer(frame)
            return serializer.data
        except Exception as e:
            return None
    
    @database_sync_to_async
    def update_match(self, updates):
        try:
            match = Match.objects.get(id=self.match_id)
            
            # Update allowed fields
            if 'match_date' in updates:
                match.match_date = updates['match_date']
            if 'frames_to_win' in updates:
                match.frames_to_win = updates['frames_to_win']
            
            match.save()
            
            serializer = MatchSerializer(match)
            return serializer.data
        except Exception as e:
            return None
    
    @database_sync_to_async
    def remove_match_event(self, event_id):
        try:
            # Get the event and verify it belongs to a frame in this match
            event = MatchEvent.objects.get(id=event_id)
            
            # Verify the event is part of this match
            frames = Frame.objects.filter(match_id=self.match_id, events=event)
            if not frames.exists():
                return {'success': False, 'message': 'Event not found in this match'}
            
            # Get event data before deletion for broadcasting
            event_data = {
                'event_id': event_id,
                'frame_ids': [frame.id for frame in frames]
            }
            
            # Remove the event from all frames
            for frame in frames:
                frame.events.remove(event)
            
            # Delete the event
            event.delete()
            
            return {'success': True, 'data': event_data}
        except MatchEvent.DoesNotExist:
            return {'success': False, 'message': 'Event not found'}
        except Exception as e:
            return {'success': False, 'message': str(e)}
    
    @database_sync_to_async
    def undo_last_event(self, frame_id):
        try:
            frame = Frame.objects.get(id=frame_id, match_id=self.match_id)
            
            # Get the last event in chronological order
            last_event = frame.events.order_by('-timestamp').first()
            
            if not last_event:
                return {'success': False, 'message': 'No events to undo in this frame'}
            
            event_data = {
                'event_id': last_event.id,
                'frame_id': frame_id,
                'event_type': last_event.eventType
            }
            
            # Remove the event from the frame
            frame.events.remove(last_event)
            
            # Delete the event
            last_event.delete()
            
            return {'success': True, 'data': event_data}
        except Frame.DoesNotExist:
            return {'success': False, 'message': 'Frame not found'}
        except Exception as e:
            return {'success': False, 'message': str(e)}
    
    @database_sync_to_async
    def remove_events_from_frame(self, frame_id, event_ids):
        try:
            frame = Frame.objects.get(id=frame_id, match_id=self.match_id)
            
            removed_events = []
            
            for event_id in event_ids:
                try:
                    event = MatchEvent.objects.get(id=event_id)
                    
                    # Verify event is in this frame
                    if frame.events.filter(id=event_id).exists():
                        frame.events.remove(event)
                        event.delete()
                        removed_events.append(event_id)
                except MatchEvent.DoesNotExist:
                    continue
            
            return {
                'success': True,
                'data': {
                    'frame_id': frame_id,
                    'removed_event_ids': removed_events,
                    'count': len(removed_events)
                }
            }
        except Frame.DoesNotExist:
            return {'success': False, 'message': 'Frame not found'}
        except Exception as e:
            return {'success': False, 'message': str(e)}
    
    @database_sync_to_async
    def clear_frame_events(self, frame_id):
        try:
            frame = Frame.objects.get(id=frame_id, match_id=self.match_id)
            
            # Get all event IDs before clearing
            event_ids = list(frame.events.values_list('id', flat=True))
            
            # Remove all events from the frame and delete them
            for event in frame.events.all():
                frame.events.remove(event)
                event.delete()
            
            return {
                'success': True,
                'data': {
                    'frame_id': frame_id,
                    'cleared_event_ids': event_ids,
                    'count': len(event_ids)
                }
            }
        except Frame.DoesNotExist:
            return {'success': False, 'message': 'Frame not found'}
        except Exception as e:
            return {'success': False, 'message': str(e)}
    
    @database_sync_to_async
    def set_frame_ball_groups(self, frame_id, player1_group, player2_group):
        try:
            frame = Frame.objects.get(id=frame_id, match_id=self.match_id)
            
            # Validate ball groups
            valid_groups = [Frame.BALL_GROUP_FULL, Frame.BALL_GROUP_STRIPED]
            
            if player1_group and player1_group in valid_groups:
                frame.player1_ball_group = player1_group
            
            if player2_group and player2_group in valid_groups:
                frame.player2_ball_group = player2_group
            
            frame.save()
            
            serializer = FrameSerializer(frame)
            return serializer.data
        except Frame.DoesNotExist:
            return None
        except Exception as e:
            return None
