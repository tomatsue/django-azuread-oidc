import uuid
import msal
import requests
from django.shortcuts import redirect
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from django.contrib.auth import get_user_model

from mysite import settings

User = get_user_model()


@login_required
def index(request):
    context = {'user': request.user}
    return render(request, 'accounts/index.html', context)


@login_required
def logout_view(request):
    logout(request)
    return redirect('/')


def login_view(request):
    request.session['state'] = str(uuid.uuid4())
    auth_url = _build_auth_url(
        scopes=settings.SCOPES, state=request.session['state'])
    context = {'auth_url': auth_url}
    return render(request, 'accounts/login.html', context)


def callback_view(request):
    if request.GET.get('state') != request.session.get("state"):
        return redirect('/')  # No-OP. Goes back to Index page
    if request.GET.get('error'):  # Authentication/Authorization failure
        return render(request, 'accounts/auth_error.html', request.GET)
    if request.GET.get('code'):
        cache = _load_cache(request)
        result = _build_msal_app(cache=cache).acquire_token_by_authorization_code(
            request.GET['code'],
            scopes=settings.SCOPES,  # Misspelled scope would cause an HTTP 400 error here
            redirect_uri=settings.REDIRECT_PATH)
        if 'error' in result:
            return render(request, 'accounts/auth_error.html', result)
        request.session['user'] = result.get('id_token_claims')
        _save_cache(request, cache)

    try:
        oid = request.session['user']['oid']
        user = User.objects.get(external_id=oid)
        login(request, user)
    except User.DoesNotExist as e:
        context = {'error': 'User.DoesNotExist', 'error_description': str(e)}
        return render(request, 'accounts/auth_error.html', context)

    return redirect('/')


@login_required
def graphcall_view(request):
    token = _get_token_from_cache(request, settings.SCOPES)
    if not token:
        return redirect('/')
    graph_data = requests.get(  # Use token to call downstream service
        settings.ENDPOINT,
        headers={'Authorization': 'Bearer ' + token['access_token']},
    ).json()
    return render(request, 'accounts/display.html', {'result': graph_data})


def _build_auth_url(authority=None, scopes=None, state=None):
    return _build_msal_app(authority=authority).get_authorization_request_url(
        scopes or [],
        state=state or str(uuid.uuid4()),
        redirect_uri=settings.REDIRECT_PATH)


def _build_msal_app(cache=None, authority=None):
    return msal.ConfidentialClientApplication(
        settings.CLIENT_ID, authority=settings.AUTHORITY,
        client_credential=settings.CLIENT_SECRET, token_cache=cache)


def _load_cache(request):
    cache = msal.SerializableTokenCache()
    if request.session.get('token_cache'):
        cache.deserialize(request.session['token_cache'])
    return cache


def _save_cache(request, cache):
    print(request.session)
    print(cache)
    if cache.has_state_changed:
        request.session['token_cache'] = cache.serialize()


def _get_token_from_cache(request, scope=None):
    # This web app maintains one cache per session
    cache = _load_cache(request)
    cca = _build_msal_app(cache=cache)
    accounts = cca.get_accounts()
    if accounts:  # So all account(s) belong to the current signed-in user
        result = cca.acquire_token_silent(scope, account=accounts[0])
        _save_cache(request, cache)
        return result
