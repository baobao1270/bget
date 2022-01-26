import json
import os
import sys
import time
import toml
import bgetlib
import argparse
from dataclasses import dataclass, field
from typing import Optional, Dict, List, Tuple
from .utils import list_unique, parse_resources


@dataclass
class Report:
    skip: List[Dict] = field(default_factory=list)
    error: List[Dict] = field(default_factory=list)
    multipart: List[Dict] = field(default_factory=list)
    inaccessible: List[Dict] = field(default_factory=list)


@dataclass
class Config:
    outdir: str
    cookies: str
    chunk_size: int
    host: Optional[str]
    switches: List[str]
    formatter: Dict[str, str]

    def load(self, raw_config: dict, section_name: Optional[str] = None):
        override_config = raw_config
        if section_name is not None:
            override_config = raw_config.get("section", {}).get(section_name, {})
        self.outdir = override_config.get("outdir", self.outdir)
        self.cookies = override_config.get("cookies", self.cookies)
        self.chunk_size = override_config.get("chunk-size", self.chunk_size)
        self.host = override_config.get("host", self.host)
        self.switches = list_unique(override_config.get("switches", self.switches))
        for key in ["meta", "audio", "video", "cover", "danmaku"]:
            self.formatter[key] = override_config.get("formatter-" + key, self.formatter[key])

    def load_args(self, args: argparse.Namespace):
        self.cookies = args.cookies or self.cookies
        self.outdir = args.outdir or self.outdir
        self.chunk_size = args.chunk_size or self.chunk_size
        self.host = args.host or self.host
        if args.no_meta:
            self.switches = list_unique(self.switches)
            self.switches.remove("meta")
        if args.no_danmaku:
            self.switches = list_unique(self.switches)
            self.switches.remove("danmaku")
        if args.with_cover:
            self.switches = list_unique(self.switches)
            self.switches.append("danmaku")
        if args.audio_only:
            self.switches.append("audio")
            self.switches = list_unique(self.switches)
            self.switches.remove("video")

    def print_self(self, logger):
        logger(
            "Calculated configuration:",
            f"dest={self.outdir}",
            f"cookies={self.cookies}",
            f"chunk_size={self.chunk_size}",
            f"host={self.host}"
        )
        logger(f"Switches: {', '.join(self.switches)}")
        logger(f"Formatters:")
        for key, value in self.formatter.items():
            logger(f"  {key}: {value}")


@dataclass
class Runtime:
    bapi: bgetlib.BilibiliAPI
    args: argparse.Namespace
    report: Report
    config: Config
    section_name: str
    resource_type: str
    resource_id: int
    log_tags: List[str] = field(init=False, default_factory=list)

    def __post_init__(self):
        if self.resource_type == "notfound":
            self.log("Section name not found in configuration")
            sys.exit()
        if self.resource_type == "unknown":
            self.log("Can not parse resource")
            sys.exit()
        self.config.print_self(self.log)
        self.log(f"Fetching resource {self.resource_type}:{self.resource_id}")

    @staticmethod
    def factory(args: argparse.Namespace, config: Config):
        section_name: str = args.resource.strip() if args.section else None
        config_dict = toml.load(args.config) if args.config is not None else {"section": {}}
        config = Runtime.build_config(args, config, section_name)
        resource_type, resource_id = parse_resources(args, config_dict)
        bapi = bgetlib.BilibiliAPI(config.cookies)
        report = Report()
        return Runtime(bapi, args, report, config, section_name, resource_type, resource_id)

    @staticmethod
    def build_config(args: argparse.Namespace, config: Config, section_name: str) -> Config:
        config_dict = toml.load(args.config) if args.config is not None else {"section": {}}
        config.load(config_dict)
        config.load_args(args)
        if args.section:
            config.load(config_dict, section_name)
        return config

    def log(self, *values, **kwargs):
        tags = "".join([f"[{tag}]" for tag in self.log_tags])
        print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}]" + tags, end="")
        print(*values, **kwargs)

    def log_progress(self, *values, **kwargs):
        kwargs["end"] = "\r"
        kwargs["flush"] = True
        self.log(*values, **kwargs)


class SectionHead:
    def __init__(self, runtime: Runtime):
        self.runtime: Runtime = runtime
        self.section: str = runtime.section_name
        self.filename: str = runtime.args.section_head
        self.tick_at: Optional[int] = None

    def tick(self):
        self.tick_at = int(time.time())
        self.runtime.log(f"Start downloading at {self.tick_at}")

    def read(self) -> int:
        if (not os.path.exists(self.filename)) or (self.runtime.section_name is None):
            return 172800  # offset 2 day to avoid timezone issue
        with open(self.filename, "r", encoding="utf-8") as f:
            head_timestamp = json.load(f).get(self.runtime.section_name)
        head_timestamp = head_timestamp or 172800
        self.runtime.log("Reading head timestamp: {}")
        return head_timestamp or 172800

    def write(self):
        if self.runtime.section_name is None:
            return
        if self.tick_at is None:
            self.runtime.log("Error: can not write before tick")
            sys.exit()
        if not os.path.exists(self.filename):
            heads = {}
        else:
            with open(self.filename, "r", encoding="utf-8") as f:
                heads = json.load(f)
        self.runtime.log(f"Writing head timestamp: {self.tick_at}")
        heads[self.runtime.section_name] = self.tick_at
        with open(self.filename, "w+", encoding="utf-8") as f:
            f.write(json.dumps(heads, ensure_ascii=False, indent=4))
