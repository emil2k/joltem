# coding: utf-8
from django_webtest import WebTest
from joltem.models import User
from common.mix import mixer


MAIN_PAGE_URL = '/'
SIGN_UP_URL = '/account/sign-up/'
SIGN_UP_FORM_ID = 'sign-up-form'


class SignUpTest(WebTest):

    def setUp(self):
        # We need at least one project.
        mixer.blend('project')

    def test_redirect_to_main_page_when_user_is_logged_in(self):
        user = mixer.blend('user')

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

    def test_user_has_profile_after_registration(self):
        response = self.app.get(SIGN_UP_URL)

        form = response.forms[SIGN_UP_FORM_ID]
        form['username'] = 'bob'
        form['first_name'] = 'Bob'
        form['email'] = 'bob@example.com'
        form['gravatar_email'] = 'rob@example.com'
        form['password1'] = '123'
        form['password2'] = '123'
        response = form.submit()

        user = User.objects.get(username='bob')
        self.assertTrue(user.gravatar_email, 'rob@example.com')


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
