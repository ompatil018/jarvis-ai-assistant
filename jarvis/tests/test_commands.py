"""
tests/test_commands.py — Command Executor Unit Tests
"""

import sys
from pathlib import Path
from unittest.mock import patch, MagicMock
sys.path.insert(0, str(Path(__file__).parent.parent))

import pytest
from command_executor.app_launcher import AppLauncher, _find_best_match
from command_executor.browser_controller import BrowserController
from command_executor.file_manager import FileManager


class TestAppLauncher:

    @pytest.fixture
    def launcher(self):
        return AppLauncher()

    def test_finds_chrome(self):
        path = _find_best_match("chrome")
        assert path is not None
        assert "chrome" in path.lower()

    def test_finds_notepad(self):
        path = _find_best_match("notepad")
        assert path is not None

    def test_fuzzy_match(self):
        path = _find_best_match("vs code")
        assert path is not None

    def test_unknown_app(self):
        path = _find_best_match("unknownapp12345xyz")
        assert path is None

    def test_launch_returns_message(self, launcher):
        with patch("subprocess.Popen") as mock_popen:
            mock_popen.return_value = MagicMock()
            result = launcher.launch("notepad")
            assert "notepad" in result.lower() or "opening" in result.lower()

    def test_unknown_app_friendly_message(self, launcher):
        result = launcher.launch("nonexistentapp999")
        assert "don't know" in result.lower() or "couldn't" in result.lower()


class TestBrowserController:

    @pytest.fixture
    def browser(self):
        return BrowserController()

    def test_open_youtube(self, browser):
        with patch("webbrowser.open") as mock_open:
            result = browser.open("youtube")
            mock_open.assert_called_once()
            assert "youtube" in result.lower()

    def test_open_google(self, browser):
        with patch("webbrowser.open") as mock_open:
            result = browser.open("google")
            mock_open.assert_called_once()

    def test_google_search(self, browser):
        with patch("webbrowser.open") as mock_open:
            result = browser.google_search("Python tutorials")
            assert "python tutorials" in result.lower() or "searching" in result.lower()
            mock_open.assert_called_once()
            call_url = mock_open.call_args[0][0]
            assert "google.com/search" in call_url

    def test_youtube_search(self, browser):
        with patch("webbrowser.open") as mock_open:
            result = browser.search_youtube("machine learning")
            call_url = mock_open.call_args[0][0]
            assert "youtube.com/results" in call_url
            assert "machine+learning" in call_url or "machine%20learning" in call_url

    def test_open_raw_url(self, browser):
        with patch("webbrowser.open") as mock_open:
            result = browser.open("https://example.com")
            mock_open.assert_called_once_with("https://example.com", new=2)

    def test_unknown_site_falls_back_to_search(self, browser):
        with patch("webbrowser.open") as mock_open:
            result = browser.open("somerandomunknownsite9999")
            mock_open.assert_called_once()


class TestFileManager:

    @pytest.fixture
    def fm(self):
        return FileManager()

    def test_search_nonexistent(self, fm):
        result = fm.search_files("zzz_totally_fake_file_xyz_123")
        assert "no files" in result.lower() or "couldn't" in result.lower()

    def test_open_nonexistent(self, fm):
        result = fm.open_file("fake_nonexistent_file.xyz")
        assert "couldn't find" in result.lower() or "couldn't" in result.lower()

    def test_delete_nonexistent(self, fm):
        result = fm.delete_file("totally_fake_file.xyz")
        assert "couldn't find" in result.lower() or "couldn't" in result.lower()

    def test_search_empty_query(self, fm):
        result = fm.search_files("")
        assert "tell me" in result.lower() or "please" in result.lower()

    def test_open_real_file(self, fm, tmp_path):
        test_file = tmp_path / "hello.txt"
        test_file.write_text("hello")
        with patch("os.startfile") as mock_sf:
            result = fm.open_file(str(test_file))
            mock_sf.assert_called_once()
            assert "opening" in result.lower()

    def test_delete_real_file(self, fm, tmp_path):
        test_file = tmp_path / "todelete.txt"
        test_file.write_text("delete me")
        result = fm.delete_file(str(test_file))
        assert not test_file.exists()
        assert "deleted" in result.lower()
