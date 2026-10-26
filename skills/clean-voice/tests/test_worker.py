import sys
import tempfile
import types
import unittest
from argparse import Namespace
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from clean_voice.worker import download


class DownloadWorkerTests(unittest.TestCase):
    def test_playlist_is_rejected_before_any_download_request(self):
        requests = []

        class Downloader:
            def __init__(self, settings):
                self.settings = settings

            def __enter__(self):
                return self

            def __exit__(self, *arguments):
                return False

            def extract_info(self, address, download):
                requests.append(download)
                return {"_type": "playlist", "entries": []}

        with tempfile.TemporaryDirectory() as temporary:
            options = Namespace(output=Path(temporary) / "result.json", input="https://example.org/playlist", cookies=None)
            with patch.dict(sys.modules, {"yt_dlp": types.SimpleNamespace(YoutubeDL=Downloader)}):
                with self.assertRaises(ValueError):
                    download(options)
            self.assertEqual(requests, [False])


if __name__ == "__main__":
    unittest.main()
