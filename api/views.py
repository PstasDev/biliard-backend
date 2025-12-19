from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.contrib.auth import authenticate
from django.contrib.auth.models import User
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from rest_framework import status
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
import json

from .models import Profile, Tournament, Match, Frame, MatchEvent, Phase, Group
from .serializers import (
    ProfileSerializer, TournamentSerializer, TournamentListSerializer,
    MatchSerializer, MatchListSerializer, FrameSerializer, MatchEventSerializer,
    PhaseSerializer, GroupSerializer
)
from .utils import jwt_required, biro_required


def index(request):
    return render(request, 'index.html')

@csrf_exempt
@require_http_methods(["POST"])
def login(request):
    """
    Login endpoint that returns JWT tokens
    POST: { "username": "...", "password": "..." }
    Returns: { "access": "...", "refresh": "...", "user": {...} }
    """
    try:
        data = json.loads(request.body)
        username = data.get('username')
        password = data.get('password')
        
        if not username or not password:
            return JsonResponse({'error': 'Username and password required'}, status=400)
        
        user = authenticate(username=username, password=password)
        
        if user is None:
            return JsonResponse({'error': 'Invalid credentials'}, status=401)
        
        # Generate JWT tokens
        refresh = RefreshToken.for_user(user)
        access_token = str(refresh.access_token)
        
        # Get user profile
        try:
            profile = Profile.objects.get(user=user)
            profile_data = ProfileSerializer(profile).data
        except Profile.DoesNotExist:
            # Create profile if it doesn't exist
            profile = Profile.objects.create(user=user)
            profile_data = ProfileSerializer(profile).data
        
        return JsonResponse({
            'access': access_token,
            'refresh': str(refresh),
            'user': profile_data
        }, status=200)
        
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON'}, status=400)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@api_view(['GET'])
@permission_classes([AllowAny])
def tournament_list(request):
    """
    Get list of all tournaments (lightweight)
    """
    tournaments = Tournament.objects.all()
    serializer = TournamentListSerializer(tournaments, many=True)
    return Response(serializer.data)


@api_view(['GET'])
@permission_classes([AllowAny])
def tournament_detail(request, tournament_id):
    """
    Get detailed tournament data including phases, groups, and matches
    """
    try:
        tournament = Tournament.objects.get(id=tournament_id)
        serializer = TournamentSerializer(tournament)
        return Response(serializer.data)
    except Tournament.DoesNotExist:
        return Response({'error': 'Tournament not found'}, status=status.HTTP_404_NOT_FOUND)


@api_view(['GET'])
@permission_classes([AllowAny])
def match_list(request):
    """
    Get list of all matches (can filter by tournament_id query param)
    """
    tournament_id = request.GET.get('tournament_id')
    
    if tournament_id:
        matches = Match.objects.filter(phase__tournament_id=tournament_id)
    else:
        matches = Match.objects.all()
    
    serializer = MatchListSerializer(matches, many=True)
    return Response(serializer.data)


@api_view(['GET'])
@permission_classes([AllowAny])
def match_detail(request, match_id):
    """
    Get detailed match data including frames and events
    """
    try:
        match = Match.objects.get(id=match_id)
        serializer = MatchSerializer(match)
        return Response(serializer.data)
    except Match.DoesNotExist:
        return Response({'error': 'Match not found'}, status=status.HTTP_404_NOT_FOUND)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def profile_detail(request, user_id=None):
    """
    Get profile data (own profile if no user_id, or specific user's profile)
    Requires JWT authentication
    """
    if user_id is None:
        user = request.user
    else:
        try:
            user = User.objects.get(id=user_id)
        except User.DoesNotExist:
            return Response({'error': 'User not found'}, status=status.HTTP_404_NOT_FOUND)
    
    try:
        profile = Profile.objects.get(user=user)
        serializer = ProfileSerializer(profile)
        return Response(serializer.data)
    except Profile.DoesNotExist:
        return Response({'error': 'Profile not found'}, status=status.HTTP_404_NOT_FOUND)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def my_profile(request):
    """
    Get authenticated user's profile
    """
    return profile_detail(request, user_id=None)


