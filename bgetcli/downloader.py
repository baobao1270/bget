import json
import bgetlib
from bgetlib import Transcoder
from bgetlib.model import VideoWithPart, DownloadProgress, VideoPart
from bgetcli.model import Runtime
from bgetcli.const import OUT
from bgetcli.utils import dest_path, class2dict, win_escape


def download_danmaku(rt: Runtime, video: VideoWithPart):
    for i in range(len(video.parts)):
        p = video.parts[i]
        rt.logger.push("P{}/{} (cid={})".format(i + 1, len(video.parts), p.cid))
        with open(dest_path(rt, OUT.FILENAME.DANMAKU, cid=p.cid), "wb+") as f:
            url = "https://comment.bilibili.com/{}.xml".format(p.cid)
            # noinspection PyProtectedMember
            f.write(rt.api._get(url).content)
            rt.logger.log("Danmaku/XML downloaded success (Title: {})".format(p.name))
        rt.logger.pop()


def download_cover(rt: Runtime, video: VideoWithPart):
    filepath = dest_path(rt, OUT.FILENAME.COVER, avid=video.avid, ext=video.cover.get_extname())
    with open(filepath, "wb+") as f:
        f.write(video.cover.download())
    rt.logger.log("Cover/PNG downloaded success")


def download_meta(rt: Runtime, video: VideoWithPart):
    with open(dest_path(rt, OUT.FILENAME.META, avid=video.avid), "w+", encoding="utf-8") as f:
        f.write(json.dumps(class2dict(video), indent=4, ensure_ascii=False))
    rt.logger.log("Meta/json downloaded success")


def download_part(rt: Runtime, video: VideoWithPart, part: VideoPart) -> Transcoder:
    @rt.downloader.callback_func
    def callback(progress: DownloadProgress):
        downloader_progress_callback(rt, progress)

    rt.logger.push("download")
    file_id = rt.downloader.download(
        video.avid, part.cid, tmp_dir=rt.config.cache_dir, chunk_size=rt.config.chunk_size, cdn_host=rt.config.cdn)
    rt.downloader.callbacks.clear()
    rt.logger.pop()
    return bgetlib.Transcoder(rt.config.cache_dir, file_id)


def transcode(rt: Runtime, ts: Transcoder, video: VideoWithPart, part: VideoPart, title: str):
    rt.logger.push("transcode")
    rt.logger.log("Merging video...", end="", flush=True)
    ts.save_dash(dest_path(rt, OUT.FILENAME.DASH, avid=video.avid, title=title))
    print("done")
    if rt.config.folder.flac_path is not None:
        rt.logger.log("Converting FLAC...", end="", flush=True)
        ts.to_flac(dest_path(rt, OUT.FILENAME.FLAC, avid=video.avid, title=title))
        print("done")
    if rt.config.folder.aiff_path is not None:
        rt.logger.log("Converting AIFF...", end="", flush=True)
        ts.to_aiff(dest_path(rt, OUT.FILENAME.AIFF, avid=video.avid, title=title))
        print("done")
    rt.logger.pop()


def download_parts(rt: Runtime, video: VideoWithPart):
    video_title = win_escape(video.title)
    for i in range(len(video.parts)):
        part = video.parts[i]
        rt.logger.push("P{}/{} (cid={})".format(i + 1, len(video.parts), part.cid))
        title = "{video_title}@[P{part_id:03d} {part_title}]".format(
            video_title=video_title,
            part_id=i + 1,
            part_title=win_escape(part.name)
        ) if len(video.parts) > 1 else video_title
        rt.logger.log("NTFS Name: {}".format(title))
        transcoder = download_part(rt, video, part)
        transcode(rt, transcoder, video, part, title)
        rt.logger.log("Done download/transcode")
        rt.logger.pop()


def downloader_progress_callback(rt: Runtime, progress: DownloadProgress):
    if progress.finished:
        rt.logger.log("")
        return None
    rt.logger.log(
        "Download {}: {:.2f}/{:.2f}MB, avg={:.2f}MB/s, diff={:.2f}MB/s".format(
               progress.tag,
               progress.downloaded_bytes / 1024 / 1024,
               progress.total_bytes / 1024 / 1024,
               progress.avg_speed() / 1024 / 1024,
               progress.speed() / 1024 / 1024
        ),
        end="\r"
    )
