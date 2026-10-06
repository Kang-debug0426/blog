"""``auth`` 模块契约 —— 对应旧 ``AdminController`` / ``AdminLoginDTO`` / ``*VO``。

【FACT】DTO / VO 字段（字节码 + 反编译确认）::

    AdminLoginDTO     { username, password, code }        三者 @NotBlank
    SendCodeDTO       { username }                        **无 @NotBlank**（旧代码未校验！）
    AdminLogoutDTO    { id, token }                       **无 @Valid**
    AdminLoginVO      { id, token }
    AdminVO           { id, nickname, email }

⚠️ **不擅自"补校验"**（本轮指令 §5「不增加业务功能」）：
   * ``SendCodeDTO`` 只有 1 个字段且**没有**校验注解 → 新系统也**不加**
     （旧行为：username 为 null 时进 service 后 ``getByUsername(null)`` → 查不到 → "账号不存在"）
   * ``AdminLogoutDTO`` 同样**不加**校验

【FACT】@Valid 失败的响应（``GlobalExceptionHandler``）::

    HTTP 400
    {code: 0, msg: "字段名: 消息; 字段名: 消息", data: null}
    // 消息文本 = @NotBlank 的 message，逐字为：
    //   username → "用户名不能为空"
    //   password → "密码不能为空"
    //   code     → "验证码不能为空"
"""
from __future__ import annotations
from pydantic import Field

from typing import Any

from pydantic import BaseModel, ConfigDict, ValidationInfo, field_validator

from app.core.legacy_types import LegacyDateTime

__all__ = [
    "AdminLoginDTO",
    "SendCodeDTO",
    "AdminLogoutDTO",
    "AdminLoginVO",
    "AdminVO",
    "NOT_BLANK_MESSAGES",
]

# 【FACT】@NotBlank(message = ...) 的逐字文本
NOT_BLANK_MESSAGES: dict[str, str] = {
    "username": "用户名不能为空",
    "password": "密码不能为空",
    "code": "验证码不能为空",
}


class _NotBlankMixin(BaseModel):
    """复刻 Jakarta ``@NotBlank``：null / ``""`` / 纯空白 均判失败。

    ⚠️ **必须用字段级** ``field_validator``，不能用 ``model_validator(mode="before")``：
       后者的错误 ``loc`` 是**整个 body（空）**，最终报文会变成
       ``unknown: 用户名不能为空`` —— 而旧系统是 ``username: 用户名不能为空``（字段名来自
       ``FieldError.getField()``）。字段级校验器的 ``loc == ("username",)``，逐字对齐。

    ⚠️ ``validate_default=True`` 不可省：字段**缺失**时 Pydantic 默认**不跑**校验器、
       直接取默认值 ``None``，于是会绕过校验、把 ``None`` 传进 service →
       最终报「账号不存在」而不是「400 用户名不能为空」—— **行为回归**。
       开启后，缺失字段同样进入校验器并抛错。

    ⚠️ 用自定义校验而非 ``Field(min_length=1)``：后者的英文默认消息
       （``String should have at least 1 character``）会破坏旧契约文案。
    """

    model_config = ConfigDict(
        extra="ignore",  # 【FACT】JacksonObjectMapper 关闭了 FAIL_ON_UNKNOWN_PROPERTIES
        validate_default=True,
    )

    @field_validator("username", "password", "code", mode="before", check_fields=False)
    @classmethod
    def _not_blank(cls, value: Any, info: ValidationInfo) -> Any:
        message = NOT_BLANK_MESSAGES.get(str(info.field_name))
        if message is None:  # pragma: no cover - 防御
            return value
        if value is None or (isinstance(value, str) and value.strip() == ""):
            raise ValueError(message)
        return value


class AdminLoginDTO(_NotBlankMixin):
    """``POST /admin/admin/login`` 的入参。"""

    username: str | None = None
    password: str | None = None
    code: str | None = None


class SendCodeDTO(BaseModel):
    """``POST /admin/admin/sendCode`` 的入参。

    【FACT】Java 侧**无校验注解** → 此处**不加**（保持行为等价）。
    """

    model_config = ConfigDict(extra="ignore")

    username: str | None = None


class AdminLogoutDTO(BaseModel):
    """``POST /admin/admin/logout`` 的入参。【FACT】Java 侧**无 @Valid**。"""

    model_config = ConfigDict(extra="ignore")

    id: int | None = None
    token: str | None = None


class AdminLoginVO(BaseModel):
    """【FACT】字段顺序：id, token。"""

    model_config = ConfigDict(extra="forbid")

    id: int | None = None
    token: str | None = None


class AdminVO(BaseModel):
    """【FACT】字段顺序：id, nickname, email。"""

    model_config = ConfigDict(extra="forbid")

    id: int | None = None
    nickname: str | None = None
    email: str | None = None


# 【FACT】未使用但登记：AdminVO 不含 createTime/updateTime（旧 build 只填 3 个字段）
_ = LegacyDateTime


class AdminChangePasswordDTO(BaseModel):
    from pydantic import Field
    old_password: str | None = Field(default=None, alias='oldPassword')
    new_password: str | None = Field(default=None, alias='newPassword')
    code: str | None = None

class AdminChangeNicknameDTO(BaseModel):
    nickname: str | None = None

class AdminChangeEmailDTO(BaseModel):
    new_email: str | None = Field(default=None, alias='newEmail')
    code: str | None = None
