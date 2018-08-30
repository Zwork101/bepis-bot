import sys
from os import environ
# import logging
# import io

# from utils.log_relay import relayer

from disco.cli import disco_main
# from gevent import spawn


sys.argv.append("--token")
sys.argv.append(environ['TOKEN'])

# log_stream = io.StringIO()
# stream_handler = logging.FileHandler(log_stream)
# logging.basicConfig(stream=stream_handler)
#
client = disco_main()
#
# spawn(relayer, client, log_stream)

client.run_forever()
