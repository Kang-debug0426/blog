
from .admin_repository import AdminSiteContentRepository
from .admin_schemas import *
from app.core.logging import get_logger
logger = get_logger(__name__)

class AdminSiteContentService:
    def __init__(self, repo: AdminSiteContentRepository):
        self._repo = repo

    async def get_personal_info(self) -> PersonalInfoEntity | None:
        r = await self._repo.get_personalinfo_by_id(1)
        return PersonalInfoEntity.model_validate(r) if r else None

    async def update_personal_info(self, dto: PersonalInfoDTO) -> None:
        data = dto.model_dump(exclude_unset=True)
        if 'create_time' in data: del data['create_time']
        if 'update_time' in data: del data['update_time']
        await self._repo.update_personalinfo(data)

    async def get_system_config_by_key(self, key: str) -> SystemConfigEntity | None:
        r = await self._repo.get_systemconfig_by_key(key)
        return SystemConfigEntity.model_validate(r) if r else None

    async def page_music(self, dto: MusicPageQueryDTO) -> PageResult:
        total, records = await self._repo.page_music(dto.page, dto.page_size, dto.title, dto.artist, dto.is_visible)
        return PageResult(total=total, records=[MusicEntity.model_validate(r) for r in records])

    async def get_all_skill(self) -> list[SkillEntity]:
        rs = await self._repo.get_all_skill()
        return [SkillEntity.model_validate(r) for r in rs]
        
    async def insert_skill(self, dto: SkillDTO) -> None:
        data = dto.model_dump(exclude_none=True)
        await self._repo.insert_skill(data)
        
    async def update_skill(self, dto: SkillDTO) -> None:
        data = dto.model_dump(exclude_unset=True)
        if 'create_time' in data: del data['create_time']
        if 'update_time' in data: del data['update_time']
        await self._repo.update_skill(data)
        
    async def batch_delete_skill(self, ids: list[int]) -> None:
        await self._repo.batch_delete_skill(ids)
        
    async def get_skill_by_id(self, id: int) -> SkillEntity | None:
        r = await self._repo.get_skill_by_id(id)
        return SkillEntity.model_validate(r) if r else None

    async def get_all_experience(self) -> list[ExperienceEntity]:
        rs = await self._repo.get_all_experience()
        return [ExperienceEntity.model_validate(r) for r in rs]
        
    async def insert_experience(self, dto: ExperienceDTO) -> None:
        data = dto.model_dump(exclude_none=True)
        await self._repo.insert_experience(data)
        
    async def update_experience(self, dto: ExperienceDTO) -> None:
        data = dto.model_dump(exclude_unset=True)
        if 'create_time' in data: del data['create_time']
        if 'update_time' in data: del data['update_time']
        await self._repo.update_experience(data)
        
    async def batch_delete_experience(self, ids: list[int]) -> None:
        await self._repo.batch_delete_experience(ids)
        
    async def get_experience_by_id(self, id: int) -> ExperienceEntity | None:
        r = await self._repo.get_experience_by_id(id)
        return ExperienceEntity.model_validate(r) if r else None

    async def get_all_socialmedia(self) -> list[SocialMediaEntity]:
        rs = await self._repo.get_all_socialmedia()
        return [SocialMediaEntity.model_validate(r) for r in rs]
        
    async def insert_socialmedia(self, dto: SocialMediaDTO) -> None:
        data = dto.model_dump(exclude_none=True)
        await self._repo.insert_socialmedia(data)
        
    async def update_socialmedia(self, dto: SocialMediaDTO) -> None:
        data = dto.model_dump(exclude_unset=True)
        if 'create_time' in data: del data['create_time']
        if 'update_time' in data: del data['update_time']
        await self._repo.update_socialmedia(data)
        
    async def batch_delete_socialmedia(self, ids: list[int]) -> None:
        await self._repo.batch_delete_socialmedia(ids)
        
    async def get_socialmedia_by_id(self, id: int) -> SocialMediaEntity | None:
        r = await self._repo.get_socialmedia_by_id(id)
        return SocialMediaEntity.model_validate(r) if r else None

    async def get_all_friendlink(self) -> list[FriendLinkEntity]:
        rs = await self._repo.get_all_friendlink()
        return [FriendLinkEntity.model_validate(r) for r in rs]
        
    async def insert_friendlink(self, dto: FriendLinkDTO) -> None:
        data = dto.model_dump(exclude_none=True)
        await self._repo.insert_friendlink(data)
        
    async def update_friendlink(self, dto: FriendLinkDTO) -> None:
        data = dto.model_dump(exclude_unset=True)
        if 'create_time' in data: del data['create_time']
        if 'update_time' in data: del data['update_time']
        await self._repo.update_friendlink(data)
        
    async def batch_delete_friendlink(self, ids: list[int]) -> None:
        await self._repo.batch_delete_friendlink(ids)
        
    async def get_friendlink_by_id(self, id: int) -> FriendLinkEntity | None:
        r = await self._repo.get_friendlink_by_id(id)
        return FriendLinkEntity.model_validate(r) if r else None

    async def get_all_systemconfig(self) -> list[SystemConfigEntity]:
        rs = await self._repo.get_all_systemconfig()
        return [SystemConfigEntity.model_validate(r) for r in rs]
        
    async def insert_systemconfig(self, dto: SystemConfigDTO) -> None:
        data = dto.model_dump(exclude_none=True)
        await self._repo.insert_systemconfig(data)
        
    async def update_systemconfig(self, dto: SystemConfigDTO) -> None:
        data = dto.model_dump(exclude_unset=True)
        if 'create_time' in data: del data['create_time']
        if 'update_time' in data: del data['update_time']
        await self._repo.update_systemconfig(data)
        
    async def batch_delete_systemconfig(self, ids: list[int]) -> None:
        await self._repo.batch_delete_systemconfig(ids)
        
    async def get_systemconfig_by_id(self, id: int) -> SystemConfigEntity | None:
        r = await self._repo.get_systemconfig_by_id(id)
        return SystemConfigEntity.model_validate(r) if r else None

    async def get_all_music(self) -> list[MusicEntity]:
        rs = await self._repo.get_all_music()
        return [MusicEntity.model_validate(r) for r in rs]
        
    async def insert_music(self, dto: MusicDTO) -> None:
        data = dto.model_dump(exclude_none=True)
        await self._repo.insert_music(data)
        
    async def update_music(self, dto: MusicDTO) -> None:
        data = dto.model_dump(exclude_unset=True)
        if 'create_time' in data: del data['create_time']
        if 'update_time' in data: del data['update_time']
        await self._repo.update_music(data)
        
    async def batch_delete_music(self, ids: list[int]) -> None:
        await self._repo.batch_delete_music(ids)
        
    async def get_music_by_id(self, id: int) -> MusicEntity | None:
        r = await self._repo.get_music_by_id(id)
        return MusicEntity.model_validate(r) if r else None
