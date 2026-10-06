"""配置系统 —— Pydantic Settings，全部凭据来自环境变量（ADR-006 / 本轮指令 §6）。

禁止事项（本轮指令 §6）：
  * 密码不得写入源码
  * JWT secret 不得写入 git
  * OSS access key 不得写入源码
  * 不提交真实凭据
  * ``.env.example`` 只允许出现变量名

设计约束（保持冻结设计，不重新定义）：
  * 【FACT】数据库为**单一 MySQL 库**（``TECHNICAL_ARCHITECTURE.md`` §6.1「同一实例、同一库」）
  * 【FACT】旧连接串 ``serverTimezone=GMT+8``、字符集 ``utf8mb4``
  * 【FACT】JWT：header 名 ``Authorization``、**裸 token 不剥离 Bearer**、TTL 7200000 ms、claims ``adminId``/``adminRole``
  * 【DECISION】Redis 新旧隔离 = 不同 db 号 和/或 不同 key 前缀；❌ 禁止 FLUSHDB / FLUSHALL
"""
from __future__ import annotations

import os
from functools import lru_cache
from urllib.parse import quote_plus

from pydantic import BaseModel, Field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict

__all__ = ["Settings", "get_settings"]


class DatabaseSettings(BaseModel):
    """单一 MySQL 库连接参数。

    注意：本项目**不存在** db_meta / db_dw 两个库（见 ``.env.example`` 顶部说明）。
    """

    host: str = "127.0.0.1"
    port: int = 3306
    user: str = ""
    password: SecretStr = SecretStr("")
    name: str = "feitwnd"
    # 【FACT】旧连接串：serverTimezone=GMT+8
    timezone: str = "+08:00"
    # 【FACT】utf8mb4 / utf8mb4_0900_ai_ci
    charset: str = "utf8mb4"

    def dsn(self, *, driver: str = "aiomysql") -> str:
        """构造 SQLAlchemy URL。

        ``driver``：
          * ``aiomysql``  → ``mysql+aiomysql://``（本阶段定版，纯 Python）
          * ``asyncmy``   → ``mysql+asyncmy://``（ADR-002 的另一备选）
          * ``pymysql``   → ``mysql+pymysql://``（同步；仅供离线工具）
        """
        user = quote_plus(self.user)
        pwd = quote_plus(self.password.get_secret_value())
        return (
            f"mysql+{driver}://{user}:{pwd}@{self.host}:{self.port}/{self.name}"
            f"?charset={self.charset}"
        )


class RedisSettings(BaseModel):
    host: str = "127.0.0.1"
    port: int = 6379
    password: SecretStr = SecretStr("")
    # 旧系统 database = 0（【FACT】application.yml）→ 新系统默认换库号实现隔离
    db: int = 1
    # 冻结命名空间前缀（TECHNICAL_ARCHITECTURE.md §7.2）
    key_prefix: str = "imcjk:"
    socket_timeout: float = 5.0


class JwtSettings(BaseModel):
    secret_key: SecretStr = SecretStr("")
    # 【FACT】feitwnd.jwt.ttl = 7200000（2h）；每次签发都重置 TTL
    ttl_ms: int = 7_200_000
    # 【FACT】feitwnd.jwt.token-name = Authorization；值为裸 token
    token_name: str = "Authorization"
    # 【UNKNOWN·U-01】旧算法未确认 → 默认按密钥长度推导，不写死
    algorithm: str = "auto"


class OssSettings(BaseModel):
    endpoint: str = "https://oss-cn-beijing.aliyuncs.com"
    access_key_id: SecretStr = SecretStr("")
    access_key_secret: SecretStr = SecretStr("")
    # D5 FROZEN：不换 bucket
    bucket_name: str = "kjc-blog-2026"

    def public_base_url(self) -> str:
        """【FACT】``https://{bucket}.{endpoint_host}``（``AliOssUtil`` 拼接规则）。"""
        host = self.endpoint.replace("https://", "").replace("http://", "").rstrip("/")
        return f"https://{self.bucket_name}.{host}"


class SmtpSettings(BaseModel):
    host: str = "smtp.qq.com"
    port: int = 587
    username: str = ""
    password: SecretStr = SecretStr("")
    from_addr: str = ""


class AppSettings(BaseModel):
    name: str = "imcjk-backend"
    # ADR-010：后端路由自带 /api 前缀（Nginx 透传）
    api_prefix: str = "/api"
    env: str = "development"

    @property
    def is_production(self) -> bool:
        return self.env.lower() in {"prod", "production"}


class LogSettings(BaseModel):
    level: str = "INFO"
    # ❌ 生产禁止 true（旧系统 mapper: debug 全量打印 SQL）
    sql_echo: bool = False


class VisitorSettings(BaseModel):
    """D1 FROZEN：游客固定验证码（保留旧行为，**不评估其安全性**）。"""

    verify_code: str = ""


class AuthSettings(BaseModel):
    """认证行为开关。

    ``lazy_rehash_enabled``：
      【DECISION·ADR-009】「把**密码首次升级**安排在切换稳定之后」——
      该缓解措施需要一个开关才能落地，因此显式提供（默认 **True** = 按 ADR-009 执行）。
      设为 False 时**登录行为完全不变**（只跳过写回，校验仍按 ``password_algo`` 分派）。
    """

    lazy_rehash_enabled: bool = True
    # 【FACT】验证码值域 000000~999999 / 长度 6
    verify_code_length: int = 6


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=os.environ.get("IMCJK_ENV_FILE", ".env"),
        env_file_encoding="utf-8",
        env_nested_delimiter="__",
        extra="ignore",
        case_sensitive=False,
    )

    database: DatabaseSettings = Field(default_factory=DatabaseSettings)
    redis: RedisSettings = Field(default_factory=RedisSettings)
    jwt: JwtSettings = Field(default_factory=JwtSettings)
    oss: OssSettings = Field(default_factory=OssSettings)
    smtp: SmtpSettings = Field(default_factory=SmtpSettings)
    app: AppSettings = Field(default_factory=AppSettings)
    log: LogSettings = Field(default_factory=LogSettings)
    visitor: VisitorSettings = Field(default_factory=VisitorSettings)
    auth: AuthSettings = Field(default_factory=AuthSettings)

    def require_production_secrets(self) -> list[str]:
        """返回缺失的必填凭据项（**不抛异常**，供启动自检使用）。

        仅在 ``app.env`` 为生产时调用。Phase 2.1 不连生产，因此契约测试不会触发。
        """
        missing: list[str] = []
        if not self.database.password.get_secret_value():
            missing.append("DATABASE__PASSWORD")
        if not self.jwt.secret_key.get_secret_value():
            missing.append("JWT__SECRET_KEY")
        if not self.oss.access_key_id.get_secret_value():
            missing.append("OSS__ACCESS_KEY_ID")
        if not self.oss.access_key_secret.get_secret_value():
            missing.append("OSS__ACCESS_KEY_SECRET")
        if not self.redis.password.get_secret_value():
            missing.append("REDIS__PASSWORD")
        return missing


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """进程内单例。测试可用 ``get_settings.cache_clear()`` 重置。"""
    return Settings()
