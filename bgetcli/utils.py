import argparse
import os
from typing import Tuple, Optional
from urllib.parse import urlparse, parse_qs

import bgetlib


def ensure_file_directory_created(file_path: str):
    os.makedirs(os.path.dirname(file_path), exist_ok=True)


def list_unique(original_list: list):
    return list(set(original_list))


def auto_format(fmt_string: str, video: dict, part_index: Optional[int] = 0, ext: str = ""):
    title = bgetlib.utils.ntfs_escape(video["title"])
    if part_index is None:
        part_index = 0
    kwargs = {
        "aid": video["aid"],
        "bvid": video["bvid"],
        "title": title,
        "up": video["owner"]["name"],
        "up_uid": video["owner"]["mid"],
        "p": part_index + 1,
        "parts": len(video["pages"]),
        "part_name": video["pages"][part_index]["part"],
        "cid": video["pages"][part_index]["cid"],
        "ext": ext
    }
    return fmt_string.format(**kwargs)


# noinspection PyBroadException
def parse_resources(args: argparse.Namespace, config_dict: dict) -> Tuple[str, int]:
    resource_name: str = args.resource.strip()

    # section
    if args.section:
        section = config_dict["section"].get(resource_name) or {}
        fid = section.get("id") or None
        if fid is None:
            return "notfound", 0
        return "fav", int(fid)

    # url
    if resource_name.startswith("http://") or resource_name.startswith("https://"):
        url = urlparse(resource_name)
        if url.netloc == "space.bilibili.com":
            try:
                return "fav", int(parse_qs(url.query).get("fid")[0])
            except:
                pass
        resource_name = os.path.basename(url.path).strip()

    # bare av/bv id
    try:
        aid = int(resource_name)
        return "video", aid
    except ValueError:
        pass
    if resource_name.lower().startswith("av"):
        return "video", int(resource_name[2:])
    if resource_name.lower().startswith("bv"):
        try:
            aid = bgetlib.utils.bv2av(resource_name)
            return "video", aid
        except:
            pass
    return "unknown", 0
