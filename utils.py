
def translate_to_english(ru_text):
    text = str(ru_text).strip()
    if text == 'Монета':
        return "Coin"
    elif text== 'Долларов в уровне':
        return "dollars per level"
    elif text=="Оценка времени, которое понадобится для разъедания плотности, в минутах":
        return "Estimate of the time it will take to corrode the density, in minutes"
    elif text=="Цена":
        return "Price"
    elif text=="Монет в уровне":
        return "Coins per level"
    elif text=="До уровня, %":
        return "To Level %"
    else:
        return text

# function to convert K, M to their respective numeric values
def convert_units(val):
    lookup = {'K': 1000, 'M': 1e6}  # define desired replacements here
    unit = val[-1].upper()  # get the last character of the string i.e K or M
    if not unit.isdigit():
        val = float(val[:-1]) * lookup.get(unit, 1)
    return val

def format_telegram_message(rows):
    # Determine the maximum length of each column
    lengths = [max(len(str(value)) for value in column) for column in zip(*rows)]

    # Create a format string that pads each column to its max length
    format_string = ' '.join('{:<%d}' % length for length in lengths)

    # Quickly fix the percentage column to be right-aligned
    format_string = format_string.replace('{:<6} {:<1}','{:>6} {:<1}')

    # Use the format string to create the final message
    message = "```\n"  # pre-formatted fixed-width code block
    message += "\n".join(format_string.format(*row) for row in rows)
    message += "\n```"
    return message

def escape_md(text):
    """
    Escape special characters for telegram when using parse_mode MarkdownV2
    :param text: the text to send the message to Telegram
    :return: text with escaped characters
    """
    escape_chars = r'\*_\[\]()~`>#+-=|{}.!'
    return ''.join('\\'+char if char in escape_chars else char for char in text)