import builtins
import itertools
import os
import sys
import traceback
from functools import wraps, partial
from typing import Optional, IO, Callable

import click
from click.exceptions import ClickException

CONTEXT_SETTINGS = dict(
    help_option_names=['-h', '--help']
)


class ClickWarningException(ClickException):
    """
    Custom exception class for displaying warnings in yellow color.

    :param message: The error message.
    :type message: str
    """

    def show(self, file: Optional[IO] = None) -> None:
        """
        Display the warning message in yellow.

        :param file: File to write the output to.
        :type file: Optional[IO]
        """
        click.secho(self.format_message(), fg='yellow', file=sys.stderr)


class ClickErrorException(ClickException):
    """
    Custom exception class for displaying errors in red color.

    :param message: The error message.
    :type message: str
    """

    def show(self, file: Optional[IO] = None) -> None:
        """
        Display the error message in red.

        :param file: File to write the output to.
        :type file: Optional[IO]
        """
        click.secho(self.format_message(), fg='red', file=sys.stderr)


def print_exception(err: BaseException, print: Optional[Callable] = None):
    """
    Print exception information, including traceback.

    :param err: The exception object.
    :type err: BaseException
    :param print: Custom print function. If not provided, uses built-in print.
    :type print: Optional[Callable]
    """
    print = print or builtins.print

    lines = list(itertools.chain(*map(
        lambda x: x.splitlines(keepends=False),
        traceback.format_tb(err.__traceback__)
    )))

    if lines:
        print('Traceback (most recent call last):')
        print(os.linesep.join(lines))

    if len(err.args) == 0:
        print(f'{type(err).__name__}')
    elif len(err.args) == 1:
        print(f'{type(err).__name__}: {err.args[0]}')
    else:
        print(f'{type(err).__name__}: {err.args}')


class KeyboardInterrupted(ClickWarningException):
    """
    Exception class for handling keyboard interruptions.

    :param msg: Custom message to display.
    :type msg: Optional[str]
    """
    exit_code = 0x7

    def __init__(self, msg=None):
        """
        Initialize the exception.

        :param msg: Custom message to display.
        :type msg: Optional[str]
        """
        ClickWarningException.__init__(self, msg or 'Interrupted.')


def command_wrap():
    """
    Decorator for wrapping Click commands.

    This decorator catches exceptions and provides consistent error handling.

    :return: Decorator function.
    :rtype: Callable
    """

    def _decorator(func):
        @wraps(func)
        def _new_func(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except ClickException:
                raise
            except KeyboardInterrupt:
                raise KeyboardInterrupted
            except BaseException as err:
                click.secho('Unexpected error found when running hfutils!', fg='red', file=sys.stderr)
                print_exception(err, partial(click.secho, fg='red', file=sys.stderr))
                sys.exit(0x1)

        return _new_func

    return _decorator
