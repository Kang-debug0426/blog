"""日志配置。

复刻约束：
  * 【FACT】旧系统 ``logging.level.cc.feitwnd.mapper = debug``（**全量打印 SQL**）
    → 【DECISION】新系统生产**必须 INFO**，禁止 ``mapper: debug``（``TECHNICAL_ARCHITECTURE.md`` §5.6）
  * 【本轮指令 §27】不得记录：password / salt / JWT secret / OSS access key / 完整 token
  * 【FACT】旧系统日志里出现过登录/改密参数（``log.info("管理员登录：{}", dto)``）
    → 新系统**不打印整个 DTO**，只打印用户名等非敏感标识（脱敏语义见 ``redact_*``）
"""
from __future__ import annotations

import logging
import sys
from typing import Any

_FORMAT = "%(asctime)s %(levelname)s [%(name)s] %(message)s"
_DATEFMT = "%Y-%m-%d %H:%M:%S"

_SENSITIVE_KEYS = frozenset(
    {
        "password",
        "newpassword",
        "confirmnewpassword",
        "oldpassword",
        "salt",
        "token",
        "secret",
        "secretkey",
        "accesskeyid",
        "accesskeysecret",
        "authorization",
    }
)


def setup_logging(level: str = "INFO") -> None:
    """初始化 root logger。生产用 INFO，禁止把级别降到 DEBUG 打 SQL。"""
    root = logging.getLogger()
    root.setLevel(getattr(logging, level.upper(), logging.INFO))
    for handler in list(root.handlers):
        root.removeHandler(handler)
    handler = logging.StreamHandler(stream=sys.stdout)
    handler.setFormatter(logging.Formatter(_FORMAT, datefmt=_DATEFMT))
    root.addHandler(handler)
    # SQLAlchemy 引擎日志：不随 root 一起降级（避免变相开启 SQL 全量打印）
    logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)
    logging.getLogger("aiomysql").setLevel(logging.WARNING)


def get_logger(name: str) -> logging.Logger:
    return logging.getLogger(name)


def redact_token(token: str | None) -> str:
    """token 只保留前缀与长度，绝不整体落日志（本轮指令 §27）。"""
    if not token:
        return "<absent>"
    return f"<token:{len(token)}ch:{token[:6]}…>"


def redact_mapping(data: dict[str, Any]) -> dict[str, Any]:
    """按 key 名脱敏，用于打印入参 dict（替代旧系统直接打印整个 DTO）。"""
    out: dict[str, Any] = {}
    for key, value in data.items():
        if key.replace("_", "").lower() in _SENSITIVE_KEYS:
            out[key] = "***"
        else:
            out[key] = value
    return out
