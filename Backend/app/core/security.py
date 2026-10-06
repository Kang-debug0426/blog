"""安全层 —— 密码哈希与 JWT。**本阶段兼容性风险最高的两个文件之一。**

复刻来源（全部为【FACT】，字节码确认）：
  * ``cc/feitwnd/service/impl/EncryptPasswordServiceImpl``（R2 已关闭）
  * ``common-src/cc/feitwnd/utils/JwtUtil``
  * ``common-src/cc/feitwnd/constant/JwtClaimsConstant``
  * ``docs/adr/ADR-009-password-hashing.md``

—— 密码 ——

【FACT】Legacy（存量的 1 行账号）：``sha256(UTF-8(password + salt))`` → **小写 hex / 64 字符 / 单轮**
        拼接**无分隔符**（**既有缺陷，复刻时不得擅自加分隔符**）。
【DECISION·ADR-009】New password storage = **Argon2id**（``argon2-cffi``）。
        仅在 **Legacy 校验成功后**做渐进重哈希（lazy rehash），并把 ``password_algo`` 置为 ``argon2id``。
        ``salt`` 列**保留不删**（升级后不再使用）→ 保证回滚到旧后端仍可读（ADR-004「只做加法」）。

—— JWT ——

【FACT】claims 为 ``adminId`` / ``adminRole``；``Authorization`` 头里是**裸 token**（**不剥离 Bearer**）；
       TTL = 7200000 ms，每次签发重置；token 存入 Redis **Set** ``token:active:{adminId}``。
【UNKNOWN·U-01】旧 token 的**具体算法**（HS256/384/512）无法确认 —— 旧 ``secret-key`` 在
       分析产物中已脱敏（``<REDACTED>``）。
       ⇒ 本实现**不写死算法**：默认 ``auto``，按 secret 的**字节长度**推导，
          与 jjwt ``Keys.hmacShaKeyFor`` 的语义一致（**标记为【INFERENCE·高置信】**）。
       ⇒ 【DECISION】不构成 STOP-08：冻结结论是 **token 不迁移**（``REDIS_MIGRATION_DESIGN`` §4），
          新系统自行签发新 token，因此**不需要**解析旧 token，
          「无法复刻旧签名」不影响任何交付物。
"""
from __future__ import annotations

import hashlib
import time
from dataclasses import dataclass
from typing import Any

import jwt as pyjwt
from argon2 import PasswordHasher
from argon2.exceptions import InvalidHashError, VerifyMismatchError

from app.core.errors import WeakJwtSecretError

__all__ = [
    "PASSWORD_ALGO_LEGACY",
    "PASSWORD_ALGO_ARGON2ID",
    "legacy_hash_password",
    "verify_legacy_password",
    "hash_password_argon2id",
    "verify_argon2id_password",
    "hash_password_for_algo",
    "verify_password_for_algo",
    "needs_rehash",
    "resolve_hmac_algorithm",
    "create_jwt",
    "parse_jwt",
    "JwtPayload",
]

# ---------------------------------------------------------------------------
# 密码
# ---------------------------------------------------------------------------
PASSWORD_ALGO_LEGACY = "sha256"
PASSWORD_ALGO_ARGON2ID = "argon2id"

# ADR-009：参数需按 1.6 GB RAM 服务器实测标定 → 此处给出**保守默认**，Phase 2 标定后可调
#   （不改变契约，只影响耗时与内存）
_ARGON2 = PasswordHasher(
    time_cost=2,
    memory_cost=19_456,  # 19 MiB，OWASP 2024 最低推荐档
    parallelism=1,
    hash_len=32,
    salt_len=16,
)


def legacy_hash_password(password: str, salt: str) -> str:
    """复刻旧系统密码哈希。

    【FACT】``MessageDigest.getInstance("SHA-256")``，输入 ``password + salt``（无分隔符），
    UTF-8 编码，单轮；输出由手工 ``bytesToHex`` 产生（单字符补 ``0``）
    ⇒ 等价于 Python ``hashlib.sha256(...).hexdigest()``：**小写、64 字符**。

    ❌ 不得加入任何分隔符 / 盐轮换 / 迭代次数（那会**改变既有事实**）。
    """
    return hashlib.sha256((password + salt).encode("utf-8")).hexdigest()


def verify_legacy_password(password: str, salt: str, expected_hash: str) -> bool:
    """**Legacy compatibility 分支**（仅为兼容存量账号而保留的校验）。

    【FACT】旧代码用 ``String.equals`` → 大小写敏感；此处保持一致（不做 lower 归一化）。
    """
    if not expected_hash:
        return False
    return legacy_hash_password(password, salt) == expected_hash


def hash_password_argon2id(password: str) -> str:
    """New password storage（新系统唯一推荐存储方案）。"""
    return _ARGON2.hash(password)


def verify_argon2id_password(password: str, stored_hash: str) -> bool:
    try:
        return _ARGON2.verify(stored_hash, password)
    except (VerifyMismatchError, InvalidHashError, ValueError):
        return False


def hash_password_for_algo(password: str, algo: str, salt: str | None) -> str:
    """按 ``password_algo`` 生成**新**哈希（用于改密 / 渐进重哈希）。

    * ``sha256``   → 仅在「必须保持旧算法」的极端回滚场景使用
    * ``argon2id`` → 默认（ADR-009）
    """
    if algo == PASSWORD_ALGO_LEGACY:
        return legacy_hash_password(password, salt or "")
    return hash_password_argon2id(password)


