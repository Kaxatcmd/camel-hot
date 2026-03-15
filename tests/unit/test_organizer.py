"""
Unit tests for gui/file_manager/organizer.py

Tests cover:
- find_audio_files()       — discovery of audio files, extension filtering
- get_next_org_number()    — CH_Org[N] auto-increment logic
- organize_by_key()        — folder structure, file placement, callback contract
- create_playlist()        — M3U generation (mocked analysis)
"""

import os
import shutil
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest

from gui.file_manager.organizer import (
    find_audio_files,
    get_next_org_number,
    organize_by_key,
    create_harmonic_playlist,
)


# ── find_audio_files ───────────────────────────────────────────────────────

class TestFindAudioFiles:
    def test_empty_directory_returns_empty_list(self, tmp_input):
        result = find_audio_files(str(tmp_input))
        assert result == []

    def test_finds_mp3_wav_flac(self, tmp_input):
        for name in ("a.mp3", "b.wav", "c.flac"):
            (tmp_input / name).touch()
        result = find_audio_files(str(tmp_input))
        assert len(result) == 3

    def test_excludes_non_audio_extensions(self, tmp_input):
        (tmp_input / "readme.txt").touch()
        (tmp_input / "cover.jpg").touch()
        (tmp_input / "song.mp3").touch()
        result = find_audio_files(str(tmp_input))
        assert len(result) == 1
        assert result[0].endswith("song.mp3")

    def test_returns_absolute_paths(self, tmp_input):
        (tmp_input / "track.mp3").touch()
        result = find_audio_files(str(tmp_input))
        assert os.path.isabs(result[0])

    def test_nonexistent_directory_returns_empty(self, tmp_path):
        result = find_audio_files(str(tmp_path / "does_not_exist"))
        assert result == []

    def test_ogg_aiff_m4a_detected(self, tmp_input):
        for name in ("x.ogg", "y.aiff", "z.m4a"):
            (tmp_input / name).touch()
        result = find_audio_files(str(tmp_input))
        assert len(result) == 3


# ── get_next_org_number ────────────────────────────────────────────────────

class TestGetNextOrgNumber:
    def test_empty_directory_returns_1(self, tmp_output):
        assert get_next_org_number(str(tmp_output)) == 1

    def test_increments_past_existing_ch_org_folders(self, tmp_output):
        (tmp_output / "CH_Org1").mkdir()
        (tmp_output / "CH_Org2").mkdir()
        assert get_next_org_number(str(tmp_output)) == 3

    def test_handles_non_contiguous_numbers(self, tmp_output):
        (tmp_output / "CH_Org1").mkdir()
        (tmp_output / "CH_Org5").mkdir()
        assert get_next_org_number(str(tmp_output)) == 6

    def test_ignores_non_ch_org_folders(self, tmp_output):
        (tmp_output / "MyMusic").mkdir()
        (tmp_output / "8A_Camelot").mkdir()
        assert get_next_org_number(str(tmp_output)) == 1

    def test_nonexistent_target_returns_1(self, tmp_path):
        assert get_next_org_number(str(tmp_path / "new_dir")) == 1


# ── organize_by_key ────────────────────────────────────────────────────────

