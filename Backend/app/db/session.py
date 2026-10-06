"""异步引擎 / Session 工厂。

【DECISION·ADR-002】SQLAlchemy 2.x **async**；事务边界在 **service** 层
（``async with session.begin()``），不在 router。

【DECISION·D9】``--workers 1``（单进程）→ 引擎连接池保持默认即可
（数据量 1.25 MB，QPS 极低；不比照 Druid 的 initial 5 / min 5 / max 20 ——
 ADR-002「未决」项，本轮不配置）。

⚠️ 惰性创建：**导入本模块不会建立任何数据库连接**。
   契约测试通过覆盖依赖注入来避免连库，因此不需要可用的 MySQL。
"""
from __future__ import annotations

from functools import lru_cache
from typing import Any

from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, async_sessionmaker, create_async_engine

from app.core.config import Settings, get_settings

__all__ = ["get_engine", "get_session_factory", "dispose_engine", "ping_database"]


@lru_cache(maxsize=1)
def get_engine(dsn: str, *, echo: bool = False) -> AsyncEngine:
    """按 DSN 缓存引擎（同进程内复用连接池）。"""
    return create_async_engine(
        dsn,
        echo=echo,
        pool_pre_ping=True,
        # 【FACT】旧连接串 useSSL=false → 本地回环，不开 TLS
        connect_args={"ssl": None} if not dsn.startswith("sqlite") else {},
    )


@lru_cache(maxsize=8)
def _session_factory(dsn: str, echo: bool) -> async_sessionmaker[AsyncSession]:
    """**只接受可哈希的原始值** —— 见 ``get_session_factory`` 的说明。"""
    engine = get_engine(dsn, echo=echo)
    return async_sessionmaker(
        engine,
        class_=AsyncSession,
        expire_on_commit=False,
        autoflush=False,
    )


def get_session_factory(settings: Settings | None = None) -> async_sessionmaker[AsyncSession]:
    """按「DSN + echo」缓存 session 工厂。

    ⚠️【踩坑记录】**不要把 ``Settings`` 直接传给 ``lru_cache`` 函数。**
       Pydantic v2 的模型**不可哈希**（``__hash__`` 未实现），
       ``lru_cache`` 会对参数做 hash → 抛
       ``TypeError: unhashable type: 'Settings'``。

       该缺陷在**契约测试里看不见**（测试用 ``dependency_overrides`` 整个替换掉了
       ``get_db_session``），只在**真实运行**时才暴露 —— 因此本模块改为对
       **原始值**（``dsn`` / ``echo``）缓存，并对真实依赖链补了
       ``tests/contract/test_app_wiring.py`` 兜底。
    """
    settings = settings or get_settings()
    return _session_factory(settings.database.dsn(), settings.log.sql_echo)


async def dispose_engine(settings: Settings | None = None) -> None:
    """关闭连接池（应用 shutdown 时调用）。

    ``lru_cache`` 不提供遍历已缓存值的能力，因此按当前设置重建同一个 key 定位引擎。
    """
    settings = settings or get_settings()
    try:
        engine = get_engine(settings.database.dsn(), echo=settings.log.sql_echo)
        await engine.dispose()
    except Exception:  # pragma: no cover - 关闭失败不影响退出
        pass
    get_engine.cache_clear()
    _session_factory.cache_clear()


async def ping_database(settings: Settings | None = None) -> bool:
    """只读连通性探测（**仅在显式调用时**连库；契约测试不调用）。"""
    from sqlalchemy import text

    factory = get_session_factory(settings)
    async with factory() as session:
        result: Any = await session.execute(text("select 1"))
        return result.scalar_one() == 1
