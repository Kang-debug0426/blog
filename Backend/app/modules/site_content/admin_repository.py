from sqlalchemy import select, insert, update, delete, func, text, desc, asc
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Any, Sequence
from app.db.models.site_content import PersonalInfo, Skill, Experience, SocialMedia, Music, FriendLink, SystemConfig

class AdminSiteContentRepository:
    def __init__(self, session: AsyncSession):
        self._s = session

    # ====== PersonalInfo ======
    async def get_all_personalinfo(self) -> Sequence[PersonalInfo]:
        stmt = select(PersonalInfo)
        result = await self._s.execute(stmt)
        return result.scalars().all()
        
    async def get_personalinfo_by_id(self, id: int) -> PersonalInfo | None:
        stmt = select(PersonalInfo).where(PersonalInfo.id == id)
        return (await self._s.execute(stmt)).scalars().first()

    async def insert_personalinfo(self, data: dict[str, Any]) -> None:
        stmt = insert(PersonalInfo).values(**data)
        await self._s.execute(stmt)

    async def update_personalinfo(self, data: dict[str, Any]) -> None:
        stmt = update(PersonalInfo).where(PersonalInfo.id == data['id']).values(**data)
        await self._s.execute(stmt)

    async def batch_delete_personalinfo(self, ids: list[int]) -> None:
        stmt = delete(PersonalInfo).where(PersonalInfo.id.in_(ids))
        await self._s.execute(stmt)

    # ====== Skill ======
    async def get_all_skill(self) -> Sequence[Skill]:
        stmt = select(Skill)
        result = await self._s.execute(stmt)
        return result.scalars().all()
        
    async def get_skill_by_id(self, id: int) -> Skill | None:
        stmt = select(Skill).where(Skill.id == id)
        return (await self._s.execute(stmt)).scalars().first()

    async def insert_skill(self, data: dict[str, Any]) -> None:
        stmt = insert(Skill).values(**data)
        await self._s.execute(stmt)

    async def update_skill(self, data: dict[str, Any]) -> None:
        stmt = update(Skill).where(Skill.id == data['id']).values(**data)
        await self._s.execute(stmt)

    async def batch_delete_skill(self, ids: list[int]) -> None:
        stmt = delete(Skill).where(Skill.id.in_(ids))
        await self._s.execute(stmt)

    # ====== Experience ======
    async def get_all_experience(self) -> Sequence[Experience]:
        stmt = select(Experience)
        result = await self._s.execute(stmt)
        return result.scalars().all()
        
    async def get_experience_by_id(self, id: int) -> Experience | None:
        stmt = select(Experience).where(Experience.id == id)
        return (await self._s.execute(stmt)).scalars().first()

    async def insert_experience(self, data: dict[str, Any]) -> None:
        stmt = insert(Experience).values(**data)
        await self._s.execute(stmt)

    async def update_experience(self, data: dict[str, Any]) -> None:
        stmt = update(Experience).where(Experience.id == data['id']).values(**data)
        await self._s.execute(stmt)

    async def batch_delete_experience(self, ids: list[int]) -> None:
        stmt = delete(Experience).where(Experience.id.in_(ids))
        await self._s.execute(stmt)

    # ====== SocialMedia ======
    async def get_all_socialmedia(self) -> Sequence[SocialMedia]:
        stmt = select(SocialMedia)
        result = await self._s.execute(stmt)
        return result.scalars().all()
        
    async def get_socialmedia_by_id(self, id: int) -> SocialMedia | None:
        stmt = select(SocialMedia).where(SocialMedia.id == id)
        return (await self._s.execute(stmt)).scalars().first()

    async def insert_socialmedia(self, data: dict[str, Any]) -> None:
        stmt = insert(SocialMedia).values(**data)
        await self._s.execute(stmt)

    async def update_socialmedia(self, data: dict[str, Any]) -> None:
        stmt = update(SocialMedia).where(SocialMedia.id == data['id']).values(**data)
        await self._s.execute(stmt)

    async def batch_delete_socialmedia(self, ids: list[int]) -> None:
        stmt = delete(SocialMedia).where(SocialMedia.id.in_(ids))
        await self._s.execute(stmt)

    # ====== Music ======
    async def get_all_music(self) -> Sequence[Music]:
        stmt = select(Music)
        result = await self._s.execute(stmt)
        return result.scalars().all()
        
    async def get_music_by_id(self, id: int) -> Music | None:
        stmt = select(Music).where(Music.id == id)
        return (await self._s.execute(stmt)).scalars().first()

    async def insert_music(self, data: dict[str, Any]) -> None:
        stmt = insert(Music).values(**data)
        await self._s.execute(stmt)

    async def update_music(self, data: dict[str, Any]) -> None:
        stmt = update(Music).where(Music.id == data['id']).values(**data)
        await self._s.execute(stmt)

    async def batch_delete_music(self, ids: list[int]) -> None:
        stmt = delete(Music).where(Music.id.in_(ids))
        await self._s.execute(stmt)

    # ====== FriendLink ======
    async def get_all_friendlink(self) -> Sequence[FriendLink]:
        stmt = select(FriendLink)
        result = await self._s.execute(stmt)
        return result.scalars().all()
        
    async def get_friendlink_by_id(self, id: int) -> FriendLink | None:
        stmt = select(FriendLink).where(FriendLink.id == id)
        return (await self._s.execute(stmt)).scalars().first()

    async def insert_friendlink(self, data: dict[str, Any]) -> None:
        stmt = insert(FriendLink).values(**data)
        await self._s.execute(stmt)

    async def update_friendlink(self, data: dict[str, Any]) -> None:
        stmt = update(FriendLink).where(FriendLink.id == data['id']).values(**data)
        await self._s.execute(stmt)

    async def batch_delete_friendlink(self, ids: list[int]) -> None:
        stmt = delete(FriendLink).where(FriendLink.id.in_(ids))
        await self._s.execute(stmt)

    # ====== SystemConfig ======
    async def get_all_systemconfig(self) -> Sequence[SystemConfig]:
        stmt = select(SystemConfig)
        result = await self._s.execute(stmt)
        return result.scalars().all()
        
    async def get_systemconfig_by_id(self, id: int) -> SystemConfig | None:
        stmt = select(SystemConfig).where(SystemConfig.id == id)
        return (await self._s.execute(stmt)).scalars().first()

    async def insert_systemconfig(self, data: dict[str, Any]) -> None:
        stmt = insert(SystemConfig).values(**data)
        await self._s.execute(stmt)

    async def update_systemconfig(self, data: dict[str, Any]) -> None:
        stmt = update(SystemConfig).where(SystemConfig.id == data['id']).values(**data)
        await self._s.execute(stmt)

    async def batch_delete_systemconfig(self, ids: list[int]) -> None:
        stmt = delete(SystemConfig).where(SystemConfig.id.in_(ids))
        await self._s.execute(stmt)

    async def get_systemconfig_by_key(self, key: str) -> SystemConfig | None:
        stmt = select(SystemConfig).where(SystemConfig.config_key == key)
        return (await self._s.execute(stmt)).scalars().first()

    async def get_systemconfig_by_key(self, key: str) -> SystemConfig | None:
        stmt = select(SystemConfig).where(SystemConfig.config_key == key)
        return (await self._s.execute(stmt)).scalars().first()

    async def page_music(self, page: int, size: int, title: str|None, artist: str|None, is_visible: int|None) -> tuple[int, Sequence[Music]]:
        stmt = select(Music)
        count_stmt = select(func.count(Music.id))
        if title:
            stmt = stmt.where(Music.title.like(f"%{title}%"))
            count_stmt = count_stmt.where(Music.title.like(f"%{title}%"))
        if artist:
            stmt = stmt.where(Music.artist.like(f"%{artist}%"))
            count_stmt = count_stmt.where(Music.artist.like(f"%{artist}%"))
        if is_visible is not None:
            stmt = stmt.where(Music.is_visible == is_visible)
            count_stmt = count_stmt.where(Music.is_visible == is_visible)
            
        total = (await self._s.execute(count_stmt)).scalar() or 0
        stmt = stmt.limit(size).offset((page - 1) * size)
        records = (await self._s.execute(stmt)).scalars().all()
        return total, records