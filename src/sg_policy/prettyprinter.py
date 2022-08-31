class TermStyle:
    PURE_RED = "\033[0;31m"
    DARK_GREEN = "\033[0;32m"
    ORANGE = "\033[0;33m"
    DARK_BLUE = "\033[0;34m"
    BRIGHT_PURPLE = "\033[0;35m"
    DARK_CYAN = "\033[0;36m"
    DULL_WHITE = "\033[0;37m"
    PURE_BLACK = "\033[0;30m"
    BRIGHT_RED = "\033[0;91m"
    LIGHT_GREEN = "\033[0;92m"
    YELLOW = "\033[0;93m"
    BRIGHT_BLUE = "\033[0;94m"
    MAGENTA = "\033[0;95m"
    LIGHT_CYAN = "\033[0;96m"
    BRIGHT_BLACK = "\033[0;90m"
    BRIGHT_WHITE = "\033[0;97m"
    CYAN_BACK = "\033[0;46m"
    PURPLE_BACK = "\033[0;45m"
    WHITE_BACK = "\033[0;47m"
    BLUE_BACK = "\033[0;44m"
    ORANGE_BACK = "\033[0;43m"
    GREEN_BACK = "\033[0;42m"
    PINK_BACK = "\033[0;41m"
    GREY_BACK = "\033[0;40m"
    GREY = "\033[38;4;236m"
    BOLD = "\033[1m"
    UNDERLINE = "\033[4m"
    ITALIC = "\033[3m"
    DARKEN = "\033[2m"
    INVISIBLE = "\033[08m"
    REVERSE_COLOUR = "\033[07m"
    RESET_COLOUR = "\033[0m"
    GREY = "\x1b[90m"

    @staticmethod
    def str_with_style(message: str, color: str) -> str:
        return f"{color}{message}{TermStyle.RESET_COLOUR}"

    @staticmethod
    def success(message: str) -> str:
        return TermStyle.str_with_style(message, TermStyle.LIGHT_GREEN + TermStyle.BOLD)

    @staticmethod
    def fail(message: str) -> str:
        return TermStyle.str_with_style(message, TermStyle.BRIGHT_RED + TermStyle.BOLD)

    @staticmethod
    def warning(message: str) -> str:
        return TermStyle.str_with_style(message, TermStyle.YELLOW + TermStyle.BOLD)


# TODO: Add method to pretty print table, ask someone to show the policy table in stackguardian
# also I still can't get a JSON output right now because the sample test input is failing when used as an input
