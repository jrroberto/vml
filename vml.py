"""
Simple MoviePy wrapper with timestamp support and automatic resource management.

Usage:
    from vml import input, output

    i = input("video.mp4", sound=False)
    clip1 = i.clip("0:00:11.000", "0:00:12")
    clip2 = i.clip("0:00:13.000", "0:00:15")
    output([clip1, clip2]).save("out.mp4")
    
Features:

- Time formats: "0:00:11.500", "1:30", "90.5", or raw seconds
- Auto-cleanup: All clips close automatically on script exit via atexit
- Audio support: Detects audio files (.mp3, .wav, etc.) and uses AudioFileClip
- Access raw clip: Use clip.raw if you need MoviePy's underlying clip

Additional options:

# Single clip
output(clip1).save("single.mp4")

# Pass encoding options
output([clip1, clip2]).save("out.mp4", codec="libx264", preset="fast")

# Manual cleanup if needed
i.close()
"""

from moviepy.editor import VideoFileClip, AudioFileClip, concatenate_videoclips, concatenate_audioclips
import atexit

# Track all open resources for cleanup
_open_clips = []


def _parse_time(t):
    """Convert 'h:mm:ss.fff' or 'mm:ss.fff' or seconds to float seconds."""
    if t is None:
        return None
    if isinstance(t, (int, float)):
        return float(t)

    parts = t.split(':')
    parts = [float(p) for p in parts]

    if len(parts) == 3:
        return parts[0] * 3600 + parts[1] * 60 + parts[2]
    elif len(parts) == 2:
        return parts[0] * 60 + parts[1]
    return parts[0]


def _cleanup():
    """Close all open clips on exit."""
    for clip in _open_clips:
        try:
            clip.close()
        except:
            pass


atexit.register(_cleanup)


class Clip:
    """Wrapper around a MoviePy clip segment."""

    def __init__(self, clip, is_audio=False):
        self._clip = clip
        self._is_audio = is_audio

    @property
    def raw(self):
        """Access the underlying MoviePy clip."""
        return self._clip


class Input:
    """Wrapper around a MoviePy source file."""

    def __init__(self, path, sound=True):
        self._path = path
        self._sound = sound
        self._is_audio = path.lower().endswith(('.mp3', '.wav', '.ogg', '.flac', '.m4a', '.aac'))

        if self._is_audio:
            self._source = AudioFileClip(path)
        else:
            self._source = VideoFileClip(path, audio=sound)

        _open_clips.append(self._source)

    def clip(self, start, end=None):
        """Extract a clip segment using timestamp strings or seconds."""
        start_sec = _parse_time(start)
        end_sec = _parse_time(end)

        subclip = self._source.subclip(start_sec, end_sec)
        return Clip(subclip, is_audio=self._is_audio)

    def close(self):
        """Manually close the source."""
        if self._source in _open_clips:
            _open_clips.remove(self._source)
        self._source.close()


class Output:
    """Wrapper for concatenating and saving clips."""

    def __init__(self, clips: Clip | list[Clip]):
        if isinstance(clips, Clip):
            clips = [clips]
        self._clips = clips
        self._is_audio = clips[0]._is_audio if clips else False

    def save(self, path, **kwargs):
        """Concatenate clips and save to file."""
        raw_clips = [c._clip for c in self._clips]

        if self._is_audio:
            final = concatenate_audioclips(raw_clips)
            final.write_audiofile(path, **kwargs)
        else:
            final = concatenate_videoclips(raw_clips)
            final.write_videofile(path, **kwargs)

        return self


def input(path, sound=True):
    """Load a video or audio file."""
    return Input(path, sound=sound)


def output(clips: Clip | list[Clip]):
    """Prepare clips for concatenation and saving."""
    return Output(clips)
