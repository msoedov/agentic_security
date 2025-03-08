from pyfiglet import Figlet, FontNotFound
from termcolor import colored

try:
    from importlib.metadata import version
except ImportError:
    from importlib_metadata import version


def generate_banner(
    title="Agentic Security",
    font="slant",
    version="v2.1.0",
    tagline="Proactive Threat Detection & Automated Security Protocols",
    author="Developed by: [Security Team]",
    website="Website: https://github.com/msoedov/agentic_security",
    warning="",
):
    """Generate a visually enhanced banner with dynamic width and borders."""
    # Define the text elements

    # Initialize Figlet with the specified font, fallback to default if not found
    try:
        f = Figlet(font=font)
    except FontNotFound:
        f = Figlet()  # Fallback to default font

    # Render the title text and calculate the maximum width of Figlet lines
    banner_text = f.renderText(title)
    banner_lines = banner_text.splitlines()
    figlet_max_width = max(len(line) for line in banner_lines) if banner_lines else 0

    # Create the details line and calculate its width
    details_line = f"Version: {version} | {website}"
    details_width = len(details_line)

    # Calculate widths of other text elements
    warning_width = len(warning)
    tagline_width = len(tagline)

    # Determine the overall maximum width for centering
    overall_max_width = max(
        figlet_max_width, warning_width, tagline_width, details_width
    )

    # Pad the Figlet lines to the overall maximum width
    padded_banner_lines = [line.center(overall_max_width) for line in banner_lines]

    # Define decorative characters and colors
    decor_chars = ["▄", "■", "►"]
    decor_colors = ["blue", "red", "yellow"]

    # Create and color the content lines
    content_lines = []
    for line in padded_banner_lines:
        content_lines.append(colored(line, "blue"))
    content_lines.append(colored(decor_chars[0] * overall_max_width, decor_colors[0]))
    content_lines.append(
        colored(warning.center(overall_max_width), "red", attrs=["blink", "bold"])
    )
    content_lines.append(colored(decor_chars[1] * overall_max_width, decor_colors[1]))
    content_lines.append(colored(tagline.center(overall_max_width), "red"))
    content_lines.append(colored(decor_chars[2] * overall_max_width, decor_colors[2]))
    content_lines.append(colored(details_line.center(overall_max_width), "magenta"))

    # Define border color and create top and bottom borders
    border_color = "blue"
    top_border = colored("╔" + "═" * (overall_max_width + 2) + "╗", border_color)
    bottom_border = colored("╚" + "═" * (overall_max_width + 2) + "╝", border_color)

    # Add side borders to each content line with padding
    bordered_content = [
        colored("║ ", border_color) + line + colored(" ║", border_color)
        for line in content_lines
    ]

    # Assemble the full banner
    banner = top_border + "\n" + "\n".join(bordered_content) + "\n" + bottom_border
    return banner


def init_banner():
    return
    ver = version("agentic_security")
    try:
        print(generate_banner(version=ver))
    except Exception:
        # UnicodeEncodeError with codec on some systems
        pass


if __name__ == "__main__":
    init_banner()
