#!/usr/bin/env python3.8

import argparse
import asyncio
import logging
from .client import run
from .server import serve

def parse_arguments():
    parser = argparse.ArgumentParser()

    subparsers = parser.add_subparsers(required=True, dest='subcommand', title='subcommands')

    serve_parser = subparsers.add_parser('serve', help='Start the server')
    serve_parser.add_argument('--host', action='store', default='localhost', help='Hostname or IP address on which to run the server')
    serve_parser.add_argument('-p', '--port', action='store', type=int, default=13180, help='Port on which to run the server') # this port should be used in the RemoteForward SSH directive (see ~/.ssh/config)

    run_parser = subparsers.add_parser('run', help='Run a command on the remote host')
    run_parser.add_argument('--host', action='store', default='localhost', help='Hostname or IP address to connect to')
    run_parser.add_argument('-p', '--port', action='store', type=int, default=13180, help='Port to connect to')
    run_parser.add_argument('command', help='Command to run')
    run_parser.add_argument('arguments', nargs=argparse.REMAINDER, help='Arguments for the command')

    return parser.parse_args()

def main():
    args = parse_arguments()
    logging.basicConfig(level=logging.INFO)
    logging.getLogger('run_remote.client').setLevel(logging.ERROR)
    if args.subcommand == 'serve':
        coroutine = serve(args.host, args.port)
    elif args.subcommand == 'run':
        coroutine = run(args.host, args.port, args.command, *args.arguments)
    else:
        assert(False) # argparse should have caught this
    try:
        asyncio.run(coroutine)
    except KeyboardInterrupt:
        pass # TODO wait for processes

if __name__ == '__main__':
    main()
