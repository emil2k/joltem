# coding: utf-8
from django.conf import settings
from django.core.urlresolvers import reverse


class ViewTestMixin(object):

    def _test_sign_in_redirect_url(self, response, url):
        login_url = '{}?next={}'.format(
            reverse(settings.LOGIN_URL),
            url,
        )
        self.assertRedirects(response, login_url)
