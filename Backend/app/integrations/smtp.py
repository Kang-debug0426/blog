"""SMTP 适配器 —— **Phase 2.1 只定义接口边界，不做真实发送。**

【FACT】旧系统 ``EmailService`` / ``EmailServiceImpl`` 用 ``spring.mail``（smtp.qq.com:587）
       发送 6 位数字验证码。
【DECISION】新系统保留该机制（不得删除 sendCode 端点 → 属 119 端点之一）。
【本轮范围·§31】不做真实发送 → 本模块提供 ``EmailSender`` 协议 + 一个**未实现**的
       ``SmtpEmailSender``，其 ``send_verify_code`` 抛 ``EmailSendErrorException``
       （即「未接线」是**显式失败**，绝不静默成功 —— 避免掩盖未实现）。
"""
from __future__ import annotations

from typing import Protocol
import asyncio
import smtplib
from email.mime.text import MIMEText
from email.header import Header
from email.utils import formataddr

from app.core.errors import EmailSendErrorException

__all__ = ["EmailSender", "SmtpEmailSender", "NullEmailSender"]


class EmailSender(Protocol):
    """发送验证码的最小 seam。"""

    async def send_verify_code(self, to_addr: str, code: str) -> None: ...


class SmtpEmailSender:
    """真实 SMTP 发信实现（支持 QQ 邮箱等标准 STARTTLS/SSL 协议）。"""

    def __init__(self, *, host: str, port: int, username: str, password: str, from_addr: str) -> None:
        self._host = host
        self._port = port
        self._username = username
        self._password = password
        self._from_addr = from_addr or username

    async def send_verify_code(self, to_addr: str, code: str) -> None:
        if not self._password or not self._username:
            raise EmailSendErrorException("SMTP 凭据未配置：请在 .env 中设置 SMTP__USERNAME 与 SMTP__PASSWORD")

        def _sync_send() -> None:
            msg = MIMEText(
                f"【IMCJK】您的后台管理验证码为：{code}，5分钟内有效。如非本人操作请忽略此邮件。",
                "plain",
                "utf-8"
            )
            msg["From"] = formataddr(("IMCJK系统通知", self._from_addr))
            msg["To"] = to_addr
            msg["Subject"] = Header("【IMCJK】管理员登录验证码", "utf-8")

            if self._port == 465:
                with smtplib.SMTP_SSL(self._host, self._port, timeout=10) as server:
                    server.login(self._username, self._password)
                    server.sendmail(self._from_addr, [to_addr], msg.as_string())
            else:
                with smtplib.SMTP(self._host, self._port, timeout=10) as server:
                    server.starttls()
                    server.login(self._username, self._password)
                    server.sendmail(self._from_addr, [to_addr], msg.as_string())

        try:
            await asyncio.to_thread(_sync_send)
        except Exception as e:
            raise EmailSendErrorException(f"SMTP 邮件发送失败: {e}") from e


class NullEmailSender:
    """测试替身：记录被发送的验证码，便于契约测试断言。

    ❗ 仅用于测试与本地开发；生产环境由 ``app.main`` 依据配置显式选择。
    """

    def __init__(self) -> None:
        self.sent: list[tuple[str, str]] = []

    async def send_verify_code(self, to_addr: str, code: str) -> None:
        self.sent.append((to_addr, code))
