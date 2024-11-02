import re

""" returns the width of a character in axes coordinates """
def get_char_width(fig,ax,fontsize,args):
    r = fig.canvas.get_renderer()
    t = ax.text(0.5, 0.5, 'x', fontsize=fontsize,**args)
    
    bb = t.get_window_extent(renderer=r).transformed(ax.transData.inverted())
    width = bb.width
    height = bb.height
    t.remove()
    return width

""" wraps English/Chinese mixed text """
def textwrap_mixed(text:str, width:int)->list[str]:
    def is_chinese(char):
        """ Check if a character is a Chinese character """
        return '\u4e00' <= char <= '\u9fff'
    
    def measure_char_width(char):
        """ Measure the width of a character: Chinese characters are 2 units, others are 1 unit """
        if is_chinese(char):
            return 2
        else:
            return 1

    def wrap_line(current_line, word, current_length, width):
        """ Try to fit the word into the current line, break with '-' if necessary """
        word_len = sum(measure_char_width(c) for c in word)
        if current_length + word_len > width:  # Word doesn't fit, break it up
            break_idx = width - current_length - 1  # Leave space for '-'
            return current_line + word[:break_idx] + '-', word[break_idx:], 0
        else:  # Word fits, no need to break
            return current_line + word, '', current_length + word_len

    # Split the text into words and Chinese characters, retaining punctuation
    width = int(width)
    tokens = re.findall(r'[\u4e00-\u9fff]|[a-zA-Z]+|[^a-zA-Z\u4e00-\u9fff\s]+|\s', text)

    lines = []
    current_line = ''
    current_length = 0

    for token in tokens:
        token_len = sum(measure_char_width(c) for c in token)

        # Handle breaking the line when Chinese characters fit individually
        if is_chinese(token):
            if current_length + token_len > width:
                # If token doesn't fit, push current line to output and start a new line
                lines.append(current_line)
                current_line = token
                current_length = token_len
            else:
                current_line += token
                current_length += token_len

        # Handle English words and punctuation
        else:
            if current_length + token_len > width:  # If token doesn't fit in the current line
                # If it's a word (no whitespace), handle word wrapping with a hyphen
                if re.match(r'[a-zA-Z]+', token):
                    wrapped, remainder, current_length = wrap_line(current_line, token, current_length, width)
                    current_line = wrapped
                    lines.append(current_line.strip())
                    current_line = remainder
                    if remainder:
                        current_length = sum(measure_char_width(c) for c in remainder)
                else:
                    # If it's punctuation or other symbols, just break to a new line
                    lines.append(current_line.strip())
                    current_line = token
                    current_length = token_len
            else:
                current_line += token
                current_length += token_len

    # Add the last line if it's non-empty
    if current_line:
        lines.append(current_line)

    return lines


