
from fastapi import APIRouter, Depends, Query
from typing import Annotated
from app.core.deps import get_db_session
from app.modules.auth.router import get_current_admin, CurrentAdmin
from app.core.errors import Envelope
from app.core.legacy_types import LegacyIdList
from .admin_service import AdminSiteContentService
from .admin_repository import AdminSiteContentRepository
from .admin_schemas import *

router = APIRouter(tags=["site-content-admin"])
AdminDep = Annotated[CurrentAdmin, Depends(get_current_admin)]

async def get_admin_svc(s: Annotated[object, Depends(get_db_session)]) -> AdminSiteContentService:
    return AdminSiteContentService(AdminSiteContentRepository(s))

SvcDep = Annotated[AdminSiteContentService, Depends(get_admin_svc)]

@router.get("/personalInfo", response_model=Envelope)
async def get_personal_info(_: AdminDep, svc: SvcDep):
    return Envelope(data=await svc.get_personal_info())

@router.put("/personalInfo", response_model=Envelope)
async def update_personal_info(dto: PersonalInfoDTO, _: AdminDep, svc: SvcDep):
    await svc.update_personal_info(dto)
    return Envelope(data=None)

@router.get("/systemConfig/key/{config_key}", response_model=Envelope)
async def get_config_by_key(config_key: str, _: AdminDep, svc: SvcDep):
    return Envelope(data=await svc.get_system_config_by_key(config_key))

@router.get("/music/page", response_model=Envelope)
async def get_music_page(dto: Annotated[MusicPageQueryDTO, Query()], _: AdminDep, svc: SvcDep):
    return Envelope(data=await svc.page_music(dto))

@router.get("/skill", response_model=Envelope)
async def get_all_skill(_: AdminDep, svc: SvcDep):
    return Envelope(data=await svc.get_all_skill())

@router.post("/skill", response_model=Envelope)
async def insert_skill(dto: SkillDTO, _: AdminDep, svc: SvcDep):
    await svc.insert_skill(dto)
    return Envelope(data=None)
        
@router.put("/skill", response_model=Envelope)
async def update_skill(dto: SkillDTO, _: AdminDep, svc: SvcDep):
    await svc.update_skill(dto)
    return Envelope(data=None)
        
@router.delete("/skill", response_model=Envelope)
async def delete_skill(ids: Annotated[LegacyIdList, Query()], _: AdminDep, svc: SvcDep):
    await svc.batch_delete_skill(ids)
    return Envelope(data=None)
        
@router.get("/skill/{id}", response_model=Envelope)
async def get_skill_by_id(id: int, _: AdminDep, svc: SvcDep):
    return Envelope(data=await svc.get_skill_by_id(id))

@router.get("/experience", response_model=Envelope)
async def get_all_experience(_: AdminDep, svc: SvcDep):
    return Envelope(data=await svc.get_all_experience())

@router.post("/experience", response_model=Envelope)
async def insert_experience(dto: ExperienceDTO, _: AdminDep, svc: SvcDep):
    await svc.insert_experience(dto)
    return Envelope(data=None)
        
@router.put("/experience", response_model=Envelope)
async def update_experience(dto: ExperienceDTO, _: AdminDep, svc: SvcDep):
    await svc.update_experience(dto)
    return Envelope(data=None)
        
@router.delete("/experience", response_model=Envelope)
async def delete_experience(ids: Annotated[LegacyIdList, Query()], _: AdminDep, svc: SvcDep):
    await svc.batch_delete_experience(ids)
    return Envelope(data=None)
        
@router.get("/experience/{id}", response_model=Envelope)
async def get_experience_by_id(id: int, _: AdminDep, svc: SvcDep):
    return Envelope(data=await svc.get_experience_by_id(id))

@router.get("/socialMedia", response_model=Envelope)
async def get_all_socialmedia(_: AdminDep, svc: SvcDep):
    return Envelope(data=await svc.get_all_socialmedia())

