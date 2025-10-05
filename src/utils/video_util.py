import ffmpeg
import io
import tempfile

def get_video_duration(video_bytes: bytes) -> float:
    """Get video duration from bytes using ffmpeg"""
    # Save bytes to a temporary file or use stdin
    with tempfile.NamedTemporaryFile(delete=False, suffix='.mp4') as tmp:
        tmp.write(video_bytes)
        tmp_path = tmp.name
    
    try:
        probe = ffmpeg.probe(tmp_path)
        print(probe)
        duration = float(probe['format']['duration'])
        return duration
    finally:
        import os
        os.unlink(tmp_path)
