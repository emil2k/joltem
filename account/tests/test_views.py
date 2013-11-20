# coding: utf-8
from django_webtest import WebTest
from django.test import TestCase

from git.models import Authentication
from joltem.libs.mix import mixer
from joltem.libs.tests import ViewTestMixin
from joltem.models import User


MAIN_PAGE_URL = '/'
SIGN_UP_URL = '/account/sign-up/'
SIGN_UP_FORM_ID = 'sign-up-form'


class SignUpTest(WebTest):

    def setUp(self):
        # We need at least one project.
        mixer.blend('project.project')

    def test_redirect_to_main_page_when_user_is_logged_in(self):
        user = mixer.blend('joltem.user')

        with self.settings(LOGIN_REDIRECT_URL=MAIN_PAGE_URL):
            response = self.app.get(SIGN_UP_URL, user=user)

        expected_redirect_url = '{}?next={}'.format(MAIN_PAGE_URL, SIGN_UP_URL)

        self.assertRedirects(
            response,
            expected_redirect_url,
            target_status_code=302,
        )

    def test_user_is_redirected_to_intro_page_after_registration(self):
        response = self.app.get(SIGN_UP_URL)

        form = response.forms[SIGN_UP_FORM_ID]
        form['username'] = 'bob'
        form['first_name'] = 'Bob'
        form['email'] = 'bob@example.com'
        form['password1'] = '123'
        form['password2'] = '123'
        response = form.submit()

        expected_redirect_url = '/intro/'

        self.assertRedirects(response, expected_redirect_url)

    def test_user_is_authenticated_after_registration(self):
        response = self.app.get(SIGN_UP_URL)

        form = response.forms[SIGN_UP_FORM_ID]
        form['username'] = 'bob'
        form['first_name'] = 'Bob'
        form['email'] = 'bob@example.com'
        form['password1'] = '123'
        form['password2'] = '123'
        response = form.submit()

        user = User.objects.get(username='bob')

        self.assertTrue(user.is_authenticated())


class SignUpRequiredFieldsTest(WebTest):

    error_message = 'This field is required.'

    def test_username_is_required(self):
        response = self.app.get(SIGN_UP_URL)

        form = response.forms[SIGN_UP_FORM_ID]
        response = form.submit()

        self.assertFormError(
            response,
            'form',
            'username',
            errors=self.error_message,
        )

    def test_first_name_is_required(self):
        response = self.app.get(SIGN_UP_URL)

        form = response.forms[SIGN_UP_FORM_ID]
        response = form.submit()

        self.assertFormError(
            response,
            'form',
            'first_name',
            errors=self.error_message,
        )

    def test_last_name_is_not_required(self):
        response = self.app.get(SIGN_UP_URL)

        form = response.forms[SIGN_UP_FORM_ID]
        response = form.submit()

        self.assertFormError(
            response,
            'form',
            'last_name',
            errors=[],
        )

    def test_email_is_required(self):
        response = self.app.get(SIGN_UP_URL)

        form = response.forms[SIGN_UP_FORM_ID]
        response = form.submit()

        self.assertFormError(
            response,
            'form',
            'email',
            errors=self.error_message,
        )

    def test_gravatar_email_is_not_required(self):
        response = self.app.get(SIGN_UP_URL)

        form = response.forms[SIGN_UP_FORM_ID]
        response = form.submit()

        self.assertFormError(
            response,
            'form',
            'gravatar_email',
            errors=[],
        )

    def test_password1_is_required(self):
        response = self.app.get(SIGN_UP_URL)

        form = response.forms[SIGN_UP_FORM_ID]
        response = form.submit()

        self.assertFormError(
            response,
            'form',
            'password1',
            errors=self.error_message,
        )

    def test_password2_is_required(self):
        response = self.app.get(SIGN_UP_URL)

        form = response.forms[SIGN_UP_FORM_ID]
        response = form.submit()

        self.assertFormError(
            response,
            'form',
            'password1',
            errors=self.error_message,
        )


