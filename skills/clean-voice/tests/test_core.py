import importlib
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))


class EditingTests(unittest.TestCase):
    def core(self):
        self.assertTrue((ROOT / "clean_voice/core.py").is_file(), "editing core must exist")
        return importlib.import_module("clean_voice.core")

    def test_timestamp_formats(self):
        core = self.core()
        self.assertEqual(core.parse_time("01:02.5"), 62.5)
        self.assertEqual(core.parse_time("1:02:03"), 3723)
        self.assertEqual(core.parse_time("2.25"), 2.25)

    def test_invalid_timestamps(self):
        core = self.core()
        for value in ["nan", "inf", "-1", "1:60", "1:2:99", "", "1:2:3:4"]:
            with self.subTest(value=value), self.assertRaises(ValueError):
                core.parse_time(value)

    def test_union_and_subtraction_use_source_timeline(self):
        core = self.core()
        self.assertEqual(core.select_ranges(30, ["0-10", "8-20"], ["4-6", "15-18"]), [(0, 4), (6, 15), (18, 20)])

    def test_end_keyword(self):
        self.assertEqual(self.core().select_ranges(12.5, ["10-end"], []), [(10, 12.5)])

    def test_reject_empty_or_outside_edits(self):
        core = self.core()
        for keep, remove in [(["5-3"], []), (["0-31"], []), ([], ["0-end"]), (["nan-2"], [])]:
            with self.subTest(keep=keep, remove=remove), self.assertRaises(ValueError):
                core.select_ranges(30, keep, remove)

    def test_silence_padding_preserves_speech_boundaries(self):
        core = self.core()
        self.assertEqual(core.speech_ranges(10, [(0, 1), (3, 5), (9, 10)], 0.2), [(0.8, 3.2), (4.8, 9.2)])

    def test_full_silence_is_not_exported_as_success(self):
        with self.assertRaises(ValueError):
            self.core().speech_ranges(10, [(0, 10)], 0.1)

    def test_phrase_matches_across_chinese_word_boundaries(self):
        words = [{"word": "你好，", "start": 1, "end": 2}, {"word": "世界。", "start": 2, "end": 3}]
        self.assertEqual(self.core().phrase_range(words, "你好世界", None, 0), (1, 3))

    def test_repeated_phrase_requires_disambiguation(self):
        core = self.core()
        words = [{"word": "你好", "start": 1, "end": 2}, {"word": "你好", "start": 4, "end": 5}]
        with self.assertRaises(ValueError):
            core.phrase_range(words, "你好", None, 0)
        self.assertEqual(core.phrase_range(words, "你好", 2, 0), (4, 5))

    def test_missing_phrase_and_invalid_word_times_fail(self):
        core = self.core()
        with self.assertRaises(ValueError):
            core.phrase_range([{"word": "你好", "start": 1, "end": 2}], "再见", None, 0)
        with self.assertRaises(ValueError):
            core.phrase_range([{"word": "你好", "start": 3, "end": 2}], "你好", None, 0)

    def test_range_intersection(self):
        self.assertEqual(self.core().intersect_ranges([(0, 5), (8, 10)], [(2, 9)]), [(2, 5), (8, 9)])


if __name__ == "__main__":
    unittest.main()
