def get_all_possible_lean_chars():
    ranges = [
        # Basic Latin + Latin-1 Supplement + Latin Extended
        (0x0020, 0x024F),  # Basic symbols, letters, extended Latin
        # IPA Extensions + Spacing Modifiers
        (0x0250, 0x02AF),  # Phonetic symbols
        # Combining Diacritical Marks
        (0x0300, 0x036F),
        # Greek and Coptic + Greek Extended
        (0x0370, 0x03FF),  # Greek letters
        (0x1F00, 0x1FFF),  # Greek extended
        # Cyrillic (some papers use these)
        (0x0400, 0x04FF),
        # Mathematical Alphanumeric Symbols (ALL)
        (0x1D400, 0x1D7FF),  # Includes bold, italic, script, etc.
        # General Punctuation
        (0x2000, 0x206F),  # Various spaces and punctuation
        # Superscripts and Subscripts (ALL)
        (0x2070, 0x209F),
        # Currency Symbols
        (0x20A0, 0x20CF),
        # Combining Diacritical Marks for Symbols
        (0x20D0, 0x20FF),
        # Letterlike Symbols (ALL)
        (0x2100, 0x214F),  # ℕ, ℤ, ℚ, ℝ, ℂ, etc.
        # Number Forms
        (0x2150, 0x218F),
        # Arrows (ALL categories)
        (0x2190, 0x21FF),  # Arrows
        (0x27F0, 0x27FF),  # Supplemental Arrows-A
        (0x2900, 0x297F),  # Supplemental Arrows-B
        (0x2B00, 0x2B4F),  # Additional Arrows
        # Mathematical Operators (ALL)
        (0x2200, 0x22FF),  # Basic Mathematical Operators
        # Miscellaneous Technical
        (0x2300, 0x23FF),
        # Control Pictures
        (0x2400, 0x243F),
        # Optical Character Recognition
        (0x2440, 0x245F),
        # Enclosed Alphanumerics
        (0x2460, 0x24FF),
        # Box Drawing + Block Elements + Geometric Shapes
        (0x2500, 0x25FF),
        # Miscellaneous Symbols
        (0x2600, 0x26FF),
        # Dingbats
        (0x2700, 0x27BF),
        # Miscellaneous Mathematical Symbols-A
        (0x27C0, 0x27EF),
        # Miscellaneous Mathematical Symbols-B
        (0x2980, 0x29FF),
        # Supplemental Mathematical Operators
        (0x2A00, 0x2AFF),
        # Miscellaneous Symbols and Arrows
        (0x2B00, 0x2BFF),
        # Supplemental Punctuation
        (0x2E00, 0x2E7F),
        # CJK Symbols and Punctuation
        (0x3000, 0x303F),
        # Additional ranges for completeness
        (0x1EE00, 0x1EEFF),  # Arabic Mathematical Alphabetic Symbols
        # Supplemental Mathematical Operators
        (0x2B30, 0x2B4F),
        # Mathematical Alphanumeric Symbols
        (0x1D400, 0x1D7FF),
    ]

    # Generate the set of all characters in these ranges
    chars = set()
    for start, end in ranges:
        chars.update(chr(i) for i in range(start, end + 1) if chr(i).isprintable())

    return chars


if __name__ == "__main__":
    # Example usage
    all_possible_chars = get_all_possible_lean_chars()
    print(f"Total characters: {len(all_possible_chars)}")
    for c in all_possible_chars:
        print(c, end=" ")
