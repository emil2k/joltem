""" Models related to Gateway app. """

from new_relic.models import NewRelicTransferEvent


class GitUploadPackEvent(NewRelicTransferEvent):

    """ Records git-upload-pack events. """


class GitReceivePackEvent(NewRelicTransferEvent):

    """ Records git-receive-pack events. """
