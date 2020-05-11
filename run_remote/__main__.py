#!/usr/bin/env python3.8

import argparse
import asyncio
import logging
import logging.config
import logging.handlers
import sys
import tomlkit

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
    parser.add_argument('--config', metavar='FILE', action='store', help='Read configuration from a file')
    parser.add_argument('--log-dest', metavar='DEST', type=log_destination, help='Set the destination for verbose output; valid values are stderr or file:FILENAME')

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

def load_configuration(filename):
    if not filename:
        return {}
    with open(filename) as f:
        return tomlkit.parse(f.read())

def configure_logging(configuration, verbosity=None, log_dest=None):
    if 'logging' in configuration:
        logging.config.dictConfig(configuration['logging'])

    basic_config_parameters = {}
    if verbosity == 1:
        basic_config_parameters['level'] = logging.WARNING
    elif verbosity == 2:
        basic_config_parameters['level'] = logging.INFO
    elif verbosity == 3:
        basic_config_parameters['level'] = logging.DEBUG
    if log_dest == 'stderr':
        basic_config_parameters['handlers'] = [logging.StreamHandler()]
    elif log_dest and log_dest.startswith('file:'):
        basic_config_parameters['handlers'] = [logging.FileHandler(log_dest[5:])]
    if basic_config_parameters:
        root_logger = logging.getLogger()
        if root_logger.hasHandlers():
            root_logger.warning('Replacing configured handlers for root logger')
            basic_config_parameters['force'] = True
        logging.basicConfig(**basic_config_parameters)

def construct_command_sanitizer(configuration):
    import importlib
    import run_remote.command
    logger = logging.getLogger('run_remote.command')
    sanitizer_config = configuration.get('command', {}).get('sanitizer', {})
    if 'class' not in sanitizer_config:
        logger.info('No sanitizer class found in configuration')
        return run_remote.command.default_sanitizer
    module_name, _, name = sanitizer_config['class'].rpartition('.')
    if module_name:
        try:
            module = importlib.import_module(module_name)
        except ImportError:
            logger.exception(f'Import of sanitizer module {module_name} failed')
            return None
        else:
            logger.debug(f'Using {module_name} as sanitizer module')
    else:
        module = run_remote.command
        logger.debug('Using run_remote.command as sanitizer module')
    try:
        sanitizer_class = getattr(module, name)
    except AttributeError:
        logger.exception(f'Sanitizer {name} not found in module {module_name}')
        return None
    try:
        return sanitizer_class(**{k: v for k, v in sanitizer_config.items() if k != 'class'})
    except:
        logger.exception(f'Unable to initialize sanitizer from class {sanitizer_class!r}')
        return None

def main():
    args = parse_arguments()
    configuration = load_configuration(args.config)
    configure_logging(configuration, args.verbose, args.log_dest)
    if args.subcommand == 'serve':
        from run_remote.server import Server
        sanitizer = construct_command_sanitizer(configuration)
        if sanitizer is None:
            sys.exit(1)
        s = Server(args.host, args.port, sanitizer)
        try:
            asyncio.run(s.serve())
        except KeyboardInterrupt:
            pass # TODO wait for processes
    elif args.subcommand == 'run':
        from run_remote.client import Client
        c = Client(args.host, args.port)
        try:
            exit_code = asyncio.run(c.run(args.command, *args.arguments))
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
