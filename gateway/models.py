""" Models related to Gateway app. """

from new_relic.models import NewRelicTransferEvent, NewRelicReport


class GitUploadPackEvent(NewRelicTransferEvent):

    """ Records git-upload-pack events. """

    metric_name_transfer_type = "Upload"


class GitReceivePackEvent(NewRelicTransferEvent):

    """ Records git-receive-pack events. """

    metric_name_transfer_type = "Receive"


class GitReport(NewRelicReport):

    """ Compiles and keeps track of New Relic reports. """

    component_guid = 'com.joltem.git'
    event_classes = (GitUploadPackEvent, GitReceivePackEvent)
