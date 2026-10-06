"""Legacy 序列化类型 —— 日期时间格式的**唯一**来源。

【FACT】``cc/feitwnd/json/JacksonObjectMapper.java``（字节码确认）::

    DEFAULT_DATE_FORMAT      = "yyyy-MM-dd"
    DEFAULT_DATE_TIME_FORMAT = "yyyy-MM-dd HH:mm"     ← **无秒**
    DEFAULT_TIME_FORMAT      = "HH:mm:ss"

同时注册了 LocalDateTime / LocalDate / LocalTime 的**序列化器与反序列化器**，
并通过 ``extendMessageConverters`` 把该 ObjectMapper **插到 converters 第 0 位**
（覆盖 Spring 默认的 JavaTimeModule）→ 所以这 3 个格式是**全站唯一**的日期契约。

⚠️ 影响：``publish_time = 2026-01-01 12:30:45`` 序列化后是 ``"2026-01-01 12:30"``
   —— **秒被截断**。前端历史行为即如此，新系统必须一致（否则字符串比较型前端逻辑会变）。
"""
from __future__ import annotations

import datetime as _dt
from collections.abc import Sequence
from typing import Annotated

from pydantic import BaseModel, BeforeValidator, ConfigDict, PlainSerializer
from pydantic.alias_generators import to_camel

__all__ = [
    "LegacyDateTime",
    "LegacyDateTimeSeconds",
    "LegacyDate",
    "LegacyTime",
    "format_datetime",
    "format_datetime_seconds",
    "format_date",
    "format_time",
    "CamelModel",
    "java_length",
    "LegacyIdList",
    "split_legacy_id_list",
]

DATETIME_FORMAT = "%Y-%m-%d %H:%M"
# 【FACT·Stage 2.2 实证】实体类字段上的 ``@JsonFormat(pattern="yyyy-MM-dd HH:mm:ss")``
#   会**覆盖**本模块 docstring 里那个类型级序列化器（Jackson 的
#   ``JSR310FormattedSerializerBase.createContextual`` 读取属性级 ``@JsonFormat``
#   并返回带该 formatter 的新序列化器）。
#   ⇒ 因此**实体直出**的端点必须用这个"带秒"的别名，而不是 ``LegacyDateTime``。
#   实证方法（真实 Jackson 2.19.2 + 项目 fat jar 内的 jar）::
#       ENTITY_JSONFORMAT = {"...","createTime":"2026-01-02 03:04:05"}   ← 有 @JsonFormat
#       PLAIN_NOMARK      = {"createTime":"2026-01-02 03:04"}            ← 无 @JsonFormat
DATETIME_SECONDS_FORMAT = "%Y-%m-%d %H:%M:%S"
DATE_FORMAT = "%Y-%m-%d"
TIME_FORMAT = "%H:%M:%S"


def format_datetime(value: _dt.datetime | None) -> str | None:
    return None if value is None else value.strftime(DATETIME_FORMAT)


def format_date(value: _dt.date | None) -> str | None:
    return None if value is None else value.strftime(DATE_FORMAT)


def format_time(value: _dt.time | None) -> str | None:
    return None if value is None else value.strftime(TIME_FORMAT)


def format_datetime_seconds(value: _dt.datetime | None) -> str | None:
    return None if value is None else value.strftime(DATETIME_SECONDS_FORMAT)


LegacyDateTime = Annotated[_dt.datetime, PlainSerializer(format_datetime, return_type=str | None)]
LegacyDateTimeSeconds = Annotated[
    _dt.datetime, PlainSerializer(format_datetime_seconds, return_type=str | None)
]
LegacyDate = Annotated[_dt.date, PlainSerializer(format_date, return_type=str | None)]
LegacyTime = Annotated[_dt.time, PlainSerializer(format_time, return_type=str | None)]

# ⚠️【踩坑记录】**列可空时必须写 ``X | None``**
#   本别名本身**不含** ``None``（``Annotated[datetime, ...]``）。
#   若把可空列声明为 ``publish_time: LegacyDateTime = None``，那么
#   **显式传入 ``None`` 会触发 Pydantic 校验失败**（默认值不会被校验，但真实数据里的
#   ``None`` 会） → 一篇 ``publish_time IS NULL`` 的文章会 500。
#   正确写法：``publish_time: LegacyDateTime | None = None``
#   （``Optional[Annotated[...]]`` 仍会应用同一个 ``PlainSerializer`` —— 已实测。）


class CamelModel(BaseModel):
    """**出参**基类：JSON 字段名 = camelCase。

    【FACT·关键契约】Jackson 默认按 **Java bean 属性名**输出 → 全部是 camelCase。
    实证（``analysis/frontend`` 产物词频统计）::

        coverImage 32 · categoryName 5 · viewCount 6 · isTop 18 · publishTime 6 · isVisible 31
        cover_image 0 · category_name 0 · view_count 0 · publish_time 0 · is_visible 0

    ⇒ ❌ 不得输出 snake_case。FastAPI 默认以 ``by_alias=True`` 序列化响应模型，
      因此只要挂上 ``alias_generator``，输出即为 camelCase。

    ⚠️ 仅用于**出参（VO）**。入参 DTO 在本阶段涉及的字段（username/password/code/id/token）
       都是单词、大小写无差异，故不使用该基类，避免把「接受 snake_case」这一
       超出旧契约的宽容度引入进来。
    """

    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
        from_attributes=True,
        extra="ignore",
    )


# ---------------------------------------------------------------------------
# Java 语义辅助
# ---------------------------------------------------------------------------
def java_length(value: str) -> int:
    """等价于 Java ``String.length()`` —— **UTF-16 code unit 个数**。

    【FACT】Jakarta ``@Size(max=n)`` 的 ``n`` 与 Java ``String.length()`` 同口径：
       每个 UTF-16 code unit 记 1。BMP 外字符（emoji、部分 CJK 扩展）在 Java 里算 **2**，
       而 Python ``len()`` 算 **1** ⇒ 直接用 ``len()`` 会让
       "20 个 emoji"（Java 长度 40）**误判为合法**，属于**契约漂移**。

    例：``java_length("😀") == 2``，而 ``len("😀") == 1``。
    """
    # surrogatepass 不需要：str.encode 会把 BMP 外字符编成 4 字节 → /2 得 2 个 code unit
    return len(value.encode("utf-16-le")) // 2


# ---------------------------------------------------------------------------
# Spring ``@RequestParam List<Long> ids`` 的逗号切分语义
# ---------------------------------------------------------------------------
#: ---------------------------------------------------------------------------
#: 【FACT·Stage 2.3 实证】这条是浏览器 E2E **逼出来的契约**，之前阶段没有发现。
#:
#: 1) 旧 Controller（``analysis/backend-src`` 反编译）：:
#:
#:        @DeleteMapping
#:        public Result<String> delete(@RequestParam List<Long> ids) { ... }
#:
#:    Spring MVC 对 ``List`` / 数组的绑定走 ``StringToCollectionConverter``，
#:    其 ```StringUtils.commaDelimitedListToStringArray`` **默认按逗号切分** ⇒
#:    ``?ids=1,2`` 与 ``?ids=1&ids=2`` **两种写法旧系统都接受**。
#:
#: 2) 旧前端**只会发逗号串**（``analysis/frontend/www/wwwroot`` 构建产物实证）::
#:
#:        admin.imcjk.top/assets/index-D5kK7fJ1.js
#:          removeCategories: a => request.delete("/admin/articleCategory",
#:                                   { params: { ids: a.join(",") } })
#:
#:    同一形态出现在全部 14 类批量接口（articleCategory / article/tag / article /
#:    friendLink / message / message:approve / operationLog / visitor / visitor:block /
#:    visitor:unblock / experience / skill / socialMedia / music / rssSubscription /
#:    view），说明这是**前端统一约定**，不是某处的偶然写法。
#:
#: ⇒ 结论：新实现若只接受重复参数，会让**真实页面的批量删除一律 400**。
#:    这不是 LEGACY-DEFECT，而是**新系统的契约漂移**（DEFECT 记于 Stage 2.3 报告 §7）。
#:    修复方向是「向旧行为对齐」（改新实现），而不是「要求前端改成重复参数」
#:    —— 后者同时违反「不改前端」与「不为测试方便而改冻结契约」两条边界。
#: ---------------------------------------------------------------------------
def split_legacy_id_list(value: object) -> object:
    """把 ``"1,2,3"`` 还原成 ``[1, 2, 3]``；已经是列表的逐元素再切一次。

    对齐 Spring ``StringToCollectionConverter``：

    * ``"1,2"``     → ``[1, 2]``            （旧前端**唯一**使用的形态）
    * ``"1, 2 ,3"`` → ``[1, 2, 3]``         （逗号两侧空白由 Spring trim 掉）
    * ``["1","2"]`` → ``[1, 2]``            （``?ids=1&ids=2``，旧系统同样接受）
    * ``["1,2"]``   → ``[1, 2]``            （两种形态混发也成立）
    * 其它值**原样返回** ⇒ 后续校验/错误消息与新实现完全一致（未引入宽容度）。

    ⚠️ 空逗号（``"1,,2"``）与空串（``""``）→ ``[1, 2]`` / ``[]``。
       Spring 对 ``""`` 会得到空列表；本实现一致。
    """
    if isinstance(value, str):
        return [part.strip() for part in value.split(",") if part.strip()]
    if isinstance(value, Sequence) and not isinstance(value, (str, bytes)):
        out: list[object] = []
        for item in value:
            if isinstance(item, str):
                out.extend(p.strip() for p in item.split(",") if p.strip())
            else:
                out.append(item)
        return out
    return value


#: 用于 router 签名：``ids: Annotated[LegacyIdList, Query()]``
LegacyIdList = Annotated[list[int], BeforeValidator(split_legacy_id_list)]