class SignUpValidateUsernameTest(WebTest):

    error_message = 'This value may contain only letters and numbers.'

    def test_can_contain_latin_letters(self):
        response = self.app.get(SIGN_UP_URL)

        form = response.forms[SIGN_UP_FORM_ID]
        form['username'] = u'validname'
        response = form.submit()

        self.assertFormError(
            response,
            'form',
            'username',
            errors=[],
        )

    def test_cannot_contain_non_latin_letters(self):
        response = self.app.get(SIGN_UP_URL)

        form = response.forms[SIGN_UP_FORM_ID]
        form['username'] = u'бла'
        response = form.submit()

        self.assertFormError(
            response,
            'form',
            'username',
            errors=self.error_message,
        )

    def test_can_contain_arabic_digits(self):
        response = self.app.get(SIGN_UP_URL)

        form = response.forms[SIGN_UP_FORM_ID]
        form['username'] = u'0123456789'
        response = form.submit()

        self.assertFormError(
            response,
            'form',
            'username',
            errors=[],
        )

    def test_cannot_contain_non_arabic_digits(self):
        response = self.app.get(SIGN_UP_URL)

        form = response.forms[SIGN_UP_FORM_ID]
        # ``\d`` regex is valid for "๓".
        thai_number_four = u'๓'
        form['username'] = thai_number_four
        response = form.submit()

        self.assertFormError(
            response,
            'form',
            'username',
            errors=self.error_message,
        )

    def test_cannot_contain_hyphen(self):
        response = self.app.get(SIGN_UP_URL)

        form = response.forms[SIGN_UP_FORM_ID]
        form['username'] = u'foo-bar'
        response = form.submit()

        self.assertFormError(
            response,
            'form',
            'username',
            errors=self.error_message,
        )

    def test_cannot_contain_undescore(self):
        response = self.app.get(SIGN_UP_URL)

        form = response.forms[SIGN_UP_FORM_ID]
        form['username'] = u'ya_da'
        response = form.submit()

        self.assertFormError(
            response,
            'form',
            'username',
            errors=self.error_message,
        )


ACCOUNT_URL = '/account/'
GENERAL_SETTINGS_FORM_ID = 'account-general-settings-form'


class GeneralSettingsTest(WebTest, ViewTestMixin):

    def setUp(self):
        self.user = mixer.blend('joltem.user')

    def test_redirect_to_login_page_when_user_is_not_logged_in(self):
        response = self.app.get(ACCOUNT_URL)

        self._test_sign_in_redirect_url(response, ACCOUNT_URL)

    def test_user_is_redirected_to_account_page_after_saving_settings(self):
        response = self.app.get(ACCOUNT_URL, user=self.user)

        form = response.forms[GENERAL_SETTINGS_FORM_ID]
        response = form.submit()

        self.assertRedirects(response, ACCOUNT_URL)

    def test_gravatar_is_changed_after_saving_settings(self):
        response = self.app.get(ACCOUNT_URL, user=self.user)

        form = response.forms[GENERAL_SETTINGS_FORM_ID]
        form['gravatar_email'] = 'fizz@example.com'
        response = form.submit()

        form = response.follow().forms[GENERAL_SETTINGS_FORM_ID]

        self.assertEqual(form['gravatar_email'].value, 'fizz@example.com')


