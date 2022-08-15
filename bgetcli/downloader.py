import os
import json
from typing import Optional
from bgetlib.models import DownloadProgress, QualityOptions
import bgetlib.codec as codec
import bgetlib.utils as utils

from .runtime import Runtime
from .utils import auto_format, ensure_file_directory_created


def show_progress(rt: Runtime, progress: DownloadProgress):
    progress.bar_format = ("[", 15, "]")
    progress_text = "{bar} {finished_mb:.2f}/{total_mb:.2f}M {speed_kbps:.2f}K/s avg={avg_speed_kbps:.2f}K/s".format(
        bar=f"{progress.tag}: {progress.percent:<7}{progress.bar}",
        finished_mb=progress.finished / 1024 / 1024,
        total_mb=progress.total / 1024 / 1024,
        speed_kbps=progress.speed / 1024,
        avg_speed_kbps=progress.average_speed / 1024,
    )
    rt.log_progress(progress_text + (" " * 10))
    if progress.done:
        rt.log("")


def downloader(name: str, extension: str = ""):
    def decorator(func):
        def wrapper(rt: Runtime, video: dict, part: Optional[int] = None):
            rt.log_tags.append(name)
            if part is not None:
                rt.log_tags.append(f"P{part+1}")
            filename = auto_format(rt.config.formatter[name], video, part, extension)
            filepath = os.path.join(rt.config.outdir, filename)
            ensure_file_directory_created(filepath)

            result = func(rt, filepath, video, part)
            rt.log("Saved to {}".format(filename))
            rt.log_tags.pop()
            if part is not None:
                rt.log_tags.pop()
            return result
        return wrapper
    return decorator


def get_av_stream_url(rt: Runtime, filename: str, aid: int, cid: int):
    stream = rt.bapi.get_stream_url(aid, cid, QualityOptions(
        h265=True,
        hdr=True,
        dolby_audio=True,
        dolby_vision=False,
        qhd_8k=True
    ))
    if rt.config.host is not None:
        stream["audio"] = utils.replace_host(stream["audio"], rt.config.host)
        stream["video"] = utils.replace_host(stream["video"], rt.config.host)
    return stream


@downloader("audio")
def download_audio(rt: Runtime, filename: str, video: dict, part: int):
    stream = get_av_stream_url(rt, filename, video["aid"], video["pages"][part]["cid"])
    audio_stream = rt.bapi.get_stream(stream["audio"], "audio", rt.config.chunk_size,
                                      callback=lambda p: show_progress(rt, p))
    extension = "aac"
    if stream["quality"].dolby_audio:
        extension = "ac3"
    if stream["quality"].flac_audio:
        extension = "flac"
    return codec.extract_audio(audio_stream, filename + extension, stream["quality"])


@downloader("video", extension="mp4")
def download_video(rt: Runtime, filename: str, video: dict, part: int):
    stream = get_av_stream_url(rt, filename, video["aid"], video["pages"][part]["cid"])
    audio_stream = rt.bapi.get_stream(stream["audio"], "audio", rt.config.chunk_size,
                                      callback=lambda p: show_progress(rt, p))
    video_stream = rt.bapi.get_stream(stream["video"], "video", rt.config.chunk_size,
                                      callback=lambda p: show_progress(rt, p))
    return codec.merge(audio_stream, video_stream, filename)


@downloader("danmaku", extension="xml")
def download_danmaku(rt: Runtime, filename: str, video: dict, part: int):
    content = rt.bapi.get_live_danmaku(video["pages"][part]["cid"])
    with open(filename, "wb+") as f:
        f.write(content)


@downloader("cover")
def download_cover(rt: Runtime, filename: str, video: dict, _: Optional[int]):
    basename, image = rt.bapi.get_cover_picture(video["aid"])
    extension = os.path.splitext(basename)[1]
    if extension.startswith("."):
        extension = extension[1:]
    filename = filename + extension
    with open(filename, "wb+") as f:
        f.write(image)


@downloader("meta", extension="json")
def download_meta(rt: Runtime, filename: str, video: dict, _: Optional[int]):
    with open(filename, "w+", encoding="utf-8") as f:
        f.write(json.dumps(video, ensure_ascii=False, indent=4))