@csrf_exempt
@jwt_required
@biro_required
@require_http_methods(["POST", "PUT", "DELETE"])
def biro_manage_match(request, match_id):
    """
    Biro-only endpoint for managing matches
    Requires JWT token with is_biro=True
    """
    try:
        match = Match.objects.get(id=match_id)
        
        if request.method == "POST":
            # Create new frame or event
            data = json.loads(request.body)
            # Implementation depends on specific requirements
            return JsonResponse({'success': True, 'message': 'Created'})
        
        elif request.method == "PUT":
            # Update match data
            data = json.loads(request.body)
            # Implementation depends on specific requirements
            return JsonResponse({'success': True, 'message': 'Updated'})
        
        elif request.method == "DELETE":
            # Delete match (if allowed)
            match.delete()
            return JsonResponse({'success': True, 'message': 'Deleted'})
            
    except Match.DoesNotExist:
        return JsonResponse({'error': 'Match not found'}, status=404)
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON'}, status=400)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


# ==================== BÍRÓ ADMINISTRATION ENDPOINTS ====================

@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
def biro_tournaments(request):
    """
    Biro-only: List all tournaments or create new tournament
    GET: List all tournaments
    POST: Create new tournament { "name": "...", "gameMode": "8ball", "location": "...", "startDate": "YYYY-MM-DD", "endDate": "YYYY-MM-DD" }
    """
    try:
        profile = Profile.objects.get(user=request.user)
        if not profile.is_biro:
            return Response({'error': 'Biro permission required'}, status=status.HTTP_403_FORBIDDEN)
    except Profile.DoesNotExist:
        return Response({'error': 'Profile not found'}, status=status.HTTP_404_NOT_FOUND)
    
    if request.method == 'GET':
        tournaments = Tournament.objects.all().order_by('-startDate')
        serializer = TournamentSerializer(tournaments, many=True)
        return Response(serializer.data)
    
    elif request.method == 'POST':
        data = request.data
        tournament = Tournament.objects.create(
            name=data.get('name'),
            gameMode=data.get('gameMode', Tournament.GAMEMODE_8BALL),
            location=data.get('location', ''),
            startDate=data.get('startDate'),
            endDate=data.get('endDate')
        )
        serializer = TournamentSerializer(tournament)
        return Response(serializer.data, status=status.HTTP_201_CREATED)


@api_view(['GET', 'PUT', 'DELETE'])
@permission_classes([IsAuthenticated])
def biro_tournament_detail(request, tournament_id):
    """
    Biro-only: Get, update, or delete tournament
    GET: Get tournament details
    PUT: Update tournament { "name": "...", "gameMode": "...", "location": "...", "startDate": "...", "endDate": "..." }
    DELETE: Delete tournament
    """
    try:
        profile = Profile.objects.get(user=request.user)
        if not profile.is_biro:
            return Response({'error': 'Biro permission required'}, status=status.HTTP_403_FORBIDDEN)
    except Profile.DoesNotExist:
        return Response({'error': 'Profile not found'}, status=status.HTTP_404_NOT_FOUND)
    
    try:
        tournament = Tournament.objects.get(id=tournament_id)
    except Tournament.DoesNotExist:
        return Response({'error': 'Tournament not found'}, status=status.HTTP_404_NOT_FOUND)
    
    if request.method == 'GET':
        serializer = TournamentSerializer(tournament)
        return Response(serializer.data)
    
    elif request.method == 'PUT':
        data = request.data
        if 'name' in data:
            tournament.name = data['name']
        if 'gameMode' in data:
            tournament.gameMode = data['gameMode']
        if 'location' in data:
            tournament.location = data['location']
        if 'startDate' in data:
            tournament.startDate = data['startDate']
        if 'endDate' in data:
            tournament.endDate = data['endDate']
        tournament.save()
        
        serializer = TournamentSerializer(tournament)
        return Response(serializer.data)
    
    elif request.method == 'DELETE':
        tournament.delete()
        return Response({'success': True, 'message': 'Tournament deleted'}, status=status.HTTP_204_NO_CONTENT)


