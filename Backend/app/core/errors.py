"""统一响应信封 + 异常体系 + 全局异常处理。

**这是本阶段兼容性风险最高的两个文件之一**（另一个是 ``security.py``）。

复刻来源（全部为【FACT】，来自反编译源码字节码）：
  * ``cc/feitwnd/result/Result.java``          → ``{code, msg, data}``，成功 ``code=1``
  * ``cc/feitwnd/result/PageResult.java``      → ``{total, records}``
  * ``cc/feitwnd/handler/GlobalExceptionHandler.java`` → 异常 → HTTP 状态码映射
  * ``common-src/.../exception/*.java``        → 18 个异常类的继承链
  * ``cc/feitwnd/json/JacksonObjectMapper.java`` → 日期格式

【FACT】继承链（字节码确认）::

    RuntimeException
    ├── BaseException                → JSON 200 + {code:0}          （业务异常）
    │   ├── AccountNotFoundException / PasswordErrorException / ArticleException /
    │   │   VerifyCodeCoolDownException / VerifyCodeErrorException /
    │   │   VerifyCodeLockException / VisitorSendCodeException /
    │   │   EmailSendErrorException / UploadFileErrorException /
    │   │   RssSubscriptionException / SystemConfigException / ValidationException
    ├── TokenException               → 401 + {code:0}
    │   ├── NotLoginException（无 token）
    │   └── UnauthorizedException（token 无效/会员状态失效）
    ├── BlockedException             → 403 + {code:0}   （封禁；不继承 BaseException！）
    └── GuestReadOnlyException       → 403 + {code:0}   （游客只读；不继承 BaseException！）

⚠️ 注意 ``BlockedException`` / ``GuestReadOnlyException`` 直接继承 ``RuntimeException``，
   因此**不会**被 ``BaseException`` 处理器捕获 —— 复刻时必须给出各自的处理器，
   否则会错误落到 500。
"""
from __future__ import annotations

from typing import Any

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from pydantic import BaseModel, ConfigDict
from starlette.exceptions import HTTPException as StarletteHTTPException

__all__ = [
    "Envelope",
    "PageResult",
    "LegacyJSONResponse",
    "FIELD_ERROR_SEPARATOR",
    "BaseException",
    "TokenException",
    "NotLoginException",
    "UnauthorizedException",
    "BlockedException",
    "GuestReadOnlyException",
    "AccountNotFoundException",
    "PasswordErrorException",
    "ArticleException",
    "VerifyCodeCoolDownException",
    "VerifyCodeErrorException",
    "VerifyCodeLockException",
    "VisitorSendCodeException",
    "EmailSendErrorException",
    "UploadFileErrorException",
    "RssSubscriptionException",
    "SystemConfigException",
    "ValidationException",
    "DuplicateEntryException",
    "register_exception_handlers",
]


# ===========================================================================
# 1) 响应信封
# ===========================================================================
class Envelope(BaseModel):
    """复刻 ``Result<T>``。

    【FACT】Java 侧 ``Result.success()`` **只设 code，不设 msg**
    → 序列化结果里 ``msg`` 为 ``null``（Jackson 默认 ``Include.ALWAYS``，
      经查 ``application.yml`` 无 ``spring.jackson.default-property-inclusion`` 配置）。
    ⇒ 因此本模型 ``msg`` 默认 ``None`` 且**必须保留在输出中**（不可 exclude_none）。

    字段顺序 ``code, msg, data`` 与 Java 声明顺序一致（JSON 对象无序，仅作可读性对齐）。
    """

    model_config = ConfigDict(extra="forbid")

    code: int = 1
    msg: str | None = None
    data: Any = None


class PageResult(BaseModel):
    """复刻 ``PageResult``：``{total, records}``。

    ❌ 禁止改成 ``{items,total}``、❌ 禁止新增 ``page`` / ``page_size`` / ``pages``
    （本轮指令 §12）。
    """

    model_config = ConfigDict(extra="forbid")

    total: int = 0
    records: list[Any] = []


# ===========================================================================
# 2) 异常体系（镜像 Java 继承链）
# ===========================================================================
class BaseException(RuntimeError):
    """对应 ``cc.feitwnd.exception.BaseException`` → HTTP 200 + ``code=0``。"""


class TokenException(RuntimeError):
    """对应 ``cc.feitwnd.exception.TokenException`` → HTTP 401。"""


class NotLoginException(TokenException):
    """缺少 token。旧消息：``未登录,请先登录``。"""


