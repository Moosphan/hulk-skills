import math
import re
import unicodedata


def parse_time(value):
    parts = str(value).strip().split(":")
    if not 1 <= len(parts) <= 3 or any(not re.fullmatch(r"\d+(?:\.\d+)?", part) for part in parts):
        raise ValueError(f"Invalid time: {value!r}; use seconds, MM:SS or HH:MM:SS")
    numbers = [float(part) for part in parts]
    if any(not math.isfinite(number) for number in numbers):
        raise ValueError("Time must be finite")
    if len(numbers) > 1 and any(number >= 60 for number in numbers[1:]):
        raise ValueError("Minutes/seconds after a colon must be below 60")
    return sum(number * 60 ** index for index, number in enumerate(reversed(numbers)))


def merge_ranges(ranges):
    result = []
    for start, end in sorted(ranges):
        if not all(math.isfinite(value) for value in [start, end]) or start < 0 or end <= start:
            raise ValueError(f"Invalid range: {start}-{end}")
        if result and start <= result[-1][1] + 1e-9:
            result[-1] = (result[-1][0], max(result[-1][1], end))
        else:
            result.append((start, end))
    return result


def parse_range(value, duration):
    parts = value.split("-")
    if len(parts) != 2:
        raise ValueError(f"Invalid range: {value!r}; use START-END")
    start = parse_time(parts[0])
    end = duration if parts[1].strip().lower() == "end" else parse_time(parts[1])
    if start >= end or end > duration + 1e-6:
        raise ValueError(f"Range {value!r} falls outside the {duration:.3f}s source")
    return start, min(end, duration)


def subtract_ranges(kept, removed):
    result = list(kept)
    for remove_start, remove_end in merge_ranges(removed):
        remaining = []
        for start, end in result:
            if remove_end <= start or remove_start >= end:
                remaining.append((start, end))
            else:
                if start < remove_start:
                    remaining.append((start, remove_start))
                if remove_end < end:
                    remaining.append((remove_end, end))
        result = remaining
    if not result:
        raise ValueError("The edit removes all audio")
    return result


def select_ranges(duration, keep, remove):
    if not math.isfinite(duration) or duration <= 0:
        raise ValueError("Source duration must be positive and finite")
    kept = merge_ranges([parse_range(value, duration) for value in keep]) if keep else [(0, duration)]
    removed = [parse_range(value, duration) for value in remove]
    return subtract_ranges(kept, removed)


def intersect_ranges(first, second):
    result = [(max(start, other_start), min(end, other_end))
              for start, end in first for other_start, other_end in second
              if max(start, other_start) < min(end, other_end)]
    if not result:
        raise ValueError("No audio remains after intersecting edits")
    return merge_ranges(result)


def speech_ranges(duration, silences, padding):
    if not math.isfinite(padding) or padding < 0:
        raise ValueError("Silence padding must be nonnegative and finite")
    removed = []
    for start, end in silences:
        if start <= 0 and end >= duration:
            raise ValueError("The entire source is silent")
        cut_start = start if start <= 0 else start + padding
        cut_end = end if end >= duration else end - padding
        if cut_end > cut_start:
            removed.append((cut_start, cut_end))
    return subtract_ranges([(0, duration)], removed)


def normalize_text(value):
    return "".join(character for character in unicodedata.normalize("NFKC", value).casefold() if character.isalnum())


def phrase_range(words, phrase, occurrence=None, padding=0):
    if not math.isfinite(padding) or padding < 0:
        raise ValueError("Phrase padding must be nonnegative and finite")
    query = normalize_text(phrase)
    if not query:
        raise ValueError("A phrase must contain letters or numbers")
    characters = []
    timing = []
    for word in words:
        start, end = float(word["start"]), float(word["end"])
        if not math.isfinite(start) or not math.isfinite(end) or start < 0 or end <= start:
            raise ValueError("Transcript contains invalid word timestamps")
        normalized = normalize_text(word.get("word", word.get("text", "")))
        characters.extend(normalized)
        timing.extend([(start, end)] * len(normalized))
    text = "".join(characters)
    positions = []
    cursor = 0
    while True:
        position = text.find(query, cursor)
        if position < 0:
            break
        positions.append(position)
        cursor = position + len(query)
    if not positions:
        raise ValueError(f"Phrase not found in transcript: {phrase!r}")
    if occurrence is None and len(positions) > 1:
        raise ValueError(f"Phrase appears {len(positions)} times; specify --occurrence or use explicit ranges")
    selected = 1 if occurrence is None else occurrence
    if not 1 <= selected <= len(positions):
        raise ValueError("Requested phrase occurrence does not exist")
    position = positions[selected - 1]
    return max(0, timing[position][0] - padding), timing[position + len(query) - 1][1] + padding
