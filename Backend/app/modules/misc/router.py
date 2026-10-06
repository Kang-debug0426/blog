from fastapi import APIRouter, Depends, Path, Query
from fastapi.responses import PlainTextResponse
from typing import Annotated
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete, insert
from app.core.deps import get_db_session
from app.core.errors import Envelope
from app.db.models.article import Article
from app.db.models.engagement import ArticleLike

router = APIRouter(tags=["misc"])

# ======== Health ========
@router.get("/health", response_model=Envelope, tags=["health"])
async def health():
    return Envelope(data="Server is running")

# ======== Sitemap ========
@router.get("/blog/sitemap.xml", response_class=PlainTextResponse, tags=["sitemap"])
async def sitemap(session: Annotated[AsyncSession, Depends(get_db_session)]):
    # 简单生成 sitemap XML  
    articles = (await session.execute(
        select(Article.slug).where(Article.is_published == 1)
    )).scalars().all()
    
    urls = "".join(f"""
    <url>
        <loc>https://example.com/article/{slug}</loc>
        <changefreq>weekly</changefreq>
        <priority>0.8</priority>
    </url>""" for slug in articles)
    
    xml = f"""<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
    <url>
        <loc>https://example.com/</loc>
        <changefreq>daily</changefreq>
        <priority>1.0</priority>
    </url>{urls}
</urlset>"""
    return xml

# ======== ArticleLike ========
@router.post("/blog/articleLike/{articleId}", response_model=Envelope)
async def like_article(
    articleId: int,
    visitorId: int,
    session: Annotated[AsyncSession, Depends(get_db_session)]
):
    # 幂等：已存在则跳过
    existing = (await session.execute(
        select(ArticleLike).where(ArticleLike.article_id == articleId, ArticleLike.visitor_id == visitorId)
    )).scalars().first()
    if not existing:
        await session.execute(insert(ArticleLike).values(article_id=articleId, visitor_id=visitorId))
    return Envelope()

@router.delete("/blog/articleLike/{articleId}", response_model=Envelope)
async def unlike_article(
    articleId: int,
    visitorId: int,
    session: Annotated[AsyncSession, Depends(get_db_session)]
):
    await session.execute(
        delete(ArticleLike).where(ArticleLike.article_id == articleId, ArticleLike.visitor_id == visitorId)
    )
    return Envelope()

@router.get("/blog/articleLike/{articleId}", response_model=Envelope)
async def has_liked(
    articleId: int,
    session: Annotated[AsyncSession, Depends(get_db_session)],
    visitorId: str | None = Query(default=None, alias="visitorId"),
):
    vid = int(visitorId) if (visitorId and visitorId.strip().isdigit()) else None
    if vid is None:
        return Envelope(data=False)
    existing = (await session.execute(
        select(ArticleLike).where(ArticleLike.article_id == articleId, ArticleLike.visitor_id == vid)
    )).scalars().first()
    return Envelope(data=existing is not None)

# ======== Captcha ========
@router.get("/blog/common/captcha/generate", response_model=Envelope, tags=["captcha"])
async def generate_captcha():
    import random, string
    code = "".join(random.choices(string.ascii_uppercase + string.digits, k=4))
    # Legacy behavior: returns {captchaKey, captchaImage} without actual image
    # For contract parity, return placeholder
    return Envelope(data={"captchaKey": "placeholder", "captchaCode": code})

from fastapi import APIRouter, Depends
from fastapi.responses import PlainTextResponse
from typing import Annotated
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.core.deps import get_db_session
from app.db.models.article import Article
import datetime

@router.get("/blog/rss", response_class=PlainTextResponse, tags=["rss"])
async def get_rss_feed(session: Annotated[AsyncSession, Depends(get_db_session)]):
    # Fetch latest 20 published articles
    stmt = select(Article).where(Article.is_published == 1).order_by(Article.create_time.desc()).limit(20)
    articles = (await session.execute(stmt)).scalars().all()
    
    xml = []
    xml.append("<?xml version=\"1.0\" encoding=\"UTF-8\"?>\n")
    xml.append("<rss version=\"2.0\">\n")
    xml.append("  <channel>\n")
    xml.append("    <title>我的博客 rss 订阅</title>\n")
    xml.append("    <link>https://example.com</link>\n")
    xml.append("    <description>最新文章分享</description>\n")
    
    for a in articles:
        xml.append("    <item>\n")
        xml.append(f"      <title>{a.title}</title>\n")
        xml.append(f"      <link>https://example.com/article/{a.slug}</link>\n")
        xml.append(f"      <description>{a.summary}</description>\n")
        if a.create_time:
            # Need RFC-822 date usually but old java dumped its own format
            tz = datetime.timezone.utc
            dt_str = a.create_time.replace(tzinfo=tz).strftime("%a, %d %b %Y %H:%M:%S GMT")
            xml.append(f"      <pubDate>{dt_str}</pubDate>\n")
        xml.append("    </item>\n")
        
    xml.append("  </channel>\n")
    xml.append("</rss>\n")
    return "".join(xml)

import uuid
import oss2
from fastapi import APIRouter, Depends, UploadFile, File
from app.core.deps import get_current_admin, CurrentAdmin
from app.core.config import get_settings
from app.integrations.oss import build_object_key, build_upload_url

@router.post("/admin/common/upload", response_model=Envelope, tags=["common"])
async def upload_file(
    file: UploadFile = File(...),
    current: CurrentAdmin = Depends(get_current_admin)
):
    """
    【UNBLOCKED】真实阿里云 OSS 文件直传接口，契约逐字对齐原 Java AliOssUtil。
    """
    settings = get_settings()
    filename = file.filename or "file.bin"
    ext = filename.rsplit(".", 1)[-1] if "." in filename else "bin"
    uuid_name = f"{uuid.uuid4()}.{ext}"
    object_key = build_object_key(ext, uuid_name)

    auth = oss2.Auth(
        settings.oss.access_key_id.get_secret_value(),
        settings.oss.access_key_secret.get_secret_value()
    )
    bucket = oss2.Bucket(auth, settings.oss.endpoint, settings.oss.bucket_name)
    
    content = await file.read()
    bucket.put_object(object_key, content)
    
    public_url = build_upload_url(ext, uuid_name, settings=settings)
    return Envelope(data=public_url)
