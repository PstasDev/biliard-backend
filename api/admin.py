from django.contrib import admin
from .models import Profile, Tournament, Phase, Group, Match, Frame, MatchEvent

customBranding = "Biliárd Adminisztráció"

admin.site.site_header = customBranding
admin.site.site_title = customBranding
admin.site.index_title = "Biliárd Adminisztációs Felület"

@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ['__str__', 'get_display_name', 'is_biro', 'pfpURL']
    list_filter = ['is_biro']
    search_fields = ['user__username', 'user__first_name', 'user__last_name', 'first_name', 'last_name']
    raw_id_fields = ['user']
    
    def get_display_name(self, obj):
        return obj.get_display_name()
    get_display_name.short_description = 'Megjelenítési név'


@admin.register(Tournament)
class TournamentAdmin(admin.ModelAdmin):
    list_display = ['name', 'gameMode', 'startDate', 'endDate', 'location']
    list_filter = ['gameMode', 'startDate']
    search_fields = ['name', 'location']
    date_hierarchy = 'startDate'


class PhaseInline(admin.TabularInline):
    model = Phase
    extra = 1
    show_change_link = True


@admin.register(Phase)
class PhaseAdmin(admin.ModelAdmin):
    list_display = ['__str__', 'tournament', 'order', 'eliminationSystem']
    list_filter = ['eliminationSystem', 'tournament']
    ordering = ['tournament', 'order']


class GroupInline(admin.TabularInline):
    model = Group
    extra = 1
    show_change_link = True


@admin.register(Group)
class GroupAdmin(admin.ModelAdmin):
    list_display = ['name', 'phase']
    list_filter = ['phase__tournament']
    search_fields = ['name']


class FrameInline(admin.TabularInline):
    model = Frame
    extra = 0
    show_change_link = True
    fields = ['frame_number', 'winner']


@admin.register(Match)
class MatchAdmin(admin.ModelAdmin):
    list_display = ['__str__', 'phase', 'group', 'match_date', 'frames_to_win']
    list_filter = ['phase__tournament', 'phase', 'group', 'match_date']
    search_fields = ['player1__user__username', 'player2__user__username']
    raw_id_fields = ['player1', 'player2']
    date_hierarchy = 'match_date'
    inlines = [FrameInline]
    
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.select_related('player1__user', 'player2__user', 'phase__tournament', 'group')


class MatchEventInline(admin.TabularInline):
    model = Frame.events.through
    extra = 0
    verbose_name = "Match Event"
    verbose_name_plural = "Match Events"


@admin.register(Frame)
class FrameAdmin(admin.ModelAdmin):
    list_display = ['__str__', 'match', 'frame_number', 'winner']
    list_filter = ['match__phase__tournament']
    raw_id_fields = ['match', 'winner']
    filter_horizontal = ['events']
    
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.select_related('match', 'winner__user')


@admin.register(MatchEvent)
class MatchEventAdmin(admin.ModelAdmin):
    list_display = ['eventType', 'timestamp', 'player', 'turn_number']
    list_filter = ['eventType', 'timestamp']
    search_fields = ['details']
    raw_id_fields = ['player']
    readonly_fields = ['timestamp']
    date_hierarchy = 'timestamp'
    
    fieldsets = (
        ('Event Information', {
            'fields': ('eventType', 'timestamp', 'turn_number')
        }),
        ('Details', {
            'fields': ('player', 'ball_ids', 'details')
        }),
    )
    
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.select_related('player__user')
