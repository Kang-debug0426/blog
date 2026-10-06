"""``taxonomy`` 出入参契约 —— 复刻旧 ``ArticleCategoryDTO`` / ``ArticleTagDTO``
与两个**实体**（``ArticleCategories`` / ``ArticleTags``）。

---

## 1. 出参是**实体直出**（不是 VO！）

【FACT】旧 controller 的返回类型是 ``Result<List<ArticleCategories>>`` ——
返回的是 **entity**（``cc.feitwnd.entity.ArticleCategories``），不是 VO。
字段顺序 = 实体声明顺序::

    ArticleCategories  id, name, slug, description, sort, articleCount, createTime, updateTime
    ArticleTags        id, name, slug, articleCount, createTime, updateTime

⚠️ **C-1（易漂移）**：这两个实体的 ``createTime`` / ``updateTime`` 上带
   ``@JsonFormat(pattern="yyyy-MM-dd HH:mm:ss")`` —— 它**覆盖**了
   ``JacksonObjectMapper`` 注册的类型级序列化器（``yyyy-MM-dd HH:mm``）
   ⇒ **实体直出的日期带秒**，与 VO（``article`` 模块）**不同**。
   实证（真实 Jackson 2.19.2 + fat jar 内 jar）::

       ENTITY_JSONFORMAT = {"createTime":"2026-01-02 03:04:05"}   ← 实体（本模块）
       PLAIN_NOMARK      = {"createTime":"2026-01-02 03:04"}      ← 无 @JsonFormat

   因此本模块**必须**用 ``LegacyDateTimeSeconds``，❌ 不得复用 ``LegacyDateTime``。

⚠️ **C-2（易漂移）**：``articleCount`` 属性**存在**，但
   * ``listAll`` 的 SQL 是 ``select * from article_categories order by ...``
     —— **没有** ``article_count`` 列 ⇒ 该属性**未被赋值** ⇒ JSON 里是
     ``"articleCount": null``（**键存在**，值为 null）。
   * ``getVisibleCategories`` / ``getVisibleTags`` 的 SQL 里有
     ``count(...) as article_count`` ⇒ 该属性有值。
   ❌ 不得把 ``listAll`` 的结果模型换成"没有 articleCount 字段"的模型 ——
      键缺失与键为 null 是**两种不同的契约**。

---

## 2. 入参校验：复刻 Jakarta ``@Valid``

【FACT】三个约束逐字复刻（``ArticleCategoryDTO`` / ``ArticleTagDTO``）::

    ArticleCategoryDTO:
      @NotBlank @Size(max=20)  name         → "分类名称不能为空" / "分类名称不能超过20字"
      @NotBlank @Size(max=20)  slug         → "URL标识不能为空"   / "URL标识不能超过20字"
                 @Size(max=100) description → "分类描述不能超过100字"
                 (无约束)       id / sort
    ArticleTagDTO:
      @NotBlank @Size(max=20)  name         → "标签名称不能为空" / "标签名称不能超过20字"
      @NotBlank @Size(max=30)  slug         → "URL标识不能为空" / "URL标识不能超过30字"
                 (无约束)       id

⚠️ **C-9（实证结论）**：**多字段同时失败时，旧系统的字段顺序不可确定**。
   实证（Hibernate Validator 8.0.3.Final + 项目自带 jar）::

       same JVM 连续 4 次：  empty#0 = slug, name
                            empty#1 = slug, name
                            empty#2 = slug, name
                            empty#3 = name, slug   ← 同一进程内就变了

   原因：``Validator.validate`` 返回 ``Set``（``ConstraintViolation`` 未实现
   ``Comparable``/``hashCode``）→ 迭代顺序随身份哈希变化。
   ⇒ 本实现固定按**字段声明顺序**输出（一种合法顺序），
     测试对多字段用例**只断言集合**，❌ 不断言顺序。

⚠️ 另一个实证结论：**同一字段可以产出 2 条消息**
   （``name = " " * 21`` → ``name: 分类名称不能为空; name: 分类名称不能超过20字``）
   ⇒ 每条字段的消息用 ``"; "`` 拼接后再由全局处理器拼一次，字符串完全对齐。

⚠️ ``@Size`` 的长度语义 = Java ``String.length()``（UTF-16 code unit）
   ⇒ 用 ``legacy_types.java_length``，❌ 不用 ``len()``。

⚠️ 忽略未知字段：``JacksonObjectMapper`` 关闭了 ``FAIL_ON_UNKNOWN_PROPERTIES``
   ⇒ ``extra="ignore"``（与旧系统一致：多传字段不报错）。
"""
from __future__ import annotations

