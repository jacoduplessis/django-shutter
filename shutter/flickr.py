import requests
from allauth.socialaccount.models import SocialApp, SocialToken
from requests_oauthlib import OAuth1


class API(requests.Session):
    def __init__(self, api_key, auth):
        super().__init__()

        self.api_key = api_key
        self.auth = auth
        self.url_base = 'https://api.flickr.com/services/rest/'

    def request(self, method, url, **kwargs):
        params = {
            'api_key': self.api_key,
            'format': 'json',
            'nojsoncallback': 1,
            'method': url
        }

        kwargs['params'] = {**params, **kwargs.pop('params', {})}
        kwargs['auth'] = self.auth

        return super().request(method, self.url_base, **kwargs)


def get_user_oauth(app=None, user=None):
    token = SocialToken.objects.filter(app__provider='flickr', account__user=user).first()
    if token is None:
        return None

    auth = OAuth1(
        client_key=app.client_id,
        client_secret=app.secret,
        resource_owner_key=token.token,
        resource_owner_secret=token.token_secret
    )
    return auth


def get_flickr_app():
    return SocialApp.objects.filter(provider='flickr').first()


def get_flickr_api_user_session(user):
    app = get_flickr_app()
    oauth = get_user_oauth(app, user)
    return API(
        api_key=app.client_id,
        auth=oauth,
    )
