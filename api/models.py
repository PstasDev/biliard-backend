from django.db import models

balls = [
    {'id': 'cue', 'name': 'Kijátszó golyó', 'color': 'white'},
    {'id': '1', 'name': '1-es golyó', 'color': 'yellow', 'full': True},
    {'id': '2', 'name': '2-es golyó', 'color': 'blue', 'full': True},
    {'id': '3', 'name': '3-as golyó', 'color': 'red', 'full': True},
    {'id': '4', 'name': '4-es golyó', 'color': 'purple', 'full': True},
    {'id': '5', 'name': '5-ös golyó', 'color': 'orange', 'full': True},
    {'id': '6', 'name': '6-os golyó', 'color': 'green', 'full': True},
    {'id': '7', 'name': '7-es golyó', 'color': 'maroon', 'full': True},
    {'id': '8', 'name': '8-as golyó', 'color': 'black', 'full': True},
    {'id': '9', 'name': '9-es golyó', 'color': 'yellow', 'full': False},
    {'id': '10', 'name': '10-es golyó', 'color': 'blue', 'full': False},
    {'id': '11', 'name': '11-es golyó', 'color': 'red', 'full': False},
    {'id': '12', 'name': '12-es golyó', 'color': 'purple', 'full': False},
    {'id': '13', 'name': '13-as golyó', 'color': 'orange', 'full': False},
    {'id': '14', 'name': '14-es golyó', 'color': 'green', 'full': False},
    {'id': '15', 'name': '15-ös golyó', 'color': 	'maroon',  'full': False},
]

class Profile(models.Model):
    # System
    user = models.OneToOneField('auth.User', on_delete=models.CASCADE, null=True, blank=True)

    # Profile details - required for players without user accounts
    first_name = models.CharField(max_length=150, blank=True, null=True)
    last_name = models.CharField(max_length=150, blank=True, null=True)
    pfpURL = models.CharField(max_length=255, blank=True, null=True)

    def full_name(self):
        """Get full name from user or profile fields"""
        if self.user:
            return f"{self.user.last_name} {self.user.first_name}".strip() or self.user.username
        else:
            return f"{self.last_name} {self.first_name}".strip() or "Névtelen játékos"

    # Permissions
    is_biro = models.BooleanField(default=False)

    class Meta:
        verbose_name = "Profil"
        verbose_name_plural = "Profilok"

    def __str__(self):
        if self.user:
            return f"{self.user.last_name} {self.user.first_name} || {self.user.username} profilja"
        else:
            return f"{self.last_name} {self.first_name} (nincs felhasználó)"
    
    def get_full_name(self):
        """Get full name from user or profile fields"""
        if self.user:
            return f"{self.user.last_name} {self.user.first_name}".strip() or self.user.username
        else:
            return f"{self.last_name} {self.first_name}".strip() or "Névtelen játékos"
    
    def get_display_name(self):
        """Get display name (username or name)"""
        if self.user:
            return self.user.username
        else:
            return self.get_full_name()
    
class Tournament(models.Model):
    name = models.CharField(max_length=100)
    startDate = models.DateField(null=True, blank=True)
    endDate = models.DateField(null=True, blank=True)
    location = models.CharField(max_length=255)

    GAMEMODE_8BALL = '8ball'
    GAMEMODE_SNOOKER = 'snooker'

    GAMEMODES = [
        (GAMEMODE_8BALL, '8 Ball'),
        (GAMEMODE_SNOOKER, 'Snooker'),
    ]

    gameMode = models.CharField(max_length=50, choices=GAMEMODES, default=GAMEMODE_8BALL)

    class Meta:
        verbose_name = "Bajnokság"
        verbose_name_plural = "Bajnokságok"

    def __str__(self):
        return self.name
    
class Phase(models.Model):
    tournament = models.ForeignKey(Tournament, on_delete=models.CASCADE, related_name='phases')
    order = models.PositiveIntegerField()

    # Csoportkörök vagy egyenes kieséses rendszer

    GROUP_STAGE = 'group'
    ELIMINATION = 'elimination'

    ELIMINATION_SYSTEMS = [
        (GROUP_STAGE, 'Csoportkör'),
        (ELIMINATION, 'Egyenes kieséses'),
    ]

    eliminationSystem = models.CharField(max_length=50, choices=ELIMINATION_SYSTEMS, default=ELIMINATION)

    class Meta:
        verbose_name = "Szakasz"
        verbose_name_plural = "Szakaszok"
        ordering = ['order']

    def __str__(self):
        return f"{self.tournament.name} - {self.order}. szakasz - {self.eliminationSystem}"
    
class Group(models.Model):
    phase = models.ForeignKey(Phase, on_delete=models.CASCADE, related_name='groups')
    name = models.CharField(max_length=100)

    class Meta:
        verbose_name = "Csoport"
        verbose_name_plural = "Csoportok"

    def __str__(self):
        return f"{self.phase.tournament.name} - {self.name} csoport"
        