def verify_password_for_algo(
    *, password: str, algo: str | None, stored_hash: str, salt: str
) -> bool:
    """**登录校验的唯一入口**（ADR-009 第 2 条的分派逻辑）。

    ``algo`` 为 ``NULL`` / ``NULL 以外的未知值`` 时**按 legacy 处理**：
    【FACT】迁移前该列不存在，默认值为 ``'sha256'``（``admin.password_algo`` NOT NULL DEFAULT 'sha256'）。
    对未知值保守回退到 legacy，与「迁移阶段不改变数据语义」一致。
    """
    if algo == PASSWORD_ALGO_ARGON2ID:
        return verify_argon2id_password(password, stored_hash)
    if algo in (None, "", PASSWORD_ALGO_LEGACY):
        return verify_legacy_password(password, salt, stored_hash)
    # 未知算法标识 → 保守回退 legacy（不抛异常，避免把未知值变成登录失败）
    return verify_legacy_password(password, salt, stored_hash)


def needs_rehash(algo: str | None) -> bool:
    """是否应在**校验成功后**做渐进重哈希。

    【DECISION·ADR-009】仅当仍为 legacy ``sha256`` 时升级；``argon2id`` 不重复升级。
    ❌ 不得强制重置密码 / 修改旧 hash / 修改 salt。
    """
    return algo in (None, "", PASSWORD_ALGO_LEGACY)


# ---------------------------------------------------------------------------
# JWT
# ---------------------------------------------------------------------------
# 【INFERENCE·高置信】jjwt ``Keys.hmacShaKeyFor(byte[])``：
#   * 要求密钥 >= 256 bit（32 字节），否则抛 ``WeakKeyException``
#   * 按字节长度选择 JWA 算法：>=64B → HS512 / >=48B → HS384 / >=32B → HS256
# ⚠️ 该分支条件**未经字节码验证**（jjwt jar 未从备份中提取）→ 标记 INFERENCE。
#    如需精确对齐，Phase 2 可从 fat jar 提取 jjwt 后复核；也可在 .env 显式指定 JWT__ALGORITHM。
_JWT_ALGO_BY_MIN_LEN: tuple[tuple[int, str], ...] = ((64, "HS512"), (48, "HS384"), (32, "HS256"))


def resolve_hmac_algorithm(secret: str, configured: str = "auto") -> str:
    """解析签名算法。

    ``configured``：
      * ``auto``（默认）→ 按 secret 字节长度推导（jjwt 语义）
      * ``HS256`` / ``HS384`` / ``HS512`` → 显式使用

    ❌ 不得在文档/日志中把 ``auto`` 的结果**断言为已确认事实**（U-01 仍为 UNKNOWN）。
    """
    if configured and configured.lower() != "auto":
        algo = configured.upper()
        if algo not in {"HS256", "HS384", "HS512"}:
            raise ValueError(f"不支持的 JWT 算法：{configured}")
        return algo
    n = len(secret.encode("utf-8"))
    for min_len, algo in _JWT_ALGO_BY_MIN_LEN:
        if n >= min_len:
            return algo
    raise WeakJwtSecretError(
        f"JWT secret 过短（{n * 8} bit < 256 bit）—— jjwt Keys.hmacShaKeyFor 会抛 WeakKeyException"
    )


@dataclass(frozen=True, slots=True)
class JwtPayload:
    admin_id: int
    admin_role: int
    claims: dict[str, Any]


def create_jwt(
    *,
    secret: str,
    ttl_ms: int,
    admin_id: int,
    admin_role: int | None,
    algorithm: str = "auto",
) -> str:
    """复刻 ``JwtUtil.createJWT``。

    【FACT】claims 只有 ``adminId`` / ``adminRole``（``JwtClaimsConstant``），
           并通过 ``.expiration(exp)`` 写入标准 ``exp``。
    ⚠️ ``admin_role`` 允许为 ``None``：``admin.role`` 在库中可 NULL，
       旧系统会把 ``adminRole: null`` 写进 token（该 token 之后必然鉴权失败）——
       此处**保持一致**，不"修正"为 0 或 1。
    """
    algo = resolve_hmac_algorithm(secret, algorithm)
    now_ms = int(time.time() * 1000)
    payload: dict[str, Any] = {
        # 【FACT】JwtClaimsConstant.ADMIN_ID = "adminId" / ADMIN_ROLE = "adminRole"
        "adminId": admin_id,
        "adminRole": admin_role,
        "iat": now_ms // 1000,
        "exp": (now_ms + ttl_ms) // 1000,
    }
    return pyjwt.encode(payload, secret, algorithm=algo)


def parse_jwt(*, secret: str, token: str, algorithm: str = "auto") -> JwtPayload:
    """复刻 ``JwtUtil.parseJWT``（校验签名 + ``exp``）。

    失败时抛 ``pyjwt`` 系列异常 —— 由调用方（``deps`` / 拦截器兼容层）
    统一转换为 ``UnauthorizedException`` → 401（复刻字节码里的 ``catch (Exception)`` 分支）。
    """
    algo = resolve_hmac_algorithm(secret, algorithm)
    claims = pyjwt.decode(token, secret, algorithms=[algo])
    admin_id = claims.get("adminId")
    admin_role = claims.get("adminRole")
    if admin_id is None or admin_role is None:
        raise pyjwt.InvalidTokenError(f"缺少必需 claim：adminId/adminRole（实际 claims={sorted(claims)}）")
    return JwtPayload(admin_id=int(admin_id), admin_role=int(admin_role), claims=claims)