class UnauthorizedException(TokenException):
    """token 无效 / 不在 Redis 白名单。旧消息：``登录状态失效,请重新登录``。"""


class BlockedException(RuntimeError):
    """封禁（**不继承 BaseException**，与 Java 一致）→ HTTP 403。"""


class GuestReadOnlyException(RuntimeError):
    """游客只读（**不继承 BaseException**）→ HTTP 403。"""


class AccountNotFoundException(BaseException):
    """旧消息：``账号不存在``。"""


class PasswordErrorException(BaseException):
    """旧消息：``密码错误`` / ``两次输入的新密码不一致`` / ``原密码错误`` / ``新密码不得与原密码相同``。"""


class ArticleException(BaseException):
    """旧消息：``文章不存在``。"""


class VerifyCodeCoolDownException(BaseException):
    """旧消息：``验证码冷却中,请等待{n}秒后重试``。"""


class VerifyCodeErrorException(BaseException):
    """旧消息：``邮件验证码错误,还可以试{n}次`` / ``邮件验证码错误,请输入:{code}``。"""


class VerifyCodeLockException(BaseException):
    """旧消息：``验证码输入错误次数过多,验证码已被锁定{n}分钟``。"""


class VisitorSendCodeException(BaseException):
    """游客无需邮箱验证码。"""


class EmailSendErrorException(BaseException):
    """邮件发送失败。"""


class UploadFileErrorException(BaseException):
    """文件上传失败。"""


class RssSubscriptionException(BaseException):
    """RSS 订阅业务异常。"""


class SystemConfigException(BaseException):
    """系统配置业务异常。"""


class ValidationException(BaseException):
    """业务校验异常（等价 Java ``ValidationException``）。"""


class DuplicateEntryException(BaseException):
    """唯一键冲突。

    【FACT】Java 侧由 ``SQLIntegrityConstraintViolationException`` 处理器承接：
    HTTP **200** + ``code=0`` + ``msg = "{重复值}已存在"``（非 409！）
    → 本轮指令 §13 明确要求保持。
    """


class WeakJwtSecretError(ValueError):
    """jjwt ``Keys.hmacShaKeyFor`` 对 < 256 bit 密钥会抛 ``WeakKeyException``。"""


# ===========================================================================
# 3) 自定义 JSON 渲染
# ===========================================================================
def _legacy_default(obj: Any) -> Any:
    """兜底序列化（正常路径已被 Pydantic 的 PlainSerializer 处理）。"""
    import datetime as _dt
    import decimal

    if isinstance(obj, _dt.datetime):
        # 【FACT】yyyy-MM-dd HH:mm（**无秒**）
        return obj.strftime("%Y-%m-%d %H:%M")
    if isinstance(obj, _dt.date):
        return obj.strftime("%Y-%m-%d")
    if isinstance(obj, _dt.time):
        return obj.strftime("%H:%M:%S")
    if isinstance(obj, decimal.Decimal):
        return float(obj)
    raise TypeError(f"Object of type {type(obj).__name__} is not JSON serializable")


class LegacyJSONResponse(JSONResponse):
    """**必须**用 ``ensure_ascii=False``。

    【FACT】Jackson 默认**不转义非 ASCII** → 中文错误消息以原始 UTF-8 字节输出
    （如 ``"账号不存在"``）。Python ``json.dumps`` 默认 ``ensure_ascii=True``
    会输出 ``\\u8d26\\u53f7...`` —— 字节级不一致，前端虽能解析但**不符合契约**。
    """

    def render(self, content: Any) -> bytes:
        import json

        return json.dumps(
            content,
            ensure_ascii=False,
            allow_nan=False,
            separators=(",", ":"),
            default=_legacy_default,
        ).encode("utf-8")


# ===========================================================================
# 4) 错误消息文本（逐字复刻 Java 侧字符串）
# ===========================================================================
MSG_NOT_LOGIN = "未登录,请先登录"
MSG_UNAUTHORIZED = "登录状态失效,请重新登录"
MSG_GUEST_READONLY = "游客账号仅有查看权限，无法进行此操作"
MSG_ACCOUNT_NOT_FOUND = "账号不存在"
MSG_PASSWORD_ERROR = "密码错误"
MSG_ARTICLE_NOT_FOUND = "文章不存在"
MSG_UNKNOWN_ERROR = "未知错误"
MSG_NO_HANDLER = "请求地址不存在"
MSG_METHOD_NOT_ALLOWED_PREFIX = "不支持的请求方法："
MSG_MISSING_PARAM_PREFIX = "缺少必要参数："
MSG_UPLOAD_TOO_LARGE = "上传文件大小超过限制"
MSG_DUPLICATE_SUFFIX = "已存在"
MSG_RATE_LIMITED = "操作过于频繁，请稍后再试"