from collections.abc import Callable
from typing import Any

from pydantic import BaseModel, ConfigDict, TypeAdapter, field_validator

from app.core.errors import FIELD_ERROR_SEPARATOR
from app.core.legacy_types import CamelModel, LegacyDateTimeSeconds, java_length

__all__ = [
    "ArticleCategoryDTO",
    "ArticleTagDTO",
    "ArticleCategoryVO",
    "ArticleTagVO",
    "CATEGORY_LIST_ADAPTER",
    "TAG_LIST_ADAPTER",
    # 校验文案（供测试逐字引用）
    "MSG_CATEGORY_NAME_BLANK",
    "MSG_CATEGORY_NAME_TOO_LONG",
    "MSG_SLUG_BLANK",
    "MSG_CATEGORY_SLUG_TOO_LONG",
    "MSG_CATEGORY_DESC_TOO_LONG",
    "MSG_TAG_NAME_BLANK",
    "MSG_TAG_NAME_TOO_LONG",
    "MSG_TAG_SLUG_TOO_LONG",
]

# ---------------------------------------------------------------------------
# 校验文案（逐字复刻 DTO 注解的 message）
# ---------------------------------------------------------------------------
MSG_CATEGORY_NAME_BLANK = "分类名称不能为空"
MSG_CATEGORY_NAME_TOO_LONG = "分类名称不能超过20字"
MSG_SLUG_BLANK = "URL标识不能为空"
MSG_CATEGORY_SLUG_TOO_LONG = "URL标识不能超过20字"
MSG_CATEGORY_DESC_TOO_LONG = "分类描述不能超过100字"
MSG_TAG_NAME_BLANK = "标签名称不能为空"
MSG_TAG_NAME_TOO_LONG = "标签名称不能超过20字"
MSG_TAG_SLUG_TOO_LONG = "URL标识不能超过30字"


def _not_blank_then_size(
    *, blank_msg: str, size_msg: str, max_len: int
) -> Callable[[Any], Any]:
    """复刻 ``@NotBlank`` + ``@Size(max=n)`` 在**同一字段**上的组合语义。

    * ``null``        → 只报 ``@NotBlank``（``@Size`` 对 null 视为通过）
    * ``""`` / 空白串 → 报 ``@NotBlank``；若**长度**也超限则再报 ``@Size``
                        （实例：21 个空格 → 两条消息，与实证一致）
    * 非空白串        → 仅长度超限时报 ``@Size``
    """

    def _validate(value: Any) -> Any:
        msgs: list[str] = []
        if value is None or (isinstance(value, str) and value.strip() == ""):
            msgs.append(blank_msg)
        if isinstance(value, str) and java_length(value) > max_len:
            msgs.append(size_msg)
        if msgs:
            # ⚠️ 一条 ``ValueError`` 承载该字段的**全部**消息（用不可见分隔符打包）。
            #    全局处理器会把它展开成 ``name: 分类名称不能为空; name: 分类名称不能超过20字``
            #    —— 即 Java 侧「逐条 violation 拼 ``field + ": " + message``」的等价物。
            #    ❌ 不要用 "; ".join()：那会让第 2 条消息丢掉 ``name: `` 前缀（已实测踩中）。
            raise ValueError(FIELD_ERROR_SEPARATOR.join(msgs))
        return value

    return _validate