class GeneralSettingsRequiredFieldsTest(WebTest):

    error_message = 'This field is required.'

    def setUp(self):
        self.user = mixer.blend('joltem.user')

    def test_first_name_is_required(self):
        response = self.app.get(ACCOUNT_URL, user=self.user)

        form = response.forms[GENERAL_SETTINGS_FORM_ID]
        form['first_name'] = ''
        response = form.submit()

        self.assertFormError(
            response,
            'form',
            'first_name',
            errors=self.error_message,
        )

    def test_last_name_is_not_required(self):
        response = self.app.get(ACCOUNT_URL, user=self.user)

        form = response.forms[GENERAL_SETTINGS_FORM_ID]
        form['last_name'] = ''
        response = form.submit()

        self.assertRedirects(response, ACCOUNT_URL)

    def test_email_is_required(self):
        response = self.app.get(ACCOUNT_URL, user=self.user)

        form = response.forms[GENERAL_SETTINGS_FORM_ID]
        form['email'] = ''
        response = form.submit()

        self.assertFormError(
            response,
            'form',
            'email',
            errors=self.error_message,
        )

    def test_gravatar_email_is_not_required(self):
        response = self.app.get(ACCOUNT_URL, user=self.user)

        form = response.forms[GENERAL_SETTINGS_FORM_ID]
        form['gravatar_email'] = ''
        response = form.submit()

        self.assertRedirects(response, ACCOUNT_URL)


ACCOUNT_SSH_KEYS_URL = '/account/keys/'
SSH_KEY_FORM_ID = 'account-ssh-keys-form'


class AccountSSHKeysTest(WebTest, ViewTestMixin):

    public_rsa_openssh = (
        "ssh-rsa AAAAB3NzaC1yc2EAAAABIwAAAGEArzJx8OYOnJmzf4tfBE"
        "vLi8DVPrJ3/c9k2I/Az64fxjHf9imyRJbixtQhlH9lfNjUIx+4LmrJH"
        "5QNRsFporcHDKOTwTTYLh5KmRpslkYHRivcJSkbh/C+BR3utDS555mV comment"
    )
    public_rsa_openssh_fingerprint = (
        '3d:13:5f:cb:c9:79:8a:93:06:27:65:bc:3d:0b:8f:af'
    )

    def setUp(self):
        self.user = mixer.blend('joltem.user')

    def test_redirect_to_login_page_when_user_is_not_logged_in(self):
        response = self.app.get(ACCOUNT_SSH_KEYS_URL)

        self._test_sign_in_redirect_url(response, ACCOUNT_SSH_KEYS_URL)

    def test_fingerprint_is_created_after_adding_private_ssh_key(self):
        response = self.app.get(ACCOUNT_SSH_KEYS_URL, user=self.user)

        form = response.forms[SSH_KEY_FORM_ID]
        form['name'] = 'my mac'
        form['key'] = self.public_rsa_openssh
        response = form.submit()

        ssh_key_instance = Authentication.objects.get()

        self.assertEqual(
            ssh_key_instance.fingerprint,
            self.public_rsa_openssh_fingerprint
        )


class AccountSSHKeysRequiredFieldsTest(WebTest):

    error_message = 'This field is required.'

    def setUp(self):
        self.user = mixer.blend('joltem.user')

    def test_name_is_required(self):
        response = self.app.get(ACCOUNT_SSH_KEYS_URL, user=self.user)

        form = response.forms[SSH_KEY_FORM_ID]
        form['name'] = ''
        response = form.submit()

        self.assertFormError(
            response,
            'form',
            'name',
            errors=self.error_message,
        )

    def test_key_is_required(self):
        response = self.app.get(ACCOUNT_SSH_KEYS_URL, user=self.user)

        form = response.forms[SSH_KEY_FORM_ID]
        form['key'] = ''
        response = form.submit()

        self.assertFormError(
            response,
            'form',
            'key',
            errors=self.error_message,
        )


