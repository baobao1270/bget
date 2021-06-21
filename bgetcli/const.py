VERSION = "2.0.0"
TIME_FORMATTER = "%Y-%m-%d %H:%M:%S"
WINDOWS_ESCAPE_CHARS = {
    "/": "╱",
    "\\": "＼",
    "\"": "＂",
    ":": "：",
    "*": "🞰",
    "<": "＜",
    ">": "＞",
    "|": "｜",
    "?": "？"
}

class OUT:
    class DIR:
        def __init__(self):
            pass
        DANMAKU = "{out_dir}/{name}/danmaku"
        COVER   = "{out_dir}/{name}/cover"
        META    = "{out_dir}/{name}/json"
        DASH    = "{out_dir}/{name}/video"
        AIFF    = "{out_dir}/{name}/aiff"
        FLAC    = "{out_dir}/{name}/flac"

    class FILENAME:
        DANMAKU = "{cid}.xml"
        COVER   = "{avid}.{ext}"
        META    = "{avid}.json"
        DASH    = "av{avid}@{title}.mp4"
        AIFF    = "av{avid}@{title}.aiff"
        FLAC    = "av{avid}@{title}.flac"