# 【FACT·实现细节】Pydantic 会给自定义 ``ValueError`` 的 message 加此前缀
#   （``ValidationError.errors()[i]["msg"] == "Value error, <原消息>"``）。
#   旧系统输出的是**裸消息** ⇒ 必须剥掉。
_PYDANTIC_VALUE_ERROR_PREFIX = "Value error, "

# 【FACT·关键】Java 侧的拼装是**逐条 violation** 的::
#
#     fieldErrors.stream()
#         .map(error -> error.getField() + ": " + error.getDefaultMessage())
#         .collect(Collectors.joining("; "))
#
#   ⇒ **同一个字段**上有两条 violation 时，字段名会**重复出现**::
#
#     name = " " * 21（同时违反 @NotBlank 与 @Size）
#     ⇒ "name: 分类名称不能为空; name: 分类名称不能超过20字"
#
#   ⚠️ 而 Pydantic 的 ``field_validator`` **一次只能抛出一个** ``ValueError``
#      ⇒ 一个字段的多条消息必须由**校验器自己**打包传递。
#      这里用一个不可见分隔符（ASCII Unit Separator, 0x1F）承载「同一字段的多条消息」，
#      由下面的处理器**展开为多个 ``field: msg`` 片段**，从而与旧系统逐字一致。
#      ❌ 若直接 ``"; ".join(msgs)``，第 2 条消息会丢掉 ``name: `` 前缀 —— 已实测踩中。
FIELD_ERROR_SEPARATOR = "\x1f"


def _envelope_response(status_code: int, msg: str | None) -> LegacyJSONResponse:
    """错误响应体固定为 ``{code:0, msg, data:null}``（复刻 ``Result.error``）。"""
    return LegacyJSONResponse(
        status_code=status_code,
        content={"code": 0, "msg": msg, "data": None},
    )


