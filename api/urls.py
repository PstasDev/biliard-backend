from django.urls import path
from .views import (
    login,
    tournament_list,
    tournament_detail,
    match_list,
    match_detail,
    profile_detail,
    my_profile,
    biro_tournaments,
    biro_tournament_detail,
    biro_phases,
    biro_phase_detail,
    biro_groups,
    biro_group_detail,
    biro_matches,
    biro_match_detail,
    biro_frames,
    biro_frame_detail,
    biro_create_event,
    biro_profiles,
    biro_profile_detail,
)


urlpatterns = [
    # Authentication
    path('login/', login, name='login'),
    
    # Public Endpoints
    path('tournaments/', tournament_list, name='tournament_list'),
    path('tournaments/<int:tournament_id>/', tournament_detail, name='tournament_detail'),
    path('matches/', match_list, name='match_list'),
    path('matches/<int:match_id>/', match_detail, name='match_detail'),
    
    # Profiles
    path('profile/', my_profile, name='my_profile'),
    path('profile/<int:user_id>/', profile_detail, name='profile_detail'),
    
    # Bíró Administration Endpoints
    # Tournaments
    path('biro/tournaments/', biro_tournaments, name='biro_tournaments'),
    path('biro/tournaments/<int:tournament_id>/', biro_tournament_detail, name='biro_tournament_detail'),
    
    # Phases
    path('biro/tournaments/<int:tournament_id>/phases/', biro_phases, name='biro_phases'),
    path('biro/phases/<int:phase_id>/', biro_phase_detail, name='biro_phase_detail'),
    
    # Groups
    path('biro/phases/<int:phase_id>/groups/', biro_groups, name='biro_groups'),
    path('biro/groups/<int:group_id>/', biro_group_detail, name='biro_group_detail'),
    
    # Matches
    path('biro/matches/', biro_matches, name='biro_matches'),
    path('biro/matches/<int:match_id>/', biro_match_detail, name='biro_match_detail'),
    
    # Frames
    path('biro/matches/<int:match_id>/frames/', biro_frames, name='biro_frames'),
    path('biro/frames/<int:frame_id>/', biro_frame_detail, name='biro_frame_detail'),
    
    # Events
    path('biro/frames/<int:frame_id>/events/', biro_create_event, name='biro_create_event'),
    
    # Profiles (for player management)
    path('biro/profiles/', biro_profiles, name='biro_profiles'),
    path('biro/profiles/<int:profile_id>/', biro_profile_detail, name='biro_profile_detail'),
]
