#!/usr/bin/env python3.8

import argparse
import asyncio
import logging
import logging.config
import logging.handlers
import sys
from .client import run
from .server import serve

def log_destination(s):
    if s in ('syslog', 'stderr'):
        return s
    elif s.startswith('file:') and len(s) > 5:
        return s
    else:
        raise argparse.ArgumentTypeError(f'{s} is not a valid logging destination')

def parse_arguments():
    parser = argparse.ArgumentParser()

    parser.add_argument('-v', '--verbose', action='count', help='Enable verbose output; repeat for increased verbosity')
    parser.add_argument('--log-dest', metavar='DEST', type=log_destination, help='Set the destination for verbose output; valid values are stderr or file:FILENAME')
    parser.add_argument('--log-config', metavar='FILE', action='store', help='Configure the logging system from a file')

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

def configure_logging(args):
    if args.log_config:
        logging.fileConfig(args.log_config)
        return

    basic_config_parameters = {}
    if args.verbose == 1:
        basic_config_parameters['level'] = logging.WARNING
    elif args.verbose == 2:
        basic_config_parameters['level'] = logging.INFO
    elif args.verbose == 3:
        basic_config_parameters['level'] = logging.DEBUG
    if args.log_dest == 'stderr':
        basic_config_parameters['handlers'] = [logging.StreamHandler()]
    elif args.log_dest and args.log_dest.startswith('file:'):
        basic_config_parameters['handlers'] = [logging.FileHandler(args.log_dest[5:])]
    logging.basicConfig(**basic_config_parameters)

def main():
    args = parse_arguments()
    configure_logging(args)
    if args.subcommand == 'serve':
        try:
            asyncio.run(serve(args.host, args.port))
        except KeyboardInterrupt:
            pass # TODO wait for processes
    elif args.subcommand == 'run':
        try:
            exit_code = asyncio.run(run(args.host, args.port, args.command, *args.arguments))
            if exit_code is None:
                sys.exit(125)
            else:
                sys.exit(exit_code)
        except KeyboardInterrupt:
            sys.exit(130)
    else:
        assert(False) # argparse should have caught this

if __name__ == '__main__':
    main()
