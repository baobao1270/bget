import os
import sys
import shutil
import argparse
import bgetlib
import pkg_resources
import base64
from typing import List
from enum import IntEnum

from .utils import auto_format
from .runtime import Config, Runtime, SectionHead
from . import downloader


VERSION = pkg_resources.get_distribution("bget").version
DEFAULT_CONFIG = Config(
    outdir=".",
    cookies="bilibili.com_cookies.txt",
    chunk_size=8192,
    host=None,
    formatter={
        "audio": "av{aid}-P{p:0>3d} {title}.{ext}",
        "video": "av{aid}-P{p:0>3d} {title}.mp4",
        "danmaku": "av{aid}-P{p:0>3d}.xml",
        "cover": "av{aid}.{ext}",
        "meta": "av{aid}.json",
    },
    switches=["video"]
)
FLAC_CHECKER = [
    "BV1dZ4y1Y7bt",  # 光与影的对白      FLAC_CAPABLE
    "BV1Z8411A7NH",  # 夏语遥AI 《诗》   FLAC_NEED_VIP
]
WINDOWS_FFMPEG = "KiBXaW5kb3dzIFtXaW5kb3dzIDEwIDIwSDIgYWJvdmUgb25seV06CiAgIGEuIFN5c3RlbSB3aWRlLCBmb3IgYWxsIHVzZXIsIHJ1biBhcyBhZG1pbmlzdHJhdG9yCiAgICAgIGN1cmwgaHR0cHM6Ly9pbWFnZS1ob3N0LTEyNTExMzE1NDUuZmlsZS5teXFjbG91ZC5jb20vYnktdXVpZC9lMDM4YmIxOC00NzVjLTQ4YjItODA2Yy00Nzc1ZGNjYzZkYTAvMjAyMy0wMS0yMS0wNS0wNy00NS11dGMtMTY3NDI3NzY2NS9mZm1wZWcuZXhlIC1vIEM6XFdpbmRvd3NcU3lzdGVtMzJcZmZtcGVnLmV4ZQogICBiLiBJbnN0YWxsIGZvciBjdXJyZW50IGRpcmVjdG9yeSBvbmx5CiAgICAgIGN1cmwgaHR0cHM6Ly9pbWFnZS1ob3N0LTEyNTExMzE1NDUuZmlsZS5teXFjbG91ZC5jb20vYnktdXVpZC9lMDM4YmIxOC00NzVjLTQ4YjItODA2Yy00Nzc1ZGNjYzZkYTAvMjAyMy0wMS0yMS0wNS0wNy00NS11dGMtMTY3NDI3NzY2NS9mZm1wZWcuZXhlIC1vIGZmbXBlZy5leGUKCg=="
WINDOWS_FFMPEG = base64.b64decode(WINDOWS_FFMPEG).decode("utf-8").strip().splitlines()


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(prog="bget", usage="bget [OPTIONS] <resource>",
                                     description="bget - a python bilibili favourites batch downloader",
                                     formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument("resource", metavar="<resource>", type=str,
                        help="a bilibili resource, url, video id or section name")
    parser.add_argument("-v", "--version", action="version", version=VERSION)

    # common settings
    parser.add_argument("--config", metavar="<config>", type=str, default=None,
                        help="config file path")
    parser.add_argument("-k", "--cookies", metavar="<cookies>", type=str, default=DEFAULT_CONFIG.cookies,
                        help="cookies file path")
    parser.add_argument("-o", "--outdir", action="store", metavar="<outdir>", type=str, default=None,
                        help="download output folder path")
    parser.add_argument("--chunk-size", metavar="<chunk-size-byte>", type=int, default=None,
                        help="chunk size of downloader")
    parser.add_argument("--host", metavar="<host>", type=str, default=None,
                        help="override the host of stream CDN")
    parser.add_argument("--meta", action="store_true", help="download metadata")
    parser.add_argument("--danmaku", action="store_true", help="download danmaku")
    parser.add_argument("--cover", action="store_true", help="download cover picture")
    parser.add_argument("--audio-only", action="store_true", help="download audio only")
    parser.add_argument("--log-include-date", action="store_true", help="include date in log")

    # Section Mode
    parser.add_argument("-s", "--skip", metavar="<offset>", type=int, default=0,
                        help="skip <offset> videos if downloading a list, not work for downloading single video")
    parser.add_argument("--section", action="store_true", help="enable section mode")
    parser.add_argument("--section-head", metavar="<head>", type=str, default="head.json",
                        help="section mode: path to head")
    parser.add_argument("--force-h264", action="store_true", default=False, help="section mode: force downloading h264 stream")
    return parser.parse_args()


def check_ffmpeg():
    ffmpeg = shutil.which("ffmpeg")
    if (ffmpeg is None) or (ffmpeg == ""):
        print("""
        bgetcli tool error: FFMPEG NOT FOUND !!!
        Please install ffmpeg first. You can download it by command below:
        {}
        {}
        {}
        {}
        {}
        * Debian/Ubuntu:    apt install ffmpeg
        * Arch Linux:       pacman -S ffmpeg
        * macOS:            brew install ffmpeg
        """.format(*WINDOWS_FFMPEG))
        sys.exit(-1)
    print(f"Found ffmpeg at: {ffmpeg}")


def ensure_cookies_exist(cookies_path: str):
    if os.path.exists(cookies_path):
        print(f"Found cookies file at: {cookies_path}")
        return
    print(f"Cookies file not found: {cookies_path}")
    print("Creating an empty cookies file.")
    with open(cookies_path, "w+") as f:
        # Create an empty cookies file
        f.write("# Netscape HTTP Cookie File\n\n")


class FLACState(IntEnum):
    FLAC_NOT_PRESENT = 0
    FLAC_LOCKED = 1
    FLAC_OK = 2
    FLAC_NEED_LOGIN = 0x7120CCCC
    FLAC_NEED_VIP = 0x7120FFFF


def check_flac(cookies_file: str):
    def check_flac_video(bvid: str):
        print(f"Checking FLAC with bvid: {bvid}", end="\t")
        bapi = bgetlib.BilibiliAPI(cookies_file)
        cid = bapi._interface_request(f"/x/player/pagelist?bvid={bvid}")["data"][0]["cid"]
        print(f"cid={cid}", end="\t")
        flac = bapi._interface_request(f"/x/player/playurl?bvid={bvid}&cid={cid}&fnver=0&fnval=1168&fourk=1")["data"]["dash"].get("flac")
        if flac is None:
            print("FLAC_NOT_PRESENT")
            return FLACState.FLAC_NOT_PRESENT
        if flac.get("display"):
            if (flac.get("audio") or {}).get("baseUrl"):
                print("FLAC_OK")
                return FLACState.FLAC_OK
            else:
                print("FLAC_LOCKED")
                return FLACState.FLAC_LOCKED
        return FLACState.FLAC_NOT_PRESENT
    
    flac_check_0 = check_flac_video(FLAC_CHECKER[0])
    flac_check_1 = check_flac_video(FLAC_CHECKER[1])
    if flac_check_0 == FLACState.FLAC_OK and flac_check_1 == FLACState.FLAC_OK:
        print("FLAC_OK: FLAC/HiRes check passed.")
        return FLACState.FLAC_OK
    if flac_check_0 == FLACState.FLAC_LOCKED and flac_check_1 == FLACState.FLAC_LOCKED:
        print("FLAC_NEED_LOGIN: You have to login to download FLAC/HiRes.")
        return FLACState.FLAC_NEED_LOGIN
    if flac_check_0 == FLACState.FLAC_OK and flac_check_1 == FLACState.FLAC_LOCKED:
        print("FLAC_NEED_VIP: You have to be a VIP or paid to download all FLAC/HiRes, but you can still download free FLAC content (example: https://b23.tv/BV1dZ4y1Y7bt ).")
        return FLACState.FLAC_NEED_VIP
    print("FLAC_NOT_PRESENT: FLAC/HiRes check failed. Unknown error.")
    return FLACState.FLAC_NOT_PRESENT


def main():
    args = parse_args()
    check_ffmpeg()
    ensure_cookies_exist(args.cookies)
    if args.resource == "check-account":
        return check_flac(args.cookies)
    runtime = Runtime.factory(args, DEFAULT_CONFIG)
    section_head = SectionHead(runtime)
    download_tasks = generate_tasks(runtime, section_head)
    section_head.tick()

    videos = checkout_videos(runtime, download_tasks)
    download_videos(runtime, videos)

    section_head.write()
    report(runtime)
    runtime.log("All done.")


def logger_tag(tag: str):
    def decorator(func):
        def wrapper(runtime: Runtime, *values, **kwargs):
            runtime.log_tags.append(tag)
            result = func(runtime, *values, **kwargs)
            runtime.log_tags.pop()
            return result
        return wrapper
    return decorator


def generate_tasks(runtime: Runtime, section_head: SectionHead):
    tasks = list()
    if runtime.resource_type == "fav":
        if runtime.section_name is None:
            tasks = runtime.bapi.get_favorites_all(runtime.resource_id)
        else:
            tasks = runtime.bapi.get_favorites_since(runtime.resource_id, section_head.read())
        tasks = skip(runtime, tasks, runtime.args.skip)
    if runtime.resource_type == "video":
        tasks = [{"id": runtime.resource_id}]
    return tasks


@logger_tag("skip")
def skip(runtime: Runtime, tasks: List[dict], skip_count: int) -> List[dict]:
    if skip_count == 0:
        return tasks
    runtime.log(f"Skipping {skip_count} items below:")
    skipped = tasks[:skip_count]
    remains = tasks[skip_count:]
    runtime.report.skip = skipped
    for task in skipped:
        runtime.log(f"Skip: av{task['id']}: {task['title']:20}")
    return remains


@logger_tag("checkout")
def checkout_videos(runtime: Runtime, tasks: List) -> List[dict]:
    videos = list()
    for i in range(len(tasks)):
        task = tasks[i]
        aid = task["id"]
        # noinspection PyBroadException
        try:
            video = runtime.bapi.get_video(aid)
        except:
            runtime.report.inaccessible.append(task)
            runtime.log(f"Inaccessible: av{aid}: {task['title']:20}")
            continue
        videos.append(video)
    runtime.log(f"Checkout {len(videos)} videos, {len(runtime.report.inaccessible)} inaccessible.")
    return videos


@logger_tag("dl")
def download_videos(runtime: Runtime, videos: List):
    for i in range(len(videos)):
        video = videos[i]
        if len(video["pages"]) > 1:
            runtime.report.multipart.append(video)
        runtime.log(f"Start downloading {i+1}/{len(videos)} https://b23.tv/av{video['aid']}")
        runtime.log_tags.append(f"av{video['aid']}")
        download_video(runtime, video)
        runtime.log_tags.pop()


def download_video(runtime: Runtime, video: dict):
    runtime.log(auto_format("av{aid} {bvid} {parts}P up='{up}' (uid={up_uid})", video))
    runtime.log(auto_format("Title: {title}", video))
    for p in range(len(video["pages"])):
        runtime.log(auto_format("Part {p}/{parts} cid={cid}: {part_name}", video, p))
        if "audio" in runtime.config.switches:
            downloader.download_audio(runtime, video, p)
        if "video" in runtime.config.switches:
            downloader.download_video(runtime, video, p)
        if "danmaku" in runtime.config.switches:
            downloader.download_danmaku(runtime, video, p)
    if "cover" in runtime.config.switches:
        downloader.download_cover(runtime, video)
    if "meta" in runtime.config.switches:
        downloader.download_meta(runtime, video)
    runtime.log(f"Done download av{video['aid']}")


def report(runtime: Runtime):
    print("=" * 80)
    print(f"""Download Report
    Skip: {len(runtime.report.skip)}
    Inaccessible: {len(runtime.report.inaccessible)}
    Error: {len(runtime.report.error)}
    Multipart: {len(runtime.report.multipart)}
    """)

    print("\n====== Skip ========")
    for task in runtime.report.skip:
        print(f"https://b23.tv/av{task['id']:<20} {task['title']:20}")

    print("\n=== Inaccessible ===")
    for task in runtime.report.inaccessible:
        print(f"https://b23.tv/av{task['id']:<20} {task['title']:20}")

    # print("\n====== Error =======")
    print("\n==== Multipart =====")
    for video in runtime.report.multipart:
        print(f"https://b23.tv/av{video['aid']:<20} {len(video['pages'])}P {video['title']:16}")
        for p in range(len(video["pages"])):
            part = video["pages"][p]
            print(f"      P{p+1:<5} cid={part['cid']:<15} {part['part']:20}")

    print("\n\nEnd of Download Report")
    print("=" * 80, "\n")


if __name__ == "__main__":
    main()