@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
def biro_phases(request, tournament_id):
    """
    Biro-only: List phases or create new phase for tournament
    GET: List all phases for tournament
    POST: Create new phase { "order": 1, "eliminationSystem": "group" or "elimination" }
    """
    try:
        profile = Profile.objects.get(user=request.user)
        if not profile.is_biro:
            return Response({'error': 'Biro permission required'}, status=status.HTTP_403_FORBIDDEN)
    except Profile.DoesNotExist:
        return Response({'error': 'Profile not found'}, status=status.HTTP_404_NOT_FOUND)
    
    try:
        tournament = Tournament.objects.get(id=tournament_id)
    except Tournament.DoesNotExist:
        return Response({'error': 'Tournament not found'}, status=status.HTTP_404_NOT_FOUND)
    
    if request.method == 'GET':
        phases = Phase.objects.filter(tournament=tournament).order_by('order')
        serializer = PhaseSerializer(phases, many=True)
        return Response(serializer.data)
    
    elif request.method == 'POST':
        data = request.data
        phase = Phase.objects.create(
            tournament=tournament,
            order=data.get('order', 1),
            eliminationSystem=data.get('eliminationSystem', Phase.ELIMINATION)
        )
        serializer = PhaseSerializer(phase)
        return Response(serializer.data, status=status.HTTP_201_CREATED)


@api_view(['GET', 'PUT', 'DELETE'])
@permission_classes([IsAuthenticated])
def biro_phase_detail(request, phase_id):
    """
    Biro-only: Get, update, or delete phase
    GET: Get phase details
    PUT: Update phase { "order": 1, "eliminationSystem": "group" }
    DELETE: Delete phase
    """
    try:
        profile = Profile.objects.get(user=request.user)
        if not profile.is_biro:
            return Response({'error': 'Biro permission required'}, status=status.HTTP_403_FORBIDDEN)
    except Profile.DoesNotExist:
        return Response({'error': 'Profile not found'}, status=status.HTTP_404_NOT_FOUND)
    
    try:
        phase = Phase.objects.get(id=phase_id)
    except Phase.DoesNotExist:
        return Response({'error': 'Phase not found'}, status=status.HTTP_404_NOT_FOUND)
    
    if request.method == 'GET':
        serializer = PhaseSerializer(phase)
        return Response(serializer.data)
    
    elif request.method == 'PUT':
        data = request.data
        if 'order' in data:
            phase.order = data['order']
        if 'eliminationSystem' in data:
            phase.eliminationSystem = data['eliminationSystem']
        phase.save()
        
        serializer = PhaseSerializer(phase)
        return Response(serializer.data)
    
    elif request.method == 'DELETE':
        phase.delete()
        return Response({'success': True, 'message': 'Phase deleted'}, status=status.HTTP_204_NO_CONTENT)


@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
def biro_groups(request, phase_id):
    """
    Biro-only: List groups or create new group for phase
    GET: List all groups for phase
    POST: Create new group { "name": "Group A" }
    """
    try:
        profile = Profile.objects.get(user=request.user)
        if not profile.is_biro:
            return Response({'error': 'Biro permission required'}, status=status.HTTP_403_FORBIDDEN)
    except Profile.DoesNotExist:
        return Response({'error': 'Profile not found'}, status=status.HTTP_404_NOT_FOUND)
    
    try:
        phase = Phase.objects.get(id=phase_id)
    except Phase.DoesNotExist:
        return Response({'error': 'Phase not found'}, status=status.HTTP_404_NOT_FOUND)
    
    if request.method == 'GET':
        groups = Group.objects.filter(phase=phase)
        serializer = GroupSerializer(groups, many=True)
        return Response(serializer.data)
    
    elif request.method == 'POST':
        data = request.data
        group = Group.objects.create(
            phase=phase,
            name=data.get('name', 'Group')
        )
        serializer = GroupSerializer(group)
        return Response(serializer.data, status=status.HTTP_201_CREATED)


