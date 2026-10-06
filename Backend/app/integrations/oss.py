"""OSS 适配器 —— **Phase 2.1 只做「只读规则」，不做任何网络调用。**

冻结依据：
  * **D5 FROZEN**：不迁 bucket（继续 `kjc-blog-2026`）
  * **D6 FROZEN**：不删除对象，只登记未引用对象
  * **URL 规则【FACT】**（``analysis/common-src/cc/feitwnd/utils/AliOssUtil.java``）::

        https://{bucket}.{endpoint-host}/{category}/{uuid}.{ext}

  * 【FACT】对象命名 ``{category}/{UUID}.{ext}``；**10 类目录**由 ``getFileCategory(扩展名)`` 生成
  * 【FACT】107 objects / 72.61 MB；68 referenced（64 业务表 + 4 ``operation_logs.operate_data``）

**本阶段明确不做**（Stage 2.1 范围）：
  * ❌ 上传 / 删除 / 拷贝对象
  * ❌ bucket 迁移
  * ❌ 修改任何历史 URL

**Stage 2.2 追加（仍是"零副作用"）**：
  * ✅ ``get_file_category`` / ``build_object_key`` / ``build_upload_url``
    —— 纯函数，复刻 ``AliOssUtil`` 的 10 类目映射与 ``{category}/{uuid}.{ext}`` 规则
  * ❌ 仍**不**上传、**不**持有可用于写操作的 SDK 客户端、**不** import ``oss2``/``aliyun``

⚠️ 因此本模块**依旧没有任何写操作**（由 ``tests/contract/test_oss_helpers.py`` 与
   ``tests/contract/test_frozen_golden_artifacts.py`` 双重断言）。
"""
from __future__ import annotations

import re
from urllib.parse import urlparse

from app.core.config import Settings, get_settings

__all__ = [
    "OssUrlRules",
    "extract_oss_key",
    "strip_oss_url_prefix",
    "FILE_CATEGORY_MAP",
    "get_file_category",
    "build_object_key",
    "build_upload_url",
]

# 【FACT】**已知**目录前缀（来自 OSS 清单的 Prefix 分布：image/ 95 · audio/ 5 · text/ 5 · other/ 1 · 根目录 1）
KNOWN_PREFIXES = ("image/", "audio/", "text/", "other/")

_OSS_URL_RE = re.compile(r"^https?://[^/]+/(?P<key>.+)$")

# ---------------------------------------------------------------------------
# 【FACT】``AliOssUtil.getFileCategory(String extension)`` —— 逐条复刻 switch 分支
# ---------------------------------------------------------------------------
# ⚠️【FACT·关键】该 switch **区分大小写**、且**没有** ``toLowerCase()``
#   ⇒ ``"PNG"`` / ``"JPG"`` 会**落空**到 ``return "other"``（对象被存进 ``other/`` 目录）。
#   这是旧系统的**实际行为**（是否属缺陷需产品裁决）—— **本阶段原样复刻，不做归一化**。
#   证据：``analysis/common-src/cc/feitwnd/utils/AliOssUtil.java`` 第 60–140 行。
FILE_CATEGORY_MAP: dict[str, str] = {
    # image
    "jpg": "image", "png": "image", "gif": "image", "bmp": "image", "webp": "image",
    "jpeg": "image", "svg": "image", "ico": "image", "tiff": "image",
    # video
    "mp4": "video", "avi": "video", "mov": "video", "mkv": "video", "wmv": "video",
    "flv": "video", "webm": "video", "m4v": "video", "3gp": "video",
    # audio
    "mp3": "audio", "wav": "audio", "wma": "audio", "ogg": "audio", "aac": "audio",
    "flac": "audio", "m4a": "audio", "ape": "audio", "mid": "audio", "midi": "audio",
    # lyric
    "lrc": "lyric", "lrcx": "lyric", "krc": "lyric", "qrc": "lyric", "trc": "lyric",
    "ksc": "lyric",
    # text
    "txt": "text", "md": "text", "rtf": "text",
    # pdf
    "pdf": "pdf",
    # word
    "doc": "word", "docx": "word", "dot": "word", "dotx": "word",
    # excel
    "xls": "excel", "xlsx": "excel", "xlt": "excel", "xltx": "excel",
    # archive
    "zip": "archive", "rar": "archive", "7z": "archive", "tar": "archive",
    "gz": "archive", "bz2": "archive",
    # font
    "ttf": "font", "otf": "font", "woff": "font", "woff2": "font", "eot": "font",
}
FILE_CATEGORY_COUNT = 10  # 【FACT】10 个具名类目（image/video/audio/lyric/text/pdf/word/excel/archive/font）

# 【FACT】10 个类目 + 未识别时的 ``"other"`` = 11 个可能取值
FILE_CATEGORY_UNKNOWN = "other"


def get_file_category(extension: str) -> str:
    """复刻 ``AliOssUtil.getFileCategory``（**大小写敏感**，未识别 → ``"other"``）。"""
    return FILE_CATEGORY_MAP.get(extension, FILE_CATEGORY_UNKNOWN)


def build_object_key(extension: str, file_name: str) -> str:
    """复刻 ``AliOssUtil.upload`` 的 ``objectName = getFileCategory(ext) + "/" + fileName``。

    ``file_name`` 由调用方给出 —— 旧系统为 ``UUID.randomUUID() + "." + extension``
    （见 ``CommonServiceImpl.uploadFile``）。
    """
    return f"{get_file_category(extension)}/{file_name}"


def build_upload_url(
    extension: str,
    file_name: str,
    *,
    settings: Settings | None = None,
) -> str:
    """按冻结 URL 规则拼出上传后的公网地址（**只拼字符串，不做任何网络调用**）。

    【FACT】``https://{bucket}.{normalizedEndpoint}/{objectName}``
       —— ``normalizedEndpoint`` = endpoint 去掉 ``^https?://`` 与尾部 ``/+``。
    """
    rules = OssUrlRules(settings)
    return rules.public_url(build_object_key(extension, file_name))


class OssUrlRules:
    """URL / object-key 规则（**只读**）。"""

    def __init__(self, settings: Settings | None = None) -> None:
        settings = settings or get_settings()
        self.base_url = settings.oss.public_base_url()          # https://kjc-blog-2026.oss-cn-beijing.aliyuncs.com
        self.bucket = settings.oss.bucket_name

    def public_url(self, object_key: str) -> str:
        """拼出公网 URL（复刻 ``AliOssUtil`` 的拼接方式，**不做归一化**）。"""
        return f"{self.base_url}/{object_key.lstrip('/')}"

    def extract_key(self, url: str) -> str | None:
        """从历史 URL 反推 object key（**只读**，用于登记与校验，不用于改写）。"""
        if not url:
            return None
        parsed = urlparse(url)
        if parsed.netloc and self.bucket not in parsed.netloc:
            # 【FORBIDDEN】不得把外部域名的 URL 改写成本 bucket 的 URL
            return None
        m = _OSS_URL_RE.match(url)
        return m.group("key") if m else None

    def is_oss_url(self, url: str) -> bool:
        return bool(url) and self.bucket in url and url.startswith("http")


def strip_oss_url_prefix(url: str) -> str:
    """去掉 ``https://{bucket}.{host}/``，返回 object key（保留原始大小写与转义）。"""
    m = _OSS_URL_RE.match(url or "")
    return m.group("key") if m else url


def extract_oss_key(url: str) -> str | None:
    """便捷函数：按**当前配置**提取 object key。"""
    return OssUrlRules().extract_key(url)
