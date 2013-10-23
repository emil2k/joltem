import struct

# Utility functions for parsing git protocol

FLUSH_PACKET_LINE = '0000'
STATUS_OK = 'ok'


def get_packet_line_size(raw, offset=0):
    """
    Parses the line size in bytes out of the git transfer protocol.
    The size of the line is represented in the first 4 bytes, returns and int in bytes

    """
    if len(raw) < 4:
        raise IOError("Packet line must be at least 4 bytes.")
    hexdigit = struct.unpack('4s', str(raw[offset:offset+4]))[0]
    return int(hexdigit, 16)


def get_packet_line(line):
    """
    Get packet line in the format, described in the git protocol

    """
    size = len(line) + 4
    if size > 65535:
        raise IOError("Packet line exceeds maximum size : %d bytes" % size)
    return '%04x%s' % (size, line)


# For reporting push status

def get_unpack_status(result=STATUS_OK):
    """
    Get the status unpack.

    It is better to leave this as `ok` most of the time and provide messages on each command status,
    to avoid a confusing error since where are

    """
    return "unpack %s\n" % result


def get_command_status(ref, status=STATUS_OK):
    """
    Get status for each individual reference push.

    Keyword arguments:
    ref -- reference that was being pushed.
    status -- the status of the command, either and error message or `ok`

    """
    if status != STATUS_OK:
        return "ng %s %s\n" % (ref, status)
    else:
        return "ok %s\n" % ref


def get_report(command_statuses, unpack_status='ok'):
    """
    Form a report to send back to the client with the status of the push.

    NOTE : This does not behave like the documented protocol for status reporting
    It seems like all the packet lines in the report are concatenated together preceded by a start of heading (\x01)
    into one packet line.

    Keyword arguments:
    command_statuses -- list of tuples representing each references push status, form (reference, error_message)
    unpack_status -- error message for the unpack status, defaults to 'ok'

    """
    report = '\x01' + get_packet_line(get_unpack_status(unpack_status))
    for ref, err_msg in command_statuses:
        if err_msg:
            report += get_packet_line(get_command_status(ref, err_msg))
        else:
            report += get_packet_line(get_command_status(ref))
    report += FLUSH_PACKET_LINE
    return get_packet_line(report)