class AccountSSHKeysValidateKeyTest(WebTest):

    error_messages = {
        'unknown_key': 'Cannot guess the type of given key.',
        'must_be_rsa': 'SSH key has to be RSA.',
        'must_be_public': 'SSH key has to be private.',
    }

    private_rsa_openssh = """-----BEGIN RSA PRIVATE KEY-----
MIIByAIBAAJhAK8ycfDmDpyZs3+LXwRLy4vA1T6yd/3PZNiPwM+uH8Yx3/YpskSW
4sbUIZR/ZXzY1CMfuC5qyR+UDUbBaaK3Bwyjk8E02C4eSpkabJZGB0Yr3CUpG4fw
vgUd7rQ0ueeZlQIBIwJgbh+1VZfr7WftK5lu7MHtqE1S1vPWZQYE3+VUn8yJADyb
Z4fsZaCrzW9lkIqXkE3GIY+ojdhZhkO1gbG0118sIgphwSWKRxK0mvh6ERxKqIt1
xJEJO74EykXZV4oNJ8sjAjEA3J9r2ZghVhGN6V8DnQrTk24Td0E8hU8AcP0FVP+8
PQm/g/aXf2QQkQT+omdHVEJrAjEAy0pL0EBH6EVS98evDCBtQw22OZT52qXlAwZ2
gyTriKFVoqjeEjt3SZKKqXHSApP/AjBLpF99zcJJZRq2abgYlf9lv1chkrWqDHUu
DZttmYJeEfiFBBavVYIF1dOlZT0G8jMCMBc7sOSZodFnAiryP+Qg9otSBjJ3bQML
pSTqy7c3a2AScC/YyOwkDaICHnnD3XyjMwIxALRzl0tQEKMXs6hH8ToUdlLROCrP
EhQ0wahUTCk1gKA4uPD6TMTChavbh4K63OvbKg==
-----END RSA PRIVATE KEY-----"""

    public_rsa_openssh = (
        "ssh-rsa AAAAB3NzaC1yc2EAAAABIwAAAGEArzJx8OYOnJmzf4tfBE"
        "vLi8DVPrJ3/c9k2I/Az64fxjHf9imyRJbixtQhlH9lfNjUIx+4LmrJH"
        "5QNRsFporcHDKOTwTTYLh5KmRpslkYHRivcJSkbh/C+BR3utDS555mV comment"
    )

    public_rsa_with_newlines = """ssh-rsa AAAAB3NzaC1yc2EAAAABIwAAAGEArzJx8OYOnJmzf4tfBE
vLi8DVPrJ3/c9k2I/Az64fxjHf9imyRJbixtQhlH9lfNjUIx+4LmrJH
5QNRsFporcHDKOTwTTYLh5KmRpslkYHRivcJSkbh/C+BR3utDS555mV comment
"""

    public_dsa_lsh = (
        "{KDEwOnB1YmxpYy1rZXkoMzpkc2EoMTpwNjU6AIbwTOSsZ7Bl7U1KyMNqV"
        "13Tu7yRAtTr70PVI3QnfrPumf2UzCgpL1ljbKxSfAi05XvrE/1vfCFAsFY"
        "XRZLhQy0pKDE6cTIxOgDPeuQJJqOngIuyvpPag0eE6LRQFykoMTpnNjQ6A"
        "NmWlNb3riFpBZLi8LTrc0Z2V1PrGlQYNwNGpub3QKg8RrZGY0646qLyWdu"
        "FitoTPKlgfcrgbO/9vEIGcq0dFSkoMTp5NjQ6K+1osyWBS0+P90u/rAuko"
        "6chZ98thUSY2kLSHp6hLKyy2bjnT29h7haELE+XHfq2bM9fckDx2FLOSIJ"
        "zy83VmSkpKQ==}"
    )

    def setUp(self):
        self.user = mixer.blend('joltem.user')

    def test_validation_passes_when_public_rsa_key_is_given(self):
        response = self.app.get(ACCOUNT_SSH_KEYS_URL, user=self.user)

        form = response.forms[SSH_KEY_FORM_ID]
        form['name'] = 'my key'
        form['key'] = self.public_rsa_openssh
        response = form.submit()

        self.assertRedirects(response, ACCOUNT_SSH_KEYS_URL)

        self.assertContains(response.follow(), 'my key')

    def test_error_when_non_rsa_key_is_given(self):
        response = self.app.get(ACCOUNT_SSH_KEYS_URL, user=self.user)

        form = response.forms[SSH_KEY_FORM_ID]
        form['key'] = self.public_dsa_lsh
        response = form.submit()

        self.assertFormError(
            response,
            'form',
            'key',
            errors=self.error_messages['must_be_rsa'],
        )

    def test_error_when_private_rsa_key_is_given(self):
        response = self.app.get(ACCOUNT_SSH_KEYS_URL, user=self.user)

        form = response.forms[SSH_KEY_FORM_ID]
        form['key'] = self.private_rsa_openssh
        response = form.submit()

        self.assertFormError(
            response,
            'form',
            'key',
            errors=self.error_messages['must_be_public'],
        )

    def test_error_when_dummy_string_is_given(self):
        response = self.app.get(ACCOUNT_SSH_KEYS_URL, user=self.user)

        form = response.forms[SSH_KEY_FORM_ID]
        form['key'] = 'dummy'
        response = form.submit()

        self.assertFormError(
            response,
            'form',
            'key',
            errors=self.error_messages['unknown_key'],
        )

    def test_error_when_public_rsa_with_newlines_is_given(self):
        response = self.app.get(ACCOUNT_SSH_KEYS_URL, user=self.user)

        form = response.forms[SSH_KEY_FORM_ID]
        form['key'] = self.public_rsa_with_newlines
        response = form.submit()

        self.assertFormError(
            response,
            'form',
            'key',
            errors=self.error_messages['unknown_key'],
        )

    def test_error_when_only_header_of_private_rsa_is_given(self):
        response = self.app.get(ACCOUNT_SSH_KEYS_URL, user=self.user)

        form = response.forms[SSH_KEY_FORM_ID]
        form['key'] = '-----BEGIN RSA PRIVATE KEY-----'
        response = form.submit()

        self.assertFormError(
            response,
            'form',
            'key',
            errors=self.error_messages['unknown_key'],
        )


