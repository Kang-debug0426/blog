"""查询参数模型的宽松解析基类。

【背景 / 契约还原】
旧 Java 系统（Spring MVC）在把 URL 查询串绑定到 ``Integer`` / ``Boolean`` /
``Long`` 等字段时，对**空字符串**的处理是：
* 有 ``defaultValue`` 的参数（如 ``page`` / ``pageSize``）→ 回落到默认值；
* 无默认值的包装类型 → 视为 ``null``。

前端沿用该约定，列表页会发送形如
``?page=1&pageSize=15&title=&categoryId=&isPublished=`` 的请求。

Pydantic v2 默认会把 ``""`` 当作非法整数/布尔值直接抛校验错误，再被统一异常处理
映射为 HTTP 400 —— 这正是切换后管理后台文章列表 400 的根因。

本基类在模型解析前按上述规则归一化空字符串，还原旧系统契约（响应契约不变）。
"""

import datetime
from typing import Annotated

from pydantic import BaseModel, BeforeValidator, ConfigDict, model_validator
from pydantic_core import PydanticUndefined


def blank_string_to_none(value):
    """把空字符串 / 纯空白转成 ``None``。"""
    if isinstance(value, str) and value.strip() == "":
        return None
    return value


def blank_to_default(default):
    """生成一个「空字符串回落到指定默认值」的 ``BeforeValidator``。

    ``default`` 可以是值，也可以是**可调用对象**（用于 ``today()`` 这类动态默认值）。
    """
    def _conv(value):
        if isinstance(value, str) and value.strip() == "":
            return default() if callable(default) else default
        return value

    return BeforeValidator(_conv)


def _default_begin() -> "datetime.date":
    return datetime.date.today() - datetime.timedelta(days=6)


#: 报表日期区间：空值回落为「最近 7 天」（对齐前端日期选择器默认值）。
BeginDateQuery = Annotated[datetime.date, blank_to_default(_default_begin)]
EndDateQuery = Annotated[datetime.date, blank_to_default(datetime.date.today)]


#: 可选整数查询参数：``?visitorId=`` 这类空值按 null 处理，不再 400。
OptionalIntQuery = Annotated[int | None, BeforeValidator(blank_string_to_none)]

#: 分页参数：空值回落默认值（对齐 Spring ``defaultValue`` 语义）。
PageNumberQuery = Annotated[int, blank_to_default(1)]
PageSizeQuery = Annotated[int, blank_to_default(10)]


class LenientQueryModel(BaseModel):
    """用于 ``Annotated[DTO, Query()]`` 的查询参数基类。

    空字符串按「有默认值→默认值，无默认值→null」归一化。
    """

    model_config = ConfigDict(populate_by_name=True, from_attributes=True)

    @model_validator(mode="before")
    @classmethod
    def _blank_string_normalise(cls, data):
        if not isinstance(data, dict):
            return data

        # 建立「字段名 / 别名 → FieldInfo」映射，便于取默认值
        by_key = {}
        for name, f in cls.model_fields.items():
            by_key[name] = f
            if f.alias:
                by_key[f.alias] = f

        out = {}
        for key, value in data.items():
            if isinstance(value, str) and value.strip() == "":
                f = by_key.get(key)
                if f is not None and f.default is not PydanticUndefined:
                    out[key] = f.default
                else:
                    out[key] = None
            else:
                out[key] = value
        return out