class MatchEvent(models.Model):
    FRAME_START = 'start'
    FRAME_END = 'end'
    NEXT_PLAYER = 'next_player'
    SCORE_UPDATE = 'score_update'
    BALLS_POTTED = 'balls_potted'
    FAUL = 'faul'
    FAUL_AND_NEXT_PLAYER = 'faul_and_next_player'
    CUE_BALL_LEFT_TABLE = 'cue_ball_left_table'
    CUE_BALL_GETS_POSITIONED = 'cue_ball_gets_positioned'

    EVENT_TYPES = [
        (FRAME_START, 'Frame kezdete'),
        (FRAME_END, 'Frame vége'),
        (NEXT_PLAYER, 'Következő játékos'),
        (SCORE_UPDATE, 'Pontszám frissítés'),
        (BALLS_POTTED, 'Golyók belövése'),
        (FAUL, 'Hiba'),
        (FAUL_AND_NEXT_PLAYER, 'Hiba és következő játékos'),
        (CUE_BALL_LEFT_TABLE, 'Kijátszó golyó elhagyta az asztalt'),
        (CUE_BALL_GETS_POSITIONED, 'Kijátszó golyó pozícionálása'),
    ]

    eventType = models.CharField(max_length=50, choices=EVENT_TYPES)
    timestamp = models.DateTimeField(auto_now_add=True)
    details = models.TextField(blank=True, null=True)
    turn_number = models.PositiveIntegerField(null=True, blank=True)
    
    # Possible relations
    player = models.ForeignKey(Profile, on_delete=models.CASCADE, related_name='match_events', null=True, blank=True)
    ball_ids = models.JSONField(null=True, blank=True)  # List of ball IDs involved in the event

    class Meta:
        verbose_name = "Mérkőzés esemény"
        verbose_name_plural = "Mérkőzés események"

    def __str__(self):
        return f"{self.eventType} at {self.timestamp}"

class Frame(models.Model):
    match = models.ForeignKey('Match', on_delete=models.CASCADE, related_name='match_frames')
    frame_number = models.PositiveIntegerField()
    
    events = models.ManyToManyField(MatchEvent, blank=True)
    winner = models.ForeignKey(Profile, on_delete=models.CASCADE, related_name='frames_won', null=True, blank=True)
    
    # Ball groups for 8-ball: 'full' (solid) or 'striped'
    BALL_GROUP_FULL = 'full'
    BALL_GROUP_STRIPED = 'striped'
    BALL_GROUPS = [
        (BALL_GROUP_FULL, 'Full (Solid)'),
        (BALL_GROUP_STRIPED, 'Striped'),
    ]
    
    player1_ball_group = models.CharField(max_length=10, choices=BALL_GROUPS, null=True, blank=True)
    player2_ball_group = models.CharField(max_length=10, choices=BALL_GROUPS, null=True, blank=True)

    def get_balls_on_table(self):
        # Initial state: all balls are on the table
        balls_on_table = {ball['id']: True for ball in balls if ball['id'] != 'cue'}

        # Process events to update the state of balls on the table
        for event in self.events.all().order_by('timestamp'):
            if event.eventType == MatchEvent.BALLS_POTTED and event.ball_ids:
                for ball_id in event.ball_ids:
                    balls_on_table[ball_id] = False  # Ball has been potted

        return [ball_id for ball_id, on_table in balls_on_table.items() if on_table]

    def return_events_as_turns(self):
        # Turns are splitted by NEXT_PLAYER events
        # Can be fetched mid-frame or after frame
        turns = []
        current_turn = []
        for event in self.events.all().order_by('timestamp'):
            if event.eventType == MatchEvent.NEXT_PLAYER and current_turn:
                turns.append(current_turn)
                current_turn = []
            current_turn.append(event)
        if current_turn:
            turns.append(current_turn)
        return turns
    
    class Meta:
        verbose_name = "Frame"
        verbose_name_plural = "Frame-ek"

    def __str__(self):
        return f"Mérkőzés {self.match.id} - Frame {self.frame_number}"

class Match(models.Model):
    phase = models.ForeignKey(Phase, on_delete=models.CASCADE, related_name='matches')
    group = models.ForeignKey(Group, on_delete=models.CASCADE, related_name='matches', null=True, blank=True)
    player1 = models.ForeignKey(Profile, on_delete=models.CASCADE, related_name='matches_as_player1')
    player2 = models.ForeignKey(Profile, on_delete=models.CASCADE, related_name='matches_as_player2')
    match_date = models.DateTimeField(null=True, blank=True)

    frames_to_win = models.PositiveIntegerField(default=5)

    # YouTube LIVE broadcast URL if available
    broadcastURL = models.CharField(max_length=255, blank=True, null=True)

    class Meta:
        verbose_name = "Mérkőzés"
        verbose_name_plural = "Mérkőzések"

    def __str__(self):
        return f"{self.player1.get_display_name()} vs {self.player2.get_display_name()} - {self.phase.tournament.name}"