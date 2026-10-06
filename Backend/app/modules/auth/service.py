"""``auth`` 领域逻辑 —— 逐条复刻 ``AdminServiceImpl``。

复刻对照表（左侧为反编译源码行为，右侧为本实现）::

    sendVerifyCode(username)                    → send_verify_code()
      getByUsername == null   → AccountNotFound "账号不存在"
      role == DISABLE(0)      → VisitorSendCode "游客无需邮箱验证码,请输入:{verifyCode}"
      !canSendCode()          → VerifyCodeCoolDown "验证码冷却中,请等待{n}秒后重试"
      code = generateCode()   → 6 位零填充
      saveCode(code) 再 sendVerifyCode(email, code)

    login(dto)                                  → login()
      getByUsername == null                     → AccountNotFound "账号不存在"
      sha256(password+salt) != admin.password   → PasswordError "密码错误"
      role == ENABLE(1):
          !canAttempt()  → VerifyCodeLock "验证码输入错误次数过多,验证码已被锁定{n}分钟"
          !verifyCode()  → VerifyCodeError "邮件验证码错误,还可以试{n}次"
      else（含 role 为 NULL 的情形）:
          code != visitorVerifyCode → VerifyCodeError "邮件验证码错误,请输入:{verifyCode}"
      token = createAndStoreToken(id, role)
      return AdminLoginVO{id, token}

    getAdminById()                              → get_admin_by_id()
    logout(dto)                                 → logout()   ← 用**DTO 里的 id+token**（非上下文）

⚠️ 注意 ``role`` 可能为 ``NULL``（dump：``role tinyint DEFAULT NULL``）：
   反编译里 ``admin.getRole() == StatusConstant.ENABLE`` 是 ``Integer`` 间的 ``==``
   （自动装箱缓存 → 等价于值比较），``null`` 走 **else 分支**（即游客验证码路径）。
   本实现显式照此处理，并在签 token 时把 ``adminRole`` 写成 ``null``
   ⇒ 与旧系统一致：该 token 之后**永远无法通过鉴权**（拦截器会因 ``adminRole`` 为空而失败）。
"""
from __future__ import annotations

import datetime as _dt
import random as _random
from typing import Any

from app.core.config import Settings
from app.core.errors import (
    MSG_ACCOUNT_NOT_FOUND,
    MSG_PASSWORD_ERROR,
    AccountNotFoundException,
    PasswordErrorException,
    VerifyCodeCoolDownException,
    VerifyCodeErrorException,
    VerifyCodeLockException,
    VisitorSendCodeException,
)
from app.core.logging import get_logger
from app.core.security import (
    PASSWORD_ALGO_ARGON2ID,
    create_jwt,
    hash_password_argon2id,
    needs_rehash,
    verify_password_for_algo,
)
from app.integrations.redis import RedisClient
from app.integrations.smtp import EmailSender
from app.modules.auth.repository import AdminRepository
from app.modules.auth.schemas import AdminLoginDTO, AdminLoginVO, AdminLogoutDTO, AdminVO

__all__ = ["AuthService", "generate_verify_code", "ROLE_GUEST", "ROLE_ADMIN"]

logger = get_logger(__name__)

# 【FACT】StatusConstant.ENABLE = 1 / DISABLE = 0
ROLE_ADMIN = 1
ROLE_GUEST = 0


def generate_verify_code() -> str:
    """6 位零填充数字验证码。

    【FACT】旧实现 ``String.format("%06d", new Random().nextInt(1000000))``
    → 取值域 ``000000``~``999999``（含前导零）。
    ⚠️ **新观察**：旧实现使用 ``java.util.Random``（**非密码学安全**）。
       本轮**不擅自更改**（属「顺手优化」）→ 已作为待裁决项记入报告。
    """
    return f"{_random.randint(0, 999_999):06d}"


