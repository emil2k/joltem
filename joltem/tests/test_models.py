from django.test import TestCase
from joltem.libs import mixer


class UserModelTest(TestCase):

    def setUp(self):
        self.user = mixer.blend('joltem.user')

    def test_gravatar(self):
        """ Test gravatar property.

        When setting you should pass and email, when getting it should give
        the image source.

        """
        self.user.gravatar = 'emil2k@gmail.com'
        self.assertEqual(self.user.gravatar_email, 'emil2k@gmail.com')
        self.assertEqual(self.user.gravatar_hash,
                         '0e3616fa71abd6c30910910d4d439470')
        self.assertEqual(self.user.gravatar,
                         'https://secure.gravatar.com/avatar/0e3616fa71abd6c30910910d4d439470')  # noqa