@api_view(['GET', 'PUT', 'DELETE'])
@permission_classes([IsAuthenticated])
def biro_group_detail(request, group_id):
    """
    Biro-only: Get, update, or delete group
    GET: Get group details
    PUT: Update group { "name": "Group B" }
    DELETE: Delete group
    """
    try:
        profile = Profile.objects.get(user=request.user)
        if not profile.is_biro:
            return Response({'error': 'Biro permission required'}, status=status.HTTP_403_FORBIDDEN)
    except Profile.DoesNotExist:
        return Response({'error': 'Profile not found'}, status=status.HTTP_404_NOT_FOUND)
    
    try:
        group = Group.objects.get(id=group_id)
    except Group.DoesNotExist:
        return Response({'error': 'Group not found'}, status=status.HTTP_404_NOT_FOUND)
    
    if request.method == 'GET':
        serializer = GroupSerializer(group)
        return Response(serializer.data)
    
    elif request.method == 'PUT':
        data = request.data
        if 'name' in data:
            group.name = data['name']
        group.save()
        
        serializer = GroupSerializer(group)
        return Response(serializer.data)
    
    elif request.method == 'DELETE':
        group.delete()
        return Response({'success': True, 'message': 'Group deleted'}, status=status.HTTP_204_NO_CONTENT)


@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
def biro_matches(request):
    """
    Biro-only: List all matches or create new match
    GET: List all matches (can filter by phase_id, group_id query params)
    POST: Create new match { "phase_id": 1, "group_id": 1, "player1_id": 1, "player2_id": 2, "match_date": "YYYY-MM-DD HH:MM:SS", "frames_to_win": 5 }
    """
    try:
        profile = Profile.objects.get(user=request.user)
        if not profile.is_biro:
            return Response({'error': 'Biro permission required'}, status=status.HTTP_403_FORBIDDEN)
    except Profile.DoesNotExist:
        return Response({'error': 'Profile not found'}, status=status.HTTP_404_NOT_FOUND)
    
    if request.method == 'GET':
        matches = Match.objects.all()
        
        phase_id = request.GET.get('phase_id')
        group_id = request.GET.get('group_id')
        
        if phase_id:
            matches = matches.filter(phase_id=phase_id)
        if group_id:
            matches = matches.filter(group_id=group_id)
        
        matches = matches.order_by('-match_date')
        serializer = MatchSerializer(matches, many=True)
        return Response(serializer.data)
    
    elif request.method == 'POST':
        data = request.data
        
        try:
            phase = Phase.objects.get(id=data.get('phase_id'))
            player1 = Profile.objects.get(id=data.get('player1_id'))
            player2 = Profile.objects.get(id=data.get('player2_id'))
            
            group = None
            if data.get('group_id'):
                group = Group.objects.get(id=data.get('group_id'))
            
            match = Match.objects.create(
                phase=phase,
                group=group,
                player1=player1,
                player2=player2,
                match_date=data.get('match_date'),
                frames_to_win=data.get('frames_to_win', 5),
                broadcastURL=data.get('broadcastURL', '')
            )
            
            serializer = MatchSerializer(match)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        
        except (Phase.DoesNotExist, Profile.DoesNotExist, Group.DoesNotExist) as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET', 'PUT', 'DELETE'])