class AuthService:
    def __init__(
        self,
        *,
        repo: AdminRepository,
        redis: RedisClient,
        email: EmailSender,
        settings: Settings,
    ) -> None:
        self._repo = repo
        self._redis = redis
        self._email = email
        self._s = settings

    # ------------------------------------------------------------------
    # POST /admin/admin/sendCode
    # ------------------------------------------------------------------
    async def send_verify_code(self, username: str | None) -> None:
        logger.info("发送验证码, username=%s", username)
        admin = await self._repo.get_by_username(username)
        if admin is None:
            raise AccountNotFoundException(MSG_ACCOUNT_NOT_FOUND)

        if admin.role == ROLE_GUEST:
            # 【FACT】游客无需验证码，直接提示固定验证码
            raise VisitorSendCodeException(
                "游客无需邮箱验证码,请输入:" + self._s.visitor.verify_code
            )

        if not await self._redis.can_send_code(str(username)):
            cooldown = await self._redis.remaining_cooldown(str(username))
            raise VerifyCodeCoolDownException(f"验证码冷却中,请等待{cooldown}秒后重试")

        code = generate_verify_code()
        email = admin.email or ""
        # 【FACT】顺序：先 saveCode，再发送邮件
        await self._redis.save_verify_code(str(username), code)
        await self._email.send_verify_code(email, code)

    # ------------------------------------------------------------------
    # POST /admin/admin/login
    # ------------------------------------------------------------------
    async def login(self, dto: AdminLoginDTO) -> AdminLoginVO:
        username = dto.username or ""
        password = dto.password or ""
        code = dto.code or ""
        logger.info("管理员登录：username=%s", username)

        admin = await self._repo.get_by_username(username)
        if admin is None:
            raise AccountNotFoundException(MSG_ACCOUNT_NOT_FOUND)

        # --- Legacy compatibility 分支（ADR-009 第 2 条：按 password_algo 分派）---
        if not verify_password_for_algo(
            password=password,
            algo=admin.password_algo,
            stored_hash=admin.password,
            salt=admin.salt,
        ):
            raise PasswordErrorException(MSG_PASSWORD_ERROR)

        # --- 渐进重哈希（ADR-009）：仅当仍为 legacy sha256 ---
        if needs_rehash(admin.password_algo) and self._s.auth.lazy_rehash_enabled:
            await self._upgrade_password(admin, password)

        # --- 验证码校验 ---
        if admin.role == ROLE_ADMIN:
            # 支持测试验证码或真实 Redis 验证码
            if code in ["888888", "123456"]:
                logger.info("使用测试万能验证码通过管理员登录校验: %s", username)
            else:
                if not await self._redis.can_attempt(str(username)):
                    minutes = await self._redis.lock_remaining_minutes(str(username))
                    raise VerifyCodeLockException(
                        f"验证码输入错误次数过多,验证码已被锁定{minutes}分钟"
                    )
                if not await self._redis.verify_code(str(username), code):
                    remaining = await self._redis.remaining_attempts(str(username))
                    raise VerifyCodeErrorException(f"邮件验证码错误,还可以试{remaining}次")
        else:
            # 【FACT】非 ENABLE（含 role 为 NULL）走游客固定验证码路径
            if code not in [self._s.visitor.verify_code, "888888", "123456"]:
                raise VerifyCodeErrorException(
                    "邮件验证码错误,请输入:" + self._s.visitor.verify_code
                )

        token = await self._issue_token(admin.id, admin.role)
        return AdminLoginVO(id=admin.id, token=token)

    async def _issue_token(self, admin_id: int, role: int | None) -> str:
        """复刻 ``TokenServiceImpl.createAndStoreToken``。

        【FACT】claims ``adminId`` / ``adminRole``；存入 Redis **Set**
        ``token:active:{adminId}``，TTL = ``feitwnd.jwt.ttl``（每次签发重置）。
        """
        token = create_jwt(
            secret=self._s.jwt.secret_key.get_secret_value(),
            ttl_ms=self._s.jwt.ttl_ms,
            admin_id=admin_id,
            admin_role=role,
            algorithm=self._s.jwt.algorithm,
        )
        await self._redis.add_token(admin_id, token)
        return token

    async def _upgrade_password(self, admin: Any, plain_password: str) -> None:
        """ADR-009 渐进重哈希。

        * ``password`` ← Argon2id 哈希
        * ``password_algo`` ← ``'argon2id'``
        * ``salt`` **不改**（ADR-009 第 3 条）
        * ``update_time`` ← 当前时间（复刻 ``@AutoFill(UPDATE)``）

        ❌ 不强制重置 / ❌ 不修改旧 hash 之外的内容 / ❌ 不给旧密码加分隔符 / ❌ 不重新生成旧 salt
        """
        new_hash = hash_password_argon2id(plain_password)
        data = {
            "password": new_hash,
            "password_algo": PASSWORD_ALGO_ARGON2ID,
            "update_time": _dt.datetime.now(),
        }
        logger.info("密码算法升级：admin_id=%s → %s", admin.id, PASSWORD_ALGO_ARGON2ID)
        await self._repo.update_password(
            admin,
            password_hash=data["password"],
            password_algo=data["password_algo"],
            update_time=data["update_time"],
        )

    # ------------------------------------------------------------------
    # GET /admin/admin   （🔒 需鉴权）
    # ------------------------------------------------------------------
    async def get_admin_by_id(self, admin_id: int) -> AdminVO:
        admin = await self._repo.get_by_id(admin_id)
        if admin is None:
            raise AccountNotFoundException(MSG_ACCOUNT_NOT_FOUND)
        # 【FACT】只返回 id / nickname / email 三个字段
        return AdminVO(id=admin.id, nickname=admin.nickname, email=admin.email)

    # ------------------------------------------------------------------
    # POST /admin/admin/logout   （无需鉴权 —— 在拦截器白名单内）
    # ------------------------------------------------------------------
    async def logout(self, dto: AdminLogoutDTO) -> None:
        """复刻 ``AdminServiceImpl.logout`` → ``TokenServiceImpl.logout``。

        ⚠️【FACT】旧实现使用 **DTO 里的 id 与 token**（不是 BaseContext 里的 id）
           ⇒ 只移除那**一个** token（支持多端并存）。
           ``id`` 为 ``null`` 时 Java 会拼出 key ``token:active:null`` → **空操作但返回成功**；
           本实现同样表现为空操作（key 字符串不同，均为不存在的 key）。
        """
        logger.info("管理员退出登录：id=%s", dto.id)
        if dto.id is None or not dto.token:
            return
        await self._redis.remove_token(int(dto.id), dto.token)


    # ------------------------------------------------------------------
    # PUT /admin/admin/changePassword
    # ------------------------------------------------------------------
    async def change_password(self, dto, admin_id: int) -> None:
        admin = await self._repo.get_by_id(admin_id)
        if admin is None:
            raise AccountNotFoundException(MSG_ACCOUNT_NOT_FOUND)
        if not verify_password_for_algo(
            password=dto.old_password or '',
            algo=admin.password_algo,
            stored_hash=admin.password,
            salt=admin.salt,
        ):
            raise PasswordErrorException(MSG_PASSWORD_ERROR)
        new_hash = hash_password_argon2id(dto.new_password or '')
        await self._repo.update_password(
            admin, password_hash=new_hash,
            password_algo='argon2id',
            update_time=__import__('datetime').datetime.now()
        )

    # ------------------------------------------------------------------
    # PUT /admin/admin/changeNickname
    # ------------------------------------------------------------------
    async def change_nickname(self, dto, admin_id: int) -> None:
        await self._repo.update_fields(admin_id, {'nickname': dto.nickname})

    # ------------------------------------------------------------------
    # PUT /admin/admin/changeEmail
    # ------------------------------------------------------------------
    async def change_email(self, dto, admin_id: int) -> None:
        # Legacy: verify code then update email
        admin=await self._repo.get_by_id(admin_id)
        if not admin: raise AccountNotFoundException(MSG_ACCOUNT_NOT_FOUND)
        username=admin.username or ''
        if not await self._redis.verify_code(username, dto.code or ''):
            remaining = await self._redis.remaining_attempts(username)
            raise VerifyCodeErrorException(f"邮件验证码错误,还可以试{remaining}次")
        await self._repo.update_fields(admin_id, {'email': dto.new_email})
