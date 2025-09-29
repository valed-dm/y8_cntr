import subprocess
import tempfile
from pathlib import Path

from moviepy import VideoFileClip


def mp4_to_gif(
    input_path: str,
    output_path: str,
    start: int = 0,
    duration: int | None = None,
    resize: float = 1.0,
    fps: int = 12,
    optimize: bool = True,
) -> None:
    """
    Convert MP4/AVI to GIF with optional trimming, resizing, and optimization.
    """

    input_path = str(Path(input_path))
    output_path = str(Path(output_path))

    with VideoFileClip(str(input_path)) as clip:
        # Trim
        clip = clip.subclipped(start, start + duration if duration else None)

        # Resize
        if resize != 1.0:
            clip = clip.resized(resize)

        # FPS
        clip = clip.with_fps(fps)

        # Temporary GIF
        with tempfile.NamedTemporaryFile(suffix=".gif", delete=False) as tmp:
            temp_gif = Path(tmp.name)

        clip.write_gif(str(temp_gif))

    if optimize:
        optimized = False

        # Try gifsicle first
        try:
            subprocess.run(
                [
                    "gifsicle",
                    "-O3",
                    "--colors",
                    "256",
                    str(temp_gif),
                    "-o",
                    str(output_path)],
                check=True,
            )
            optimized = True
        except FileNotFoundError:
            pass

        # Fallback to ffmpeg
        if not optimized:
            subprocess.run(
                [
                    "ffmpeg", "-y", "-i", str(temp_gif),
                    "-vf", f"fps={fps},scale=480:-1:flags=lanczos",
                    str(output_path),
                ],
                check=True,
            )
        temp_gif.unlink(missing_ok=True)
    else:
        temp_gif.rename(output_path)

    print(f"✅ GIF saved at: {output_path}")


mp4_to_gif(
    "../output/output_dual_video.mp4",
    "../output/output_dual.gif",
    start=10,
    duration=5,
    resize=0.5,
    fps=10,
    optimize=True,
)