@permission_classes([IsAuthenticated])
def biro_match_detail(request, match_id):
    """
    Biro-only: Get, update, or delete match
    GET: Get match details
    PUT: Update match { "player1_id": 1, "player2_id": 2, "match_date": "...", "frames_to_win": 5 }
    DELETE: Delete match
    """
    try:
        profile = Profile.objects.get(user=request.user)
        if not profile.is_biro:
            return Response({'error': 'Biro permission required'}, status=status.HTTP_403_FORBIDDEN)
    except Profile.DoesNotExist:
        return Response({'error': 'Profile not found'}, status=status.HTTP_404_NOT_FOUND)
    
    try:
        match = Match.objects.get(id=match_id)
    except Match.DoesNotExist:
        return Response({'error': 'Match not found'}, status=status.HTTP_404_NOT_FOUND)
    
    if request.method == 'GET':
        serializer = MatchSerializer(match)
        return Response(serializer.data)
    
    elif request.method == 'PUT':
        data = request.data
        
        if 'phase_id' in data:
            try:
                match.phase = Phase.objects.get(id=data['phase_id'])
            except Phase.DoesNotExist:
                return Response({'error': 'Phase not found'}, status=status.HTTP_400_BAD_REQUEST)
        
        if 'player1_id' in data:
            try:
                match.player1 = Profile.objects.get(id=data['player1_id'])
            except Profile.DoesNotExist:
                return Response({'error': 'Player1 not found'}, status=status.HTTP_400_BAD_REQUEST)
        
        if 'player2_id' in data:
            try:
                match.player2 = Profile.objects.get(id=data['player2_id'])
            except Profile.DoesNotExist:
                return Response({'error': 'Player2 not found'}, status=status.HTTP_400_BAD_REQUEST)
        
        if 'match_date' in data:
            match.match_date = data['match_date']
        if 'frames_to_win' in data:
            match.frames_to_win = data['frames_to_win']
        if 'broadcastURL' in data:
            match.broadcastURL = data['broadcastURL']
        
        match.save()
        
        serializer = MatchSerializer(match)
        
        # Broadcast match update to WebSocket clients
        channel_layer = get_channel_layer()
        async_to_sync(channel_layer.group_send)(
            f'match_{match_id}',
            {
                'type': 'match_update',
                'data': serializer.data
            }
        )
        
        return Response(serializer.data)
    
    elif request.method == 'DELETE':
        match.delete()
        return Response({'success': True, 'message': 'Match deleted'}, status=status.HTTP_204_NO_CONTENT)


