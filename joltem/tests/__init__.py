import logging
TEST_LOGGER = logging.getLogger('tests')


class TestCaseDebugMixin():
    """
    General mixin for adding formatting to set up and teardown output
    """

    def setUp(self):
        TEST_LOGGER.debug("\n\n///* SETUP : %s\n" % self.id())

    def tearDown(self):
        TEST_LOGGER.debug("\n\n*/// TEARDOWN\n")


# Load tests from submodules
from joltem.tests.loaders import *
from joltem.tests.notifications import *
