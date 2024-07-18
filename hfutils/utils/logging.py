import logging


class Colors:
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
    COLORS = {
        'DEBUG': Colors.BLUE,
        'INFO': Colors.GREEN,
        'WARNING': Colors.YELLOW,
        'ERROR': Colors.RED,
        'CRITICAL': Colors.BOLD + Colors.RED,
    }

    def format(self, record):
        log_color = self.COLORS.get(record.levelname, Colors.RESET)
        format_str = f"{Colors.BRIGHT_BLACK}[%(asctime)s]{Colors.RESET} "
        format_str += f"{log_color}%(levelname)-8s{Colors.RESET} "
        format_str += f"{Colors.CYAN}%(name)s{Colors.RESET} - "
        format_str += f"{Colors.WHITE}%(message)s{Colors.RESET}"

        formatter = logging.Formatter(format_str, datefmt="%Y-%m-%d %H:%M:%S")
        return formatter.format(record)