@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
def biro_frames(request, match_id):
    """
    Biro-only: List frames or create new frame for match
    GET: List all frames for match
    POST: Create new frame { "frame_number": 1, "winner_id": 1 (optional) }
    """
    try:
        profile = Profile.objects.get(user=request.user)
        if not profile.is_biro:
            return Response({'error': 'Biro permission required'}, status=status.HTTP_403_FORBIDDEN)
    except Profile.DoesNotExist:
        return Response({'error': 'Profile not found'}, status=status.HTTP_404_NOT_FOUND)
    
    try:
        match = Match.objects.get(id=match_id)
    except Match.DoesNotExist:
        return Response({'error': 'Match not found'}, status=status.HTTP_404_NOT_FOUND)
    
    if request.method == 'GET':
        frames = Frame.objects.filter(match=match).order_by('frame_number')
        serializer = FrameSerializer(frames, many=True)
        return Response(serializer.data)
    
    elif request.method == 'POST':
        data = request.data
        
        # Check if match is already decided (Best of N logic)
        player1_wins = match.match_frames.filter(winner=match.player1).count()
        player2_wins = match.match_frames.filter(winner=match.player2).count()
        total_frames = match.frames_to_win
        
        # Best of N: Need (N+1)/2 to win if N is odd, or match ends in draw if N/2 - N/2 and N is even
        frames_needed_to_win = (total_frames + 1) // 2
        
        # Check if someone already won
        if player1_wins >= frames_needed_to_win or player2_wins >= frames_needed_to_win:
            return Response({
                'error': 'Match is already decided - winner declared',
                'player1_wins': player1_wins,
                'player2_wins': player2_wins,
                'frames_to_win': match.frames_to_win
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Check if match ended in draw (even total frames and tied)
        if total_frames % 2 == 0 and player1_wins + player2_wins >= total_frames:
            return Response({
                'error': 'Match ended in draw',
                'player1_wins': player1_wins,
                'player2_wins': player2_wins,
                'frames_to_win': match.frames_to_win
            }, status=status.HTTP_400_BAD_REQUEST)
        
        winner = None
        if data.get('winner_id'):
            try:
                winner = Profile.objects.get(id=data.get('winner_id'))
            except Profile.DoesNotExist:
                return Response({'error': 'Winner not found'}, status=status.HTTP_400_BAD_REQUEST)
        
        frame = Frame.objects.create(
            match=match,
            frame_number=data.get('frame_number', match.match_frames.count() + 1),
            winner=winner
        )
        
        serializer = FrameSerializer(frame)
        
        # Broadcast frame creation to WebSocket clients
        channel_layer = get_channel_layer()
        async_to_sync(channel_layer.group_send)(
            f'match_{match_id}',
            {
                'type': 'frame_update',
                'data': serializer.data
            }
        )
        
        return Response(serializer.data, status=status.HTTP_201_CREATED)


@api_view(['GET', 'PUT', 'DELETE'])
@permission_classes([IsAuthenticated])
def biro_frame_detail(request, frame_id):
    """
    Biro-only: Get, update, or delete frame
    GET: Get frame details
    PUT: Update frame { "frame_number": 2, "winner_id": 1 }
    DELETE: Delete frame
    """
    try:
        profile = Profile.objects.get(user=request.user)
        if not profile.is_biro:
            return Response({'error': 'Biro permission required'}, status=status.HTTP_403_FORBIDDEN)
    except Profile.DoesNotExist:
        return Response({'error': 'Profile not found'}, status=status.HTTP_404_NOT_FOUND)
    
    try:
        frame = Frame.objects.get(id=frame_id)
    except Frame.DoesNotExist:
        return Response({'error': 'Frame not found'}, status=status.HTTP_404_NOT_FOUND)
    
    if request.method == 'GET':
        serializer = FrameSerializer(frame)
        return Response(serializer.data)
    
    elif request.method == 'PUT':
        data = request.data
        
        if 'frame_number' in data:
            frame.frame_number = data['frame_number']
        
        if 'winner_id' in data:
            if data['winner_id'] is None:
                frame.winner = None
            else:
                try:
                    frame.winner = Profile.objects.get(id=data['winner_id'])
                except Profile.DoesNotExist:
                    return Response({'error': 'Winner not found'}, status=status.HTTP_400_BAD_REQUEST)
        
        if 'player1_ball_group' in data:
            frame.player1_ball_group = data['player1_ball_group']
        
        if 'player2_ball_group' in data:
            frame.player2_ball_group = data['player2_ball_group']
        
        frame.save()
        
        serializer = FrameSerializer(frame)
        
        # Broadcast frame update to WebSocket clients
        channel_layer = get_channel_layer()
        match_id = frame.match_id
        async_to_sync(channel_layer.group_send)(
            f'match_{match_id}',
            {
                'type': 'frame_update',
                'data': serializer.data
            }
        )
        
        return Response(serializer.data)
    
    elif request.method == 'DELETE':
        frame.delete()
        return Response({'success': True, 'message': 'Frame deleted'}, status=status.HTTP_204_NO_CONTENT)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def biro_create_event(request, frame_id):
    """
    Biro-only: Create new match event for frame
    POST: Create event { "eventType": "balls_potted", "player_id": 1, "ball_ids": [1, 2], "details": "...", "turn_number": 1 }
    """
    try:
        profile = Profile.objects.get(user=request.user)
        if not profile.is_biro:
            return Response({'error': 'Biro permission required'}, status=status.HTTP_403_FORBIDDEN)
    except Profile.DoesNotExist:
        return Response({'error': 'Profile not found'}, status=status.HTTP_404_NOT_FOUND)
    
    try:
        frame = Frame.objects.get(id=frame_id)
    except Frame.DoesNotExist:
        return Response({'error': 'Frame not found'}, status=status.HTTP_404_NOT_FOUND)
    
    data = request.data
    
    player = None
    if data.get('player_id'):
        try:
            player = Profile.objects.get(id=data.get('player_id'))
        except Profile.DoesNotExist:
            return Response({'error': 'Player not found'}, status=status.HTTP_400_BAD_REQUEST)
    
    event = MatchEvent.objects.create(
        eventType=data.get('eventType'),
        player=player,
        ball_ids=data.get('ball_ids', []),
        details=data.get('details', ''),
        turn_number=data.get('turn_number')
    )
    
    frame.events.add(event)
    
    serializer = MatchEventSerializer(event)
    
    # Broadcast event to WebSocket clients
    channel_layer = get_channel_layer()
    match_id = frame.match_id
    async_to_sync(channel_layer.group_send)(
        f'match_{match_id}',
        {
            'type': 'event_created',
            'data': serializer.data
        }
    )
    
    return Response(serializer.data, status=status.HTTP_201_CREATED)


@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
def biro_profiles(request):
    """
    Biro-only: Manage profiles (for player management)
    GET: List all profiles
    POST: Create new profile (with or without user account)
    """
    try:
        profile = Profile.objects.get(user=request.user)
        if not profile.is_biro:
            return Response({'error': 'Biro permission required'}, status=status.HTTP_403_FORBIDDEN)
    except Profile.DoesNotExist:
        return Response({'error': 'Profile not found'}, status=status.HTTP_404_NOT_FOUND)
    
    if request.method == 'GET':
        profiles = Profile.objects.all().select_related('user').order_by('-id')
        serializer = ProfileSerializer(profiles, many=True)
        return Response(serializer.data)
    
    elif request.method == 'POST':
        data = request.data
        
        # Create profile without user (player without login)
        if not data.get('user_id'):
            new_profile = Profile.objects.create(
                first_name=data.get('first_name', ''),
                last_name=data.get('last_name', ''),
                pfpURL=data.get('pfpURL', ''),
                is_biro=data.get('is_biro', False)
            )
            serializer = ProfileSerializer(new_profile)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        
        # Create profile with existing user
        else:
            try:
                user = User.objects.get(id=data.get('user_id'))
                # Check if profile already exists for this user
                if Profile.objects.filter(user=user).exists():
                    return Response({'error': 'Profile already exists for this user'}, 
                                  status=status.HTTP_400_BAD_REQUEST)
                
                new_profile = Profile.objects.create(
                    user=user,
                    pfpURL=data.get('pfpURL', ''),
                    is_biro=data.get('is_biro', False)
                )
                serializer = ProfileSerializer(new_profile)
                return Response(serializer.data, status=status.HTTP_201_CREATED)
            except User.DoesNotExist:
                return Response({'error': 'User not found'}, status=status.HTTP_404_NOT_FOUND)


@api_view(['GET', 'PUT', 'DELETE'])
@permission_classes([IsAuthenticated])
def biro_profile_detail(request, profile_id):
    """
    Biro-only: Manage specific profile
    GET: Get profile details
    PUT: Update profile
    DELETE: Delete profile
    """
    try:
        profile = Profile.objects.get(user=request.user)
        if not profile.is_biro:
            return Response({'error': 'Biro permission required'}, status=status.HTTP_403_FORBIDDEN)
    except Profile.DoesNotExist:
        return Response({'error': 'Profile not found'}, status=status.HTTP_404_NOT_FOUND)
    
    try:
        target_profile = Profile.objects.get(id=profile_id)
    except Profile.DoesNotExist:
        return Response({'error': 'Target profile not found'}, status=status.HTTP_404_NOT_FOUND)
    
    if request.method == 'GET':
        serializer = ProfileSerializer(target_profile)
        return Response(serializer.data)
    
    elif request.method == 'PUT':
        data = request.data
        
        # Update profile fields
        if 'first_name' in data:
            target_profile.first_name = data['first_name']
        if 'last_name' in data:
            target_profile.last_name = data['last_name']
        if 'pfpURL' in data:
            target_profile.pfpURL = data['pfpURL']
        if 'is_biro' in data:
            target_profile.is_biro = data['is_biro']
        
        target_profile.save()
        serializer = ProfileSerializer(target_profile)
        return Response(serializer.data)
    
    elif request.method == 'DELETE':
        target_profile.delete()
        return Response({'success': True, 'message': 'Profile deleted'}, 
                       status=status.HTTP_204_NO_CONTENT)