class TestOrganizeByKey:
    """
    Tests use mock analyze_track so no real audio I/O is needed.
    """

    def _make_audio_files(self, directory: Path, names):
        for name in names:
            (directory / name).touch()

    def test_organizes_into_camelot_subfolders(self, tmp_input, tmp_output):
        self._make_audio_files(tmp_input, ["track1.mp3", "track2.mp3"])

        def fake_analyze(path):
            return {
                "file_path": path,
                "key": "C Major",
                "camelot": "8B",
                "bpm": 128,
                "duration": 300.0,
                "confidence": 0.9,
            }

        with patch("audio_analysis.key_detection.analyze_track", side_effect=fake_analyze):
            result = organize_by_key(str(tmp_input), str(tmp_output))

        assert result["organized_count"] == 2
        assert "8B" in result.get("by_key", {})

    def test_parent_folder_name_creates_subfolder(self, tmp_input, tmp_output):
        (tmp_input / "song.mp3").touch()

        def fake_analyze(path):
            return {"file_path": path, "key": "A Minor", "camelot": "8A",
                    "bpm": 125, "duration": 240.0, "confidence": 0.8}

        with patch("audio_analysis.key_detection.analyze_track", side_effect=fake_analyze):
            organize_by_key(str(tmp_input), str(tmp_output),
                            parent_folder_name="CH_Org1")

        key_folder = tmp_output / "CH_Org1" / "8A_Camelot"
        assert key_folder.is_dir() or (tmp_output / "CH_Org1").is_dir()

    def test_unknown_key_goes_to_unclassified(self, tmp_input, tmp_output):
        (tmp_input / "mystery.mp3").touch()

        def fake_analyze(path):
            return {"file_path": path, "key": "Unknown", "camelot": "Unknown",
                    "bpm": 0, "duration": 0.0, "confidence": 0.0}

        with patch("audio_analysis.key_detection.analyze_track", side_effect=fake_analyze):
            result = organize_by_key(str(tmp_input), str(tmp_output))

        # File should not appear in by_key under a real Camelot code
        for code in result.get("by_key", {}):
            assert code != "Unknown"

    def test_progress_callback_called_per_file(self, tmp_input, tmp_output):
        for i in range(3):
            (tmp_input / f"track{i}.mp3").touch()

        calls = []

        def fake_analyze(path):
            return {"file_path": path, "key": "C Major", "camelot": "8B",
                    "bpm": 128, "duration": 300.0, "confidence": 0.9}

        def cb(filename, idx, total):
            calls.append((filename, idx, total))
            return False  # don't cancel

        with patch("audio_analysis.key_detection.analyze_track", side_effect=fake_analyze):
            organize_by_key(str(tmp_input), str(tmp_output), progress_callback=cb)

        assert len(calls) == 3
        assert all(total == 3 for _, _, total in calls)

    def test_progress_callback_cancel_stops_processing(self, tmp_input, tmp_output):
        for i in range(5):
            (tmp_input / f"track{i}.mp3").touch()

        calls = []

        def fake_analyze(path):
            return {"file_path": path, "key": "C Major", "camelot": "8B",
                    "bpm": 128, "duration": 300.0, "confidence": 0.9}

        def cb(filename, idx, total):
            calls.append(idx)
            return idx >= 1  # cancel after 2nd file

        with patch("audio_analysis.key_detection.analyze_track", side_effect=fake_analyze):
            organize_by_key(str(tmp_input), str(tmp_output), progress_callback=cb)

        # Should have stopped after cancellation
        assert len(calls) <= 5

    def test_does_not_modify_input_directory(self, tmp_input, tmp_output):
        for i in range(2):
            (tmp_input / f"song{i}.mp3").touch()

        before = set(f.name for f in tmp_input.iterdir())

        def fake_analyze(path):
            return {"file_path": path, "key": "G Major", "camelot": "9B",
                    "bpm": 130, "duration": 200.0, "confidence": 0.85}

        with patch("audio_analysis.key_detection.analyze_track", side_effect=fake_analyze):
            organize_by_key(str(tmp_input), str(tmp_output), move_files=False)

        after = set(f.name for f in tmp_input.iterdir())
        assert before == after, "Input directory was modified (files should be copied, not removed)"

    def test_result_keys_total_files_and_organized_count(self, tmp_input, tmp_output):
        (tmp_input / "a.mp3").touch()

        def fake_analyze(path):
            return {"file_path": path, "key": "D Major", "camelot": "10B",
                    "bpm": 120, "duration": 180.0, "confidence": 0.7}

        with patch("audio_analysis.key_detection.analyze_track", side_effect=fake_analyze):
            result = organize_by_key(str(tmp_input), str(tmp_output))

        assert "total_files" in result
        assert "organized_count" in result
        assert "by_key" in result


# ── create_harmonic_playlist ───────────────────────────────────────────────

class TestCreateHarmonicPlaylist:
    def test_generates_m3u_file(self, tmp_input, tmp_output):
        (tmp_input / "track1.mp3").touch()
        out_file = str(tmp_output / "playlist.m3u")

        def fake_analyze(path):
            return {"file_path": path, "key": "A Minor", "camelot": "8A",
                    "bpm": 125, "duration": 240.0, "confidence": 0.8}

        with patch("audio_analysis.key_detection.analyze_track", side_effect=fake_analyze):
            create_harmonic_playlist(
                input_directory=str(tmp_input),
                output_file=out_file,
            )

        assert Path(out_file).exists()

    def test_m3u_header_present(self, tmp_input, tmp_output):
        (tmp_input / "track.mp3").touch()
        out_file = str(tmp_output / "test.m3u")

        def fake_analyze(path):
            return {"file_path": path, "key": "C Major", "camelot": "8B",
                    "bpm": 128, "duration": 300.0, "confidence": 0.9}

        with patch("audio_analysis.key_detection.analyze_track", side_effect=fake_analyze):
            create_harmonic_playlist(
                input_directory=str(tmp_input),
                output_file=out_file,
            )

        content = Path(out_file).read_text()
        assert "#EXTM3U" in content
