from functools import wraps
from django.http import JsonResponse
from rest_framework_simplejwt.tokens import AccessToken
from rest_framework_simplejwt.exceptions import TokenError, InvalidToken
from .models import Profile


def jwt_required(view_func):
    """
    Decorator to check if JWT token is valid and attach user to request
    """
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        auth_header = request.headers.get('Authorization', '')
        
        if not auth_header.startswith('Bearer '):
            return JsonResponse({'error': 'Missing or invalid Authorization header'}, status=401)
        
        token = auth_header.split(' ')[1]
        
        try:
            access_token = AccessToken(token)
            user_id = access_token['user_id']
            
            # Attach user_id to request for view access
            from django.contrib.auth.models import User
            request.user = User.objects.get(id=user_id)
            
        except (TokenError, InvalidToken) as e:
            return JsonResponse({'error': 'Invalid or expired token', 'detail': str(e)}, status=401)
        except User.DoesNotExist:
            return JsonResponse({'error': 'User not found'}, status=404)
        
        return view_func(request, *args, **kwargs)
    
    return wrapper


def biro_required(view_func):
    """
    Decorator to check if user is a biro (requires jwt_required as well)
    """
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not hasattr(request, 'user'):
            return JsonResponse({'error': 'Authentication required'}, status=401)
        
        try:
            profile = Profile.objects.get(user=request.user)
            if not profile.is_biro:
                return JsonResponse({'error': 'Biro permission required'}, status=403)
            
            # Attach profile to request for convenience
            request.profile = profile
            
        except Profile.DoesNotExist:
            return JsonResponse({'error': 'Profile not found'}, status=404)
        
        return view_func(request, *args, **kwargs)
    
    return wrapper


def get_user_from_token(token_string):
    """
    Helper function to extract user from JWT token
    Returns User object or None
    """
    try:
        access_token = AccessToken(token_string)
        user_id = access_token['user_id']
        
        from django.contrib.auth.models import User
        return User.objects.get(id=user_id)
    except:
        return None


def get_profile_from_token(token_string):
    """
    Helper function to extract profile from JWT token
    Returns Profile object or None
    """
    user = get_user_from_token(token_string)
    if user:
        try:
            return Profile.objects.get(user=user)
        except Profile.DoesNotExist:
            return None
    return None