ACCOUNT_SSH_KEY_DELETE_URL = '/account/keys/{}/delete/'
SSH_KEY_DELETE_FORM_ID = 'account-ssh-key-delete-form'


class AccountSSHKeyDeleteTest(WebTest, ViewTestMixin):

    def setUp(self):
        self.user = mixer.blend('joltem.user')
        self.ssh_key = mixer.blend('git.authentication',
                                   user=self.user, name='key666')

        self.delete_url = ACCOUNT_SSH_KEY_DELETE_URL.format(self.ssh_key.pk)

    def test_redirect_to_login_page_when_user_is_not_logged_in(self):
        response = self.app.get(self.delete_url)

        self._test_sign_in_redirect_url(response, self.delete_url)

    def test_user_can_delete_only_his_keys(self):
        stranger = mixer.blend('joltem.user')
        self.app.get(self.delete_url, user=stranger, status=404)

    def test_user_successfully_deleted_ssh_key(self):
        response = self.app.get(self.delete_url, user=self.user)

        self.assertContains(response, 'key666')

        form = response.forms[SSH_KEY_DELETE_FORM_ID]
        response = form.submit()

        self.assertRedirects(response, ACCOUNT_SSH_KEYS_URL)

        self.assertFalse(
            Authentication.objects.filter(name='key666').exists()
        )


class AuthomaticTest(TestCase):

    def test_authomatic_url(self):
        response = self.client.get('/account/sign-in/fb/')
        self.assertEqual(response.status_code, '302 Found')
        self.assertTrue(response['Location'].startswith(
            'https://www.facebook.com/dialog/oauth'))

        response = self.client.get('/account/sign-in/gt/', data=dict(
            error='redirect_uri_mismatch',
            state='66ca2ed63c29abd63057a9fe9e',
        ), follow=True)
        m = list(response.context['messages']).pop()
        self.assertEqual(m.message, 'Unknow error. Please try another time.')

        response = self.client.get('/account/sign-in/gt/', data=dict(
            code='39b1d9b271b96044a027',
            state='5466603fb1a07c8c0948cb189a',
        ))
        self.assertRedirects(response, '/account/sign-in/')
