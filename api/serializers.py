from rest_framework import serializers
from django.contrib.auth.models import User
from .models import Profile, Tournament, Phase, Group, Match, Frame, MatchEvent


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'first_name', 'last_name', 'email']


class ProfileSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    full_name = serializers.CharField(source='get_full_name', read_only=True)
    display_name = serializers.CharField(source='get_display_name', read_only=True)
    
    class Meta:
        model = Profile
        fields = ['id', 'user', 'first_name', 'last_name', 'pfpURL', 'is_biro', 'full_name', 'display_name']


class MatchEventSerializer(serializers.ModelSerializer):
    player = ProfileSerializer(read_only=True)
    
    class Meta:
        model = MatchEvent
        fields = ['id', 'eventType', 'timestamp', 'details', 'turn_number', 'player', 'ball_ids']


class FrameSerializer(serializers.ModelSerializer):
    events = MatchEventSerializer(many=True, read_only=True)
    winner = ProfileSerializer(read_only=True)
    
    class Meta:
        model = Frame
        fields = ['id', 'frame_number', 'events', 'winner', 'player1_ball_group', 'player2_ball_group']


class MatchSerializer(serializers.ModelSerializer):
    player1 = ProfileSerializer(read_only=True)
    player2 = ProfileSerializer(read_only=True)
    match_frames = FrameSerializer(many=True, read_only=True)
    
    class Meta:
        model = Match
        fields = ['id', 'phase', 'group', 'player1', 'player2', 'match_date', 'frames_to_win', 'match_frames']


class MatchListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for match lists without frames"""
    player1 = ProfileSerializer(read_only=True)
    player2 = ProfileSerializer(read_only=True)
    
    class Meta:
        model = Match
        fields = ['id', 'phase', 'group', 'player1', 'player2', 'match_date', 'frames_to_win']


class GroupSerializer(serializers.ModelSerializer):
    matches = MatchListSerializer(many=True, read_only=True)
    
    class Meta:
        model = Group
        fields = ['id', 'name', 'matches']


class PhaseSerializer(serializers.ModelSerializer):
    groups = GroupSerializer(many=True, read_only=True)
    matches = MatchListSerializer(many=True, read_only=True)
    
    class Meta:
        model = Phase
        fields = ['id', 'order', 'eliminationSystem', 'groups', 'matches']


class TournamentSerializer(serializers.ModelSerializer):
    phases = PhaseSerializer(many=True, read_only=True)
    
    class Meta:
        model = Tournament
        fields = ['id', 'name', 'startDate', 'endDate', 'location', 'gameMode', 'phases']


class TournamentListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for tournament lists"""
    
    class Meta:
        model = Tournament
        fields = ['id', 'name', 'startDate', 'endDate', 'location', 'gameMode']
