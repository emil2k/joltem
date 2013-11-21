""" Account listeners. """

from django.contrib.auth.signals import user_logged_in

from .models import OAuth


def attach_oauth(sender, request=None, user=None, **kwargs):
    """ Attach verified OAuth to logged user. """

    for service, oauth in request.session.get('oauth', {}).items():
        if oauth.get('service_id'):
            OAuth.objects.get_or_create(
                service=service,
                service_id=oauth.get('service_id'),
                user=user,
                username=oauth.get('username'),
            )

    request.session['oauth'] = {}
    request.session.save()


user_logged_in.connect(attach_oauth)
