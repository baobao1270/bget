import os
import sys
import time
import toml
import argparse
import traceback
from datetime import datetime
from typing import List, Tuple
from bgetlib.model import FavoriteItem, VideoWithPart

from .downloader import download_danmaku, download_cover, download_meta, download_parts
from .model import Runtime
from .utils import read_config, abspath, outdirs_init
from .logger import Logger
from .const import VERSION, TIME_FORMATTER


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(prog="bget", usage="bget [OPTIONS] <section>",
                                     description="bget - a python bilibili favourites batch downloader",
                                     formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument("alias", metavar="<section>", type=str,
                        help="section name of favourite in config file")
    parser.add_argument("-s", "--skip", metavar="<offset>", type=int, default=0,
                        help="skip <offset> videos form start")
    parser.add_argument("-k", "--cookies", metavar="<cookies>", type=str, default="bilibili.com_cookies.txt",
                        help="cookies file path")
    parser.add_argument("-c", "--config", metavar="<config>", type=str, default="config.toml",
                        help="config file path")
    parser.add_argument("-t", "--head", metavar="<head>", type=str, default="head.toml",
                        help="head file path")
    parser.add_argument("-o", "--out", metavar="<output-folder>", type=str, default="downloads",
                        help="download output folder path")
    parser.add_argument("-v", "--version", action="version", version=VERSION)
    return parser.parse_args()


def skip(rt: Runtime, collection_videos: List[FavoriteItem]):
    rt.logger.push("skip")
    skipped = collection_videos[:rt.skip]
    not_skipped = collection_videos[rt.skip:]
    for v in skipped:
        rt.logger.log("av{}: {:20}".format(v.avid, v.title))
    rt.logger.pop()
    return not_skipped


def ensure_dirs_created(rt: Runtime):
    os.makedirs(rt.config.cache_dir, exist_ok=True)
    # noinspection PyPep8Naming,SpellCheckingInspection
    OUTDIR = outdirs_init(rt)
    os.makedirs(OUTDIR.DASH, exist_ok=True)
    if rt.config.folder.flac_path is not None:
        os.makedirs(OUTDIR.FLAC, exist_ok=True)
    if rt.config.folder.aiff_path is not None:
        os.makedirs(OUTDIR.AIFF, exist_ok=True)
    if rt.config.folder.danmaku_path is not None:
        os.makedirs(OUTDIR.DANMAKU, exist_ok=True)
    if rt.config.folder.cover_path is not None:
        os.makedirs(OUTDIR.COVER, exist_ok=True)
    if rt.config.folder.meta_path is not None:
        os.makedirs(OUTDIR.META, exist_ok=True)


def get_pending_download(rt: Runtime) -> Tuple[List[FavoriteItem], datetime]:
    rt.logger.log("Using collection '{}' (id={})".format(rt.config.name, rt.config.id))
    rt.logger.log("HEAD is {}".format(rt.head.strftime(TIME_FORMATTER)))
    collection_videos = rt.api.get_favorites_nbf(favorite_id=rt.config.id,
                                                 from_timestamp=int(rt.head.timestamp()))
    snapshot_time = datetime.fromtimestamp(int(datetime.now().timestamp()))
    collection_videos = skip(rt, collection_videos)
    return collection_videos, snapshot_time


def download_collection(rt: Runtime, collection_videos: List[FavoriteItem], multipart_videos: List[VideoWithPart]):
    for collection_item in collection_videos:
        video = rt.api.get_video(collection_item.avid)
        rt.logger.push("av{}".format(video.avid))
        rt.logger.log("Title {:40}".format(video.title))
        rt.logger.log("Parts: {}, Uploader: {} (uid={})".format(
            len(video.parts), video.uploader.name, video.uploader.uid))
        download_video(rt, video)
        if len(video.parts) > 1:
            multipart_videos.append(video)
        rt.logger.pop()


def download_video(rt: Runtime, video: VideoWithPart):
    if rt.config.folder.danmaku_path is not None:
        download_danmaku(rt, video)
    if rt.config.folder.cover_path is not None:
        download_cover(rt, video)
    if rt.config.folder.meta_path is not None:
        download_meta(rt, video)
    download_parts(rt, video)
    time.sleep(5)


def update_head(rt: Runtime, old_head: datetime, new_head: datetime):
    head_filepath = abspath(rt.args.head)
    heads = {}
    if os.path.exists(head_filepath):
        heads = toml.load(head_filepath)
    heads[rt.config.name] = new_head
    with open(head_filepath, "w+", encoding="utf-8") as f:
        toml.dump(heads, f)
    rt.logger.tags = []
    rt.logger.log("New HEAD is set: {} -> {}".format(
        old_head.strftime(TIME_FORMATTER), new_head.strftime(TIME_FORMATTER)))


def print_multipart_videos(rt: Runtime, multipart_videos: List[VideoWithPart]):
    if len(multipart_videos) == 0:
        return
    rt.logger.tags = []
    rt.logger.log("Multipart Videos:")
    for v in multipart_videos:
        rt.logger.log("\tav{}\t{}".format(v.avid, v.title))
        rt.logger.log("\t\tLink: https://b23.tv/av{}".format(v.avid))
        for p in v.parts:
            rt.logger.log("\t\tcid={} {}".format(p.cid, p.name))


def main():
    args = parse_args()
    logger = Logger()
    config, head = read_config(logger, args)
    runtime = Runtime(args=args, config=config, head=head, logger=logger)
    ensure_dirs_created(runtime)
    collection_videos, snapshot_time = get_pending_download(runtime)
    multipart_videos: List[VideoWithPart] = []
    # noinspection PyBroadException
    try:
        download_collection(runtime, collection_videos, multipart_videos)
        update_head(runtime, head, snapshot_time)
    except:
        traceback.print_exc()
    finally:
        print_multipart_videos(runtime, multipart_videos)


if __name__ == "__main__":
    main()
