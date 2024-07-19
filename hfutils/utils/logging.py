"""
Overview:
    This module provides functionality to enhance logging output with colors for different log levels.
    It includes a `Colors` class defining ANSI escape sequences for various colors and styles,
    and a `ColoredFormatter` class to format log messages with these colors based on their severity level.
"""

import logging


class Colors:
    """
    A collection of ANSI escape sequences for terminal text coloring and styling.
    These constants can be used to format strings with various colors and text styles.
    """
    RESET = "\033[0m"
    BOLD = "\033[1m"
    UNDERLINE = "\033[4m"
    BLACK = "\033[30m"
    RED = "\033[31m"
    GREEN = "\033[32m"
    YELLOW = "\033[33m"
    BLUE = "\033[34m"
    MAGENTA = "\033[35m"
    CYAN = "\033[36m"
    WHITE = "\033[37m"
    BRIGHT_BLACK = "\033[90m"
    BRIGHT_RED = "\033[91m"
    BRIGHT_GREEN = "\033[92m"
    BRIGHT_YELLOW = "\033[93m"
    BRIGHT_BLUE = "\033[94m"
    BRIGHT_MAGENTA = "\033[95m"
    BRIGHT_CYAN = "\033[96m"
    BRIGHT_WHITE = "\033[97m"


class ColoredFormatter(logging.Formatter):
    """
    A logging formatter that applies colors to log messages based on their severity level.

    The colors are defined in the `Colors` class and are applied to different parts of the log message
    such as the timestamp, log level, logger name, and the message itself.
    """
    COLORS = {
        'DEBUG': Colors.BLUE,
        'INFO': Colors.GREEN,
        'WARNING': Colors.YELLOW,
        'ERROR': Colors.RED,
        'CRITICAL': Colors.BOLD + Colors.RED,
    }

    def format(self, record):
        """
        Format the specified record as text, applying color based on the log level.

        :param record: The log record to be formatted.
        :type record: logging.LogRecord

        :return: The formatted log message with appropriate colors.
        :rtype: str
        """
        log_color = self.COLORS.get(record.levelname, Colors.RESET)
        format_str = f"{Colors.BRIGHT_BLACK}[%(asctime)s]{Colors.RESET} "
        format_str += f"{log_color}%(levelname)-8s{Colors.RESET} "
        format_str += f"{Colors.CYAN}%(name)s{Colors.RESET} - "
        format_str += f"%(message)s"

        formatter = logging.Formatter(format_str, datefmt="%Y-%m-%d %H:%M:%S")
        return formatter.format(record)