# ===========================================================================
# 5) 全局异常处理器
# ===========================================================================
def register_exception_handlers(app: FastAPI) -> None:
    """注册全部处理器。**顺序无关**（FastAPI 按类型精确匹配）。"""

    # --- 业务异常：200 + code=0（复刻 BaseException 处理器，无 @ResponseStatus）
    @app.exception_handler(BaseException)
    async def _handle_base(_: Request, exc: BaseException) -> LegacyJSONResponse:
        return _envelope_response(200, str(exc))

    # --- token 异常：401
    @app.exception_handler(TokenException)
    async def _handle_token(_: Request, exc: TokenException) -> LegacyJSONResponse:
        return _envelope_response(401, str(exc))

    # --- 封禁 / 游客只读：403
    @app.exception_handler(BlockedException)
    async def _handle_blocked(_: Request, exc: BlockedException) -> LegacyJSONResponse:
        return _envelope_response(403, str(exc))

    @app.exception_handler(GuestReadOnlyException)
    async def _handle_guest(_: Request, exc: GuestReadOnlyException) -> LegacyJSONResponse:
        return _envelope_response(403, str(exc))

    # --- 唯一键冲突：**200** + code=0（❌ 不是 409；本轮指令 §13）
    @app.exception_handler(DuplicateEntryException)
    async def _handle_duplicate(_: Request, exc: DuplicateEntryException) -> LegacyJSONResponse:
        return _envelope_response(200, str(exc))

    # --- @Valid 失败：**400**（❌ 不是 FastAPI 默认的 422；ADR-010 决策三第 2 条）
    @app.exception_handler(RequestValidationError)
    async def _handle_validation(_: Request, exc: RequestValidationError) -> LegacyJSONResponse:
        """【FACT】旧实现（``GlobalExceptionHandler``）::

               ex.getBindingResult().getFieldErrors().stream()
                 .map(error -> error.getField() + ": " + error.getDefaultMessage())
                 .collect(Collectors.joining("; "))
               → HTTP 400 + {code:0, msg:"username: 用户名不能为空; password: 密码不能为空", data:null}

        ⚠️ 必须剥掉 Pydantic 自动加的 ``"Value error, "`` 前缀，
           否则文案变成 ``username: Value error, 用户名不能为空`` —— **与旧契约不符**。
        """
        parts: list[str] = []
        for err in exc.errors():
            loc = [
                str(x)
                for x in err.get("loc", [])
                if x not in ("body", "query", "path", "header", "cookie")
            ]
            field = ".".join(loc) if loc else "unknown"
            # 【FACT·Stage 2.2】缺失**必填 query 参数**走的是**另一个**处理器：
            #   ``MissingServletRequestParameterException`` → 400 + ``"缺少必要参数：" + 参数名``
            #   （见 GlobalExceptionHandler 第 2 个参数异常处理器）。
            #   Pydantic 会把这类错误标记为 ``type="missing"`` 且 ``loc[0] == "query"``
            #   ⇒ 必须分流，否则文案会变成 ``ids: Field required``（英文，非旧契约）。
            if err.get("type") == "missing" and err.get("loc") and err["loc"][0] == "query":
                parts.append(f"{MSG_MISSING_PARAM_PREFIX}{field}")
                continue
            msg = str(err.get("msg", ""))
            if msg.startswith(_PYDANTIC_VALUE_ERROR_PREFIX):
                msg = msg[len(_PYDANTIC_VALUE_ERROR_PREFIX) :]
            # 【FACT】同一字段的多条 violation → 每条都带 ``field: `` 前缀
            #   （见 ``FIELD_ERROR_SEPARATOR`` 的说明）
            if FIELD_ERROR_SEPARATOR in msg:
                parts.extend(f"{field}: {one}" for one in msg.split(FIELD_ERROR_SEPARATOR))
            else:
                parts.append(f"{field}: {msg}")
        return _envelope_response(400, "; ".join(parts) if parts else MSG_UNKNOWN_ERROR)

    # --- 框架级 HTTPException：404 / 405 保持旧语义与文案
    @app.exception_handler(StarletteHTTPException)
    async def _handle_http(request: Request, exc: StarletteHTTPException) -> LegacyJSONResponse:
        if exc.status_code == 404:
            return _envelope_response(404, MSG_NO_HANDLER)
        if exc.status_code == 405:
            # 【FACT】旧实现：``"不支持的请求方法：" + ex.getMethod()``
            #        ``HttpRequestMethodNotSupportedException.getMethod()`` 返回的是
            #        **请求本身的 HTTP 方法**（如 ``DELETE``），**不是** Starlette 的 detail
            #        （``"Method Not Allowed"``）⇒ 必须用 ``request.method``。
            return _envelope_response(405, MSG_METHOD_NOT_ALLOWED_PREFIX + request.method.upper())
        if exc.status_code in (400, 401, 403, 500):
            return _envelope_response(exc.status_code, MSG_UNKNOWN_ERROR)
        return _envelope_response(exc.status_code, MSG_UNKNOWN_ERROR)

    # --- 兜底：500 + {code:0, msg:"未知错误"}
    @app.exception_handler(Exception)
    async def _handle_unknown(_: Request, exc: Exception) -> LegacyJSONResponse:
        from app.core.logging import get_logger

        get_logger(__name__).exception("未知异常：%s", exc)
        return _envelope_response(500, MSG_UNKNOWN_ERROR)

    # --- ⚠️ Stage 2.2：**删除**了 Stage 2.1 里的「裸 ValueError → 400 缺少必要参数」兜底 ---
    #   理由（已核对，见 docs/PHASE2_STAGE2_2_REPORT.md §3 / §7）：
    #     ① **无人使用**：缺失必填 query 参数时 FastAPI 抛的是 ``RequestValidationError``
    #        （已由上面的处理器按 ``type == "missing"`` 正确分流为
    #        ``400 + "缺少必要参数：X"``）；字段校验器的 ``ValueError`` 也会被 Pydantic
    #        包装成 ``RequestValidationError``。⇒ 裸 ``ValueError`` 在这条路径上**从不出现**。
    #     ② **映射错误**：``pydantic.ValidationError`` 与 ``json.JSONDecodeError``
    #        都是 ``ValueError`` 的**子类** ⇒ 业务代码里任何"缓存值损坏 / 数据形状不符"
    #        都会被错误地报成「缺少必要参数：<pydantic 长英文报文>」。
    #     ③ **旧行为**：旧系统没有这种 400。反序列化失败在 Spring 里由
    #        ``SimpleCacheErrorHandler`` **原样重抛** ⇒ 落到 ``Exception`` 处理器
    #        ⇒ **500 + "未知错误"**。因此让裸 ``ValueError`` 自然落到上面的兜底才是**等价**行为。
    #   ⚠️ Stage 2.1 的全部测试在新行为下依然为绿（已验证）。
