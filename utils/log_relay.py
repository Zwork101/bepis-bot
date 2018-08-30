from utils.common import LOG_CHANNEL

from gevent import sleep


def relayer(client, log_stream):
    curr_place = log_stream.tell()

    while True:
        log_stream.seek(curr_place)
        logs = log_stream.read()
        curr_place = log_stream.tell()

        if logs.strip():
            client.api.channels_messages_create(
                LOG_CHANNEL,
                logs
            )
            print(logs)

        sleep(.02)