@router.post("/socialMedia", response_model=Envelope)
async def insert_socialmedia(dto: SocialMediaDTO, _: AdminDep, svc: SvcDep):
    await svc.insert_socialmedia(dto)
    return Envelope(data=None)
        
@router.put("/socialMedia", response_model=Envelope)
async def update_socialmedia(dto: SocialMediaDTO, _: AdminDep, svc: SvcDep):
    await svc.update_socialmedia(dto)
    return Envelope(data=None)
        
@router.delete("/socialMedia", response_model=Envelope)
async def delete_socialmedia(ids: Annotated[LegacyIdList, Query()], _: AdminDep, svc: SvcDep):
    await svc.batch_delete_socialmedia(ids)
    return Envelope(data=None)
        
@router.get("/socialMedia/{id}", response_model=Envelope)
async def get_socialmedia_by_id(id: int, _: AdminDep, svc: SvcDep):
    return Envelope(data=await svc.get_socialmedia_by_id(id))

@router.get("/systemConfig", response_model=Envelope)
async def get_all_systemconfig(_: AdminDep, svc: SvcDep):
    return Envelope(data=await svc.get_all_systemconfig())

@router.post("/systemConfig", response_model=Envelope)
async def insert_systemconfig(dto: SystemConfigDTO, _: AdminDep, svc: SvcDep):
    await svc.insert_systemconfig(dto)
    return Envelope(data=None)
        
@router.put("/systemConfig", response_model=Envelope)
async def update_systemconfig(dto: SystemConfigDTO, _: AdminDep, svc: SvcDep):
    await svc.update_systemconfig(dto)
    return Envelope(data=None)
        
@router.delete("/systemConfig", response_model=Envelope)
async def delete_systemconfig(ids: Annotated[LegacyIdList, Query()], _: AdminDep, svc: SvcDep):
    await svc.batch_delete_systemconfig(ids)
    return Envelope(data=None)
        
@router.get("/systemConfig/{id}", response_model=Envelope)
async def get_systemconfig_by_id(id: int, _: AdminDep, svc: SvcDep):
    return Envelope(data=await svc.get_systemconfig_by_id(id))

@router.get("/friendLink", response_model=Envelope)
async def get_all_friendlink(_: AdminDep, svc: SvcDep):
    return Envelope(data=await svc.get_all_friendlink())

@router.post("/friendLink", response_model=Envelope)
async def insert_friendlink(dto: FriendLinkDTO, _: AdminDep, svc: SvcDep):
    await svc.insert_friendlink(dto)
    return Envelope(data=None)
        
@router.put("/friendLink", response_model=Envelope)
async def update_friendlink(dto: FriendLinkDTO, _: AdminDep, svc: SvcDep):
    await svc.update_friendlink(dto)
    return Envelope(data=None)
        
@router.delete("/friendLink", response_model=Envelope)
async def delete_friendlink(ids: Annotated[LegacyIdList, Query()], _: AdminDep, svc: SvcDep):
    await svc.batch_delete_friendlink(ids)
    return Envelope(data=None)
        
@router.get("/friendLink/{id}", response_model=Envelope)
async def get_friendlink_by_id(id: int, _: AdminDep, svc: SvcDep):
    return Envelope(data=await svc.get_friendlink_by_id(id))

@router.post("/music", response_model=Envelope)
async def insert_music(dto: MusicDTO, _: AdminDep, svc: SvcDep):
    await svc.insert_music(dto)
    return Envelope(data=None)
        
@router.put("/music", response_model=Envelope)
async def update_music(dto: MusicDTO, _: AdminDep, svc: SvcDep):
    await svc.update_music(dto)
    return Envelope(data=None)
        
@router.delete("/music", response_model=Envelope)
async def delete_music(ids: Annotated[LegacyIdList, Query()], _: AdminDep, svc: SvcDep):
    await svc.batch_delete_music(ids)
    return Envelope(data=None)
        
@router.get("/music/{id}", response_model=Envelope)
async def get_music_by_id(id: int, _: AdminDep, svc: SvcDep):
    return Envelope(data=await svc.get_music_by_id(id))
