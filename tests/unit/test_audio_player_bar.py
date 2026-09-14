"""Unit tests for the compatibility tab's VLC player lifecycle."""

import builtins
import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

import pytest
from PyQt5.QtWidgets import QApplication

from gui import main_window


class FakeState:
    Ended = "ended"
    Stopped = "stopped"
    NothingSpecial = "nothing-special"
    Playing = "playing"
    Error = "error"


class FakePlayer:
    def __init__(self, name, events):
        self.name = name
        self.events = events
        self.state = FakeState.Playing
        self.play_result = 0
        self.play_calls = 0
        self.position_calls = []
        self.media = None

    def set_media(self, media):
        self.media = media

    def get_media(self):
        return self.media

    def play(self):
        self.play_calls += 1
        self.events.append(f"{self.name}.play")
        return self.play_result

    def stop(self):
        self.events.append(f"{self.name}.stop")

    def pause(self):
        self.events.append(f"{self.name}.pause")

    def release(self):
        self.events.append(f"{self.name}.release")

    def get_state(self):
        return self.state

    def set_rate(self, rate):
        self.events.append(f"{self.name}.rate.{rate}")

    def audio_set_volume(self, volume):
        self.events.append(f"{self.name}.volume.{volume}")

    def set_position(self, position):
        self.position_calls.append(position)
        self.events.append(f"{self.name}.position.{position}")

    def get_position(self):
        return 0.25

    def get_time(self):
        return 0

    def get_length(self):
        return 120000

    def set_time(self, value):
        self.events.append(f"{self.name}.time.{value}")


class FakeInstance:
    def __init__(self, events, instance_number):
        self.events = events
        self.instance_number = instance_number
        self.players = []

    def media_player_new(self):
        player = FakePlayer(
            f"instance{self.instance_number}.player{len(self.players)}", self.events
        )
        self.players.append(player)
        return player

    def media_new(self, path):
        return path

    def release(self):
        self.events.append(f"instance{self.instance_number}.release")


class FakeVLC:
    State = FakeState

    def __init__(self):
        self.events = []
        self.instances = []

    def Instance(self, *arguments):
        instance = FakeInstance(self.events, len(self.instances))
        self.instances.append(instance)
        return instance


@pytest.fixture
def player_bar(monkeypatch):
    app = QApplication.instance() or QApplication([])
    fake_vlc = FakeVLC()
    monkeypatch.setattr(main_window, "_vlc", fake_vlc)
    monkeypatch.setattr(main_window, "VLC_AVAILABLE", True)
    bar = main_window.AudioPlayerBar()
    yield bar, fake_vlc, app
    bar.shutdown()
    bar.deleteLater()


def _showoff_plan():
    return {
        "bpm1_rate": 1.0,
        "bpm2_rate": 1.0,
        "exit_ratio": 0.75,
        "entry_ratio": 0.10,
        "crossfade_sec": 2,
    }


def test_showoff_sequences_tracks_before_starting_crossfade(player_bar):
    bar, fake_vlc, _ = player_bar
    plan = _showoff_plan()
    bar.load_tracks("first.mp3", "second.mp3")

    bar.execute_showoff(plan)
    generation = bar._showoff_generation
    assert fake_vlc.events == [
        "instance0.player0.stop", "instance0.player1.stop",
        "instance0.player0.rate.1.0", "instance0.player1.rate.1.0",
        "instance0.player0.volume.100", "instance0.player0.play",
    ]

    bar._showoff_seek_track1(generation)
    assert fake_vlc.events[-1] == "instance0.player0.position.0.75"
    assert bar._cf_timer is None

    bar._showoff_start_track2(generation)
    assert fake_vlc.events[-2:] == [
        "instance0.player1.volume.0", "instance0.player1.play"
    ]
    assert bar._cf_timer is None

    bar._showoff_seek_track2(generation)
    assert fake_vlc.events[-1] == "instance0.player1.position.0.1"
    assert bar._cf_timer is not None
    assert bar._cf_timer.isActive()


def test_native_vlc_import_failure_disables_internal_player(monkeypatch, caplog):
    app = QApplication.instance() or QApplication([])
    original_import = builtins.__import__

    def unavailable_vlc_import(name, *args, **kwargs):
        if name == "vlc":
            raise OSError("dlopen(libvlccore.dylib): image not found")
        return original_import(name, *args, **kwargs)

    with monkeypatch.context() as context:
        context.setattr(builtins, "__import__", unavailable_vlc_import)
        assert main_window._load_vlc() is None

    assert "VLC playback unavailable; internal player disabled" in caplog.text
    monkeypatch.setattr(main_window, "_vlc", None)
    monkeypatch.setattr(main_window, "VLC_AVAILABLE", False)
    bar = main_window.AudioPlayerBar()
    try:
        bar.load_tracks("first.mp3", "second.mp3")

        assert bar.status_lbl.text() == main_window.VLC_UNAVAILABLE_MESSAGE
        assert not bar.btn_play1.isEnabled()
        assert not bar.btn_play2.isEnabled()
        assert not bar.btn_stop.isEnabled()
        assert not bar.btn_showoff.isEnabled()
    finally:
        bar.shutdown()
        bar.deleteLater()


@pytest.mark.parametrize("action", ["stop", "reload", "close"])
def test_showoff_callbacks_are_invalidated_during_lifecycle_changes(player_bar, action):
    bar, fake_vlc, _ = player_bar
    bar.load_tracks("first.mp3", "second.mp3")
    original_player = bar._players[0]
    bar.execute_showoff(_showoff_plan())
    original_generation = bar._showoff_generation

    if action == "stop":
        bar.stop_all()
    elif action == "reload":
        bar.load_tracks("new-first.mp3", "new-second.mp3")
    else:
        bar.close()

    bar._showoff_seek_track1(original_generation)

    assert original_player.position_calls == []
    assert not bar._showoff_timers
    assert len(fake_vlc.instances) == (2 if action == "reload" else 1)


def test_old_showoff_callback_cannot_start_new_players(player_bar):
    bar, _, _ = player_bar
    bar.load_tracks("first.mp3", "second.mp3")
    bar.execute_showoff(_showoff_plan())
    original_generation = bar._showoff_generation

    bar.load_tracks("new-first.mp3", "new-second.mp3")
    new_track_two = bar._players[1]
    bar._showoff_start_track2(original_generation)

    assert new_track_two.play_calls == 0
    assert "Showoff!" not in bar.status_lbl.text()


def test_play_returning_minus_one_never_sets_playing_ui(player_bar, caplog):
    bar, _, _ = player_bar
    bar.load_tracks("first.mp3", "second.mp3")
    bar._players[0].play_result = -1

    bar._toggle_play(0)

    assert not bar._playing[0]
    assert "Playback error" in bar.status_lbl.text()
    assert "Track 1" in bar.btn_play1.text()
    assert "play() returned -1" in caplog.text


def test_vlc_error_state_never_sets_playing_ui(player_bar, caplog):
    bar, _, _ = player_bar
    bar.load_tracks("first.mp3", "second.mp3")
    bar._players[0].state = FakeState.Error

    bar._toggle_play(0)

    assert not bar._playing[0]
    assert "Playback error" in bar.status_lbl.text()
    assert "error state" in caplog.text


def test_players_are_stopped_and_released_before_shared_instance(player_bar):
    bar, fake_vlc, _ = player_bar
    bar.load_tracks("first.mp3", "second.mp3")
    bar.shutdown()

    events = fake_vlc.events
    instance_release = events.index("instance0.release")
    for player_number in (0, 1):
        player_prefix = f"instance0.player{player_number}"
        assert events.index(f"{player_prefix}.stop") < events.index(f"{player_prefix}.release")
        assert events.index(f"{player_prefix}.release") < instance_release