def _size_only(*, size_msg: str, max_len: int) -> Callable[[Any], Any]:
    """复刻单独的 ``@Size(max=n)``（``null`` 通过）。"""

    def _validate(value: Any) -> Any:
        if isinstance(value, str) and java_length(value) > max_len:
            raise ValueError(size_msg)
        return value

    return _validate


# ===========================================================================
# 入参 DTO
# ===========================================================================
class ArticleCategoryDTO(BaseModel):
    """复刻 ``cc.feitwnd.dto.ArticleCategoryDTO``（``@Valid @RequestBody``）。"""

    # 【FACT】JacksonObjectMapper 关闭 FAIL_ON_UNKNOWN_PROPERTIES → 多传字段不报错
    # ⚠️ ``validate_default=True`` 必须开：否则字段**缺失**时 Pydantic 会跳过校验，
    #    把 ``None`` 直接送进 service（返回 200 而非 400）—— 行为回归。
    model_config = ConfigDict(extra="ignore", validate_default=True)

    id: int | None = None
    name: str | None = None
    slug: str | None = None
    description: str | None = None
    sort: int | None = None

    _v_name = field_validator("name", mode="before")(
        _not_blank_then_size(
            blank_msg=MSG_CATEGORY_NAME_BLANK,
            size_msg=MSG_CATEGORY_NAME_TOO_LONG,
            max_len=20,
        )
    )
    _v_slug = field_validator("slug", mode="before")(
        _not_blank_then_size(
            blank_msg=MSG_SLUG_BLANK,
            size_msg=MSG_CATEGORY_SLUG_TOO_LONG,
            max_len=20,
        )
    )
    _v_description = field_validator("description", mode="before")(
        _size_only(size_msg=MSG_CATEGORY_DESC_TOO_LONG, max_len=100)
    )


class ArticleTagDTO(BaseModel):
    """复刻 ``cc.feitwnd.dto.ArticleTagDTO``（``@Valid @RequestBody``）。"""

    model_config = ConfigDict(extra="ignore", validate_default=True)

    id: int | None = None
    name: str | None = None
    slug: str | None = None

    _v_name = field_validator("name", mode="before")(
        _not_blank_then_size(
            blank_msg=MSG_TAG_NAME_BLANK,
            size_msg=MSG_TAG_NAME_TOO_LONG,
            max_len=20,
        )
    )
    _v_slug = field_validator("slug", mode="before")(
        _not_blank_then_size(
            blank_msg=MSG_SLUG_BLANK,
            size_msg=MSG_TAG_SLUG_TOO_LONG,
            max_len=30,
        )
    )


# ===========================================================================
# 出参（实体直出）
# ===========================================================================
class ArticleCategoryVO(CamelModel):
    """复刻 ``cc.feitwnd.entity.ArticleCategories``（**实体直出**）。

    ⚠️ 日期字段必须是 ``LegacyDateTimeSeconds``（**带秒**）—— 见模块 docstring C-1。
    """

    id: int | None = None
    name: str | None = None
    slug: str | None = None
    description: str | None = None
    sort: int | None = None
    # 【C-2】``listAll`` 时该键**存在且为 null**（SQL 无 article_count 列）
    article_count: int | None = None
    create_time: LegacyDateTimeSeconds | None = None
    update_time: LegacyDateTimeSeconds | None = None


class ArticleTagVO(CamelModel):
    """复刻 ``cc.feitwnd.entity.ArticleTags``（**实体直出**）。"""

    id: int | None = None
    name: str | None = None
    slug: str | None = None
    # 【C-2】``listAll`` 时该键**存在且为 null**
    article_count: int | None = None
    create_time: LegacyDateTimeSeconds | None = None
    update_time: LegacyDateTimeSeconds | None = None


# 缓存 JSON ⇄ 模型 的适配器（缓存里存的是**响应 data 的 JSON**）
CATEGORY_LIST_ADAPTER: TypeAdapter[list[ArticleCategoryVO]] = TypeAdapter(list[ArticleCategoryVO])
TAG_LIST_ADAPTER: TypeAdapter[list[ArticleTagVO]] = TypeAdapter(list[ArticleTagVO])
