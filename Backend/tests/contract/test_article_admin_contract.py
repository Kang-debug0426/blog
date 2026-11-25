"""文章管理端接口契约与业务逻辑完整性测试。

验证范围：
1. 路由注册与路径前缀对齐（/api/admin/article POST/PUT/DELETE 及 publish/top PUT）
2. ArticleDTO 对 tagIds 与 tagIdList 的双向别名兼容与解析
3. Service 层创建文章时的标签关联写入
4. Service 层更新文章时的标签替换与空标签清空
5. Service 层查询详情时的 tagIds 回显
6. Service 层批量删除时的标签级联删除
7. 发布切换与置顶切换的逻辑闭环
8. HTTP 请求级契约测试（TestClient）：
   - 未提供 Token 时返回 401 NotLogin
   - 携带有效 Token 访问 POST /api/admin/article 正确返回 Envelope(code=1)
   - 游客账号执行写操作返回 403 GuestReadOnly
"""
import pytest
from unittest.mock import AsyncMock, MagicMock
from fastapi import FastAPI, Depends, Header
from fastapi.testclient import TestClient

from app.modules.article.schemas import ArticleDTO, ArticleEntity, Envelope
from app.modules.article.service import ArticleService
from app.modules.article.router import admin_router, get_article_service
from app.core.deps import get_current_admin, CurrentAdmin, ROLE_ADMIN, ROLE_GUEST
from app.core.errors import register_exception_handlers


def test_article_dto_tag_alias_compatibility():
    """测试 tagIds 与 tagIdList 输入均能正确解析，输出保持 tagIds"""
    # 1. 前端传统格式：tagIds
    dto1 = ArticleDTO.model_validate({
        "title": "测试文章1",
        "slug": "test-1",
        "contentMarkdown": "# Hello",
        "categoryId": 1,
        "tagIds": [101, 102]
    })
    assert dto1.tag_id_list == [101, 102]
    dump1 = dto1.model_dump(by_alias=True)
    assert dump1.get("tagIds") == [101, 102]

    # 2. 新格式：tagIdList
    dto2 = ArticleDTO.model_validate({
        "title": "测试文章2",
        "slug": "test-2",
        "contentMarkdown": "# Hello 2",
        "categoryId": 2,
        "tagIdList": [201, 202]
    })
    assert dto2.tag_id_list == [201, 202]

    # 3. 空标签列表
    dto3 = ArticleDTO.model_validate({
        "title": "测试文章3",
        "slug": "test-3",
        "contentMarkdown": "# Hello 3",
        "categoryId": 1,
        "tagIds": []
    })
    assert dto3.tag_id_list == []

    # 4. 未提供标签
    dto4 = ArticleDTO.model_validate({
        "title": "测试文章4",
        "slug": "test-4",
        "contentMarkdown": "# Hello 4",
        "categoryId": 1
    })
    assert dto4.tag_id_list is None


def test_article_entity_tag_ids_serialization():
    """测试 ArticleEntity 正确包含并向前端序列化 tagIds"""
    ent = ArticleEntity.model_validate({
        "id": 10,
        "title": "已存文章",
        "slug": "existing",
        "tagIds": [5, 6, 7]
    })
    assert ent.tag_ids == [5, 6, 7]
    dumped = ent.model_dump(by_alias=True)
    assert dumped["tagIds"] == [5, 6, 7]


def test_router_endpoints_registration():
    """测试 admin_router 中注册的所有管理端路由及其 HTTP 方法"""
    routes = {
        (r.path, tuple(r.methods))
        for r in admin_router.routes
        if hasattr(r, "methods")
    }
    
    # 确认 5 个新补齐端点存在
    assert ("/article", ("POST",)) in routes
    assert ("/article", ("PUT",)) in routes
    assert ("/article", ("DELETE",)) in routes
    assert ("/article/publish/{id}", ("PUT",)) in routes
    assert ("/article/top/{id}", ("PUT",)) in routes

    # 确认原有查询端点依然完整
    assert ("/article/page", ("GET",)) in routes
    assert ("/article/search", ("GET",)) in routes
    assert ("/article/{id}", ("GET",)) in routes


@pytest.mark.asyncio
async def test_service_create_article_with_tags():
    """测试 Service 创建文章：文章写入 + 标签关联写入"""
    mock_repo = MagicMock()
    mock_article = MagicMock()
    mock_article.id = 99
    mock_repo.insert_article = AsyncMock(return_value=mock_article)
    mock_repo.batch_insert_article_tag_relations = AsyncMock()

    svc = ArticleService(mock_repo)
    dto = ArticleDTO.model_validate({
        "title": "新文章",
        "slug": "new-art",
        "contentMarkdown": "内容",
        "categoryId": 3,
        "isPublished": 1,
        "tagIds": [11, 22, 33]
    })

    await svc.create_article(dto)

    # 验证文章主体插入
    mock_repo.insert_article.assert_awaited_once()
    insert_data = mock_repo.insert_article.await_args[0][0]
    assert insert_data["title"] == "新文章"
    assert insert_data["is_published"] == 1
    assert "publish_time" in insert_data
    assert "tag_id_list" not in insert_data  # 确保不向 articles 表多余字段写入

    # 验证标签多对多关联插入
    mock_repo.batch_insert_article_tag_relations.assert_awaited_once_with(99, [11, 22, 33])


@pytest.mark.asyncio
async def test_service_update_article_replace_tags():
    """测试 Service 更新文章：先删旧标签，再全量插入新标签"""
    mock_repo = MagicMock()
    mock_repo.get_article_by_id = AsyncMock(return_value=MagicMock(publish_time=None))
    mock_repo.update_article = AsyncMock()
    mock_repo.delete_article_tag_relations_by_article_id = AsyncMock()
    mock_repo.batch_insert_article_tag_relations = AsyncMock()

    svc = ArticleService(mock_repo)
    dto = ArticleDTO.model_validate({
        "id": 99,
        "title": "更新文章",
        "slug": "new-art",
        "contentMarkdown": "新内容",
        "categoryId": 3,
        "tagIds": [44, 55]
    })

    await svc.update_article(dto)

    mock_repo.update_article.assert_awaited_once()
    # 验证先删后插
    mock_repo.delete_article_tag_relations_by_article_id.assert_awaited_once_with(99)
    mock_repo.batch_insert_article_tag_relations.assert_awaited_once_with(99, [44, 55])


@pytest.mark.asyncio
async def test_service_update_article_clear_tags():
    """测试 Service 更新文章时传空标签列表：清空关联且不执行批量插入"""
    mock_repo = MagicMock()
    mock_repo.get_article_by_id = AsyncMock(return_value=MagicMock(publish_time=None))
    mock_repo.update_article = AsyncMock()
    mock_repo.delete_article_tag_relations_by_article_id = AsyncMock()
    mock_repo.batch_insert_article_tag_relations = AsyncMock()

    svc = ArticleService(mock_repo)
    dto = ArticleDTO.model_validate({
        "id": 99,
        "title": "清空标签文章",
        "tagIds": []
    })

    await svc.update_article(dto)

    mock_repo.delete_article_tag_relations_by_article_id.assert_awaited_once_with(99)
    mock_repo.batch_insert_article_tag_relations.assert_not_awaited()


@pytest.mark.asyncio
async def test_service_get_by_id_returns_tag_ids():
    """测试 Service 根据 ID 查询文章详情正确回显 tagIds"""
    mock_repo = MagicMock()
    # 用标准类模拟 DB 返回的实体对象，避免 MagicMock 动态产生字段
    class MockArticleRow:
        id = 88
        title = "带标签文章"
        slug = "tagged-art"
        summary = "摘要"
        cover_image = None
        content_markdown = "MD"
        content_html = "<p>MD</p>"
        category_id = 2
        category_name = "后端"
        view_count = 0
        like_count = 0
        comment_count = 0
        word_count = 10
        reading_time = None
        is_published = 1
        is_top = 0
        publish_time = None
        publish_year = None
        publish_month = None
        publish_day = None
        publish_date = None
        create_time = None
        update_time = None

    mock_repo.get_article_by_id = AsyncMock(return_value=MockArticleRow())
    mock_repo.get_tag_ids_by_article_id = AsyncMock(return_value=[801, 802])

    svc = ArticleService(mock_repo)
    res = await svc.get_by_id(88)

    assert res is not None
    assert res.id == 88
    assert res.tag_ids == [801, 802]
    dumped = res.model_dump(by_alias=True)
    assert dumped["tagIds"] == [801, 802]


@pytest.mark.asyncio
async def test_service_batch_delete_cascade_tags():
    """测试 Service 批量删除文章时级联删除标签关联"""
    mock_repo = MagicMock()
    mock_repo.batch_delete_article_tag_relations_by_article_ids = AsyncMock()
    mock_repo.batch_delete_article = AsyncMock()

    svc = ArticleService(mock_repo)
    await svc.batch_delete_article([10, 20, 30])

    mock_repo.batch_delete_article_tag_relations_by_article_ids.assert_awaited_once_with([10, 20, 30])
    mock_repo.batch_delete_article.assert_awaited_once_with([10, 20, 30])


@pytest.mark.asyncio
async def test_service_toggle_publish_and_top():
    """测试发布切换与置顶切换正确下发至仓储层"""
    mock_repo = MagicMock()
    mock_article = MagicMock(publish_time=None)
    mock_repo.get_article_by_id = AsyncMock(return_value=mock_article)
    mock_repo.update_article = AsyncMock()
    mock_repo.publish_or_cancel = AsyncMock()
    mock_repo.toggle_top = AsyncMock()

    svc = ArticleService(mock_repo)

    # 首次发布补时间
    await svc.publish_or_cancel(1, 1)
    mock_repo.update_article.assert_awaited_once()

    # 取消发布
    await svc.publish_or_cancel(1, 0)
    mock_repo.publish_or_cancel.assert_awaited_once_with(1, 0)

    # 置顶切换
    await svc.toggle_top(1, 1)
    mock_repo.toggle_top.assert_awaited_once_with(1, 1)


def test_http_contract_via_testclient():
    """使用 TestClient 模拟 HTTP 请求，全面验证路由挂载、鉴权拦截与成功响应信封"""
    app = FastAPI()
    register_exception_handlers(app)
    app.include_router(admin_router, prefix="/api/admin")

    # 1. 模拟未携带 Token 请求 POST /api/admin/article -> 必须 401
    client = TestClient(app)
    resp_unauth = client.post("/api/admin/article", json={"title": "Test", "slug": "test"})
    assert resp_unauth.status_code == 401
    assert resp_unauth.json()["code"] == 0

    # 2. 模拟管理员登录身份 (role = 1) -> POST /api/admin/article 必须返回 200 及 Envelope
    mock_service = MagicMock()
    mock_service.create_article = AsyncMock()
    mock_service.update_article = AsyncMock()
    mock_service.batch_delete_article = AsyncMock()
    mock_service.publish_or_cancel = AsyncMock()
    mock_service.toggle_top = AsyncMock()

    app.dependency_overrides[get_current_admin] = lambda: CurrentAdmin(admin_id=1, role=ROLE_ADMIN)
    app.dependency_overrides[get_article_service] = lambda: mock_service

    auth_client = TestClient(app)

    # 测试 POST 创建文章
    create_payload = {
        "title": "发布好文",
        "slug": "good-article",
        "contentMarkdown": "正文内容",
        "categoryId": 5,
        "isPublished": 1,
        "tagIds": [1, 2, 3]
    }
    resp_create = auth_client.post("/api/admin/article", json=create_payload)
    assert resp_create.status_code == 200
    assert resp_create.json() == {"code": 1, "msg": None, "data": None}
    mock_service.create_article.assert_awaited_once()

    # 测试 PUT 更新文章
    update_payload = {
        "id": 12,
        "title": "更新好文",
        "slug": "good-article",
        "contentMarkdown": "更新后的正文",
        "tagIdList": [3, 4]  # 兼容 tagIdList
    }
    resp_update = auth_client.put("/api/admin/article", json=update_payload)
    assert resp_update.status_code == 200
    assert resp_update.json() == {"code": 1, "msg": None, "data": None}
    mock_service.update_article.assert_awaited_once()

    # 测试 DELETE 批量删除
    resp_delete = auth_client.delete("/api/admin/article?ids=12,13")
    assert resp_delete.status_code == 200
    assert resp_delete.json() == {"code": 1, "msg": None, "data": None}
    mock_service.batch_delete_article.assert_awaited_once_with([12, 13])

    # 测试 PUT 发布切换
    resp_pub = auth_client.put("/api/admin/article/publish/12?isPublished=1")
    assert resp_pub.status_code == 200
    assert resp_pub.json() == {"code": 1, "msg": None, "data": None}
    mock_service.publish_or_cancel.assert_awaited_once_with(12, 1)

    # 测试 PUT 置顶切换
    resp_top = auth_client.put("/api/admin/article/top/12?isTop=1")
    assert resp_top.status_code == 200
    assert resp_top.json() == {"code": 1, "msg": None, "data": None}
    mock_service.toggle_top.assert_awaited_once_with(12, 1)

    # 3. 模拟游客身份 (role = 0) 执行 POST 写操作 -> 必须返回 403 游客只读
    from app.core.errors import GuestReadOnlyException, MSG_GUEST_READONLY
    def guest_admin_mock(request=None):
        raise GuestReadOnlyException(MSG_GUEST_READONLY)
    app.dependency_overrides[get_current_admin] = guest_admin_mock

    guest_client = TestClient(app)
    resp_guest = guest_client.post("/api/admin/article", json=create_payload)
    assert resp_guest.status_code == 403
    assert resp_guest.json()["code"] == 0
    assert "游客" in resp_guest.json()["msg"]


@pytest.mark.asyncio
async def test_service_get_by_slug_with_tags_and_category():
    """测试公开详情按 Slug 查询：正确组装分类名称和标签名称列表"""
    class MockCategory:
        id = 1
        name = "技术"

    class MockTag:
        def __init__(self, name):
            self.name = name

    class MockArticle:
        id = 20
        title = "公开文章"
        slug = "public-article"
        summary = "摘要"
        cover_image = ""
        content_markdown = "# 正文"
        content_html = "<p>正文</p>"
        category_id = 1
        category_name = None
        view_count = 10
        like_count = 5
        comment_count = 2
        word_count = 100
        reading_time = 1
        is_published = 1
        is_top = 0
        publish_time = "2026-10-14 00:00:00"
        update_time = None

    mock_repo = MagicMock()
    mock_repo.get_article_by_slug = AsyncMock(return_value=MockArticle())
    mock_repo.get_all_articlecategory = AsyncMock(return_value=[MockCategory()])
    mock_repo.get_tags_by_article_id = AsyncMock(return_value=[MockTag("个人"), MockTag("学习")])

    svc = ArticleService(mock_repo)
    res = await svc.get_by_slug("public-article")

    assert res is not None
    assert res.id == 20
    assert res.category_name == "技术"
    assert res.tag_names == ["个人", "学习"]
    dumped = res.model_dump(by_alias=True)
    assert dumped["categoryName"] == "技术"
    assert dumped["tagNames"] == ["个人", "学习"]


@pytest.mark.asyncio
async def test_service_get_by_slug_without_tags():
    """测试公开详情文章无标签时：tag_names 正常回退为空列表 []"""
    class MockArticleNoTags:
        id = 21
        title = "无标签文章"
        slug = "no-tags-article"
        summary = ""
        cover_image = ""
        content_markdown = "MD"
        content_html = "<p>MD</p>"
        category_id = None
        category_name = None
        view_count = 0
        like_count = 0
        comment_count = 0
        word_count = 20
        reading_time = 1
        is_published = 1
        is_top = 0
        publish_time = None
        update_time = None

    mock_repo = MagicMock()
    mock_repo.get_article_by_slug = AsyncMock(return_value=MockArticleNoTags())
    mock_repo.get_tags_by_article_id = AsyncMock(return_value=[])

    svc = ArticleService(mock_repo)
    res = await svc.get_by_slug("no-tags-article")

    assert res is not None
    assert res.id == 21
    assert res.category_name is None
    assert res.tag_names == []
    dumped = res.model_dump(by_alias=True)
    assert dumped["tagNames"] == []


@pytest.mark.asyncio
async def test_service_get_by_slug_not_found():
    """测试公开详情文章不存在时返回 None"""
    mock_repo = MagicMock()
    mock_repo.get_article_by_slug = AsyncMock(return_value=None)

    svc = ArticleService(mock_repo)
    res = await svc.get_by_slug("non-existent")
    assert res is None


@pytest.mark.asyncio
async def test_service_get_by_slug_propagates_tag_query_db_error():
    """测试标签查询发生数据库异常时：必须如实抛出，严禁私自吞没为假空列表"""
    class MockArticle:
        id = 30
        title = "异常测试"
        slug = "db-err-test"
        category_id = None
        category_name = None
        is_published = 1
        is_top = 0

    mock_repo = MagicMock()
    mock_repo.get_article_by_slug = AsyncMock(return_value=MockArticle())
    # 模拟底层数据库断开或 SQL 查询错误
    mock_repo.get_tags_by_article_id = AsyncMock(side_effect=RuntimeError("Database connection lost"))

    svc = ArticleService(mock_repo)
    with pytest.raises(RuntimeError, match="Database connection lost"):
        await svc.get_by_slug("db-err-test")


@pytest.mark.asyncio
async def test_service_get_by_slug_propagates_category_query_db_error():
    """测试分类查询发生数据库异常时：必须如实抛出，严禁私自吞没"""
    class MockArticle:
        id = 31
        title = "分类异常测试"
        slug = "cat-err-test"
        category_id = 1
        category_name = None
        is_published = 1
        is_top = 0

    mock_repo = MagicMock()
    mock_repo.get_article_by_slug = AsyncMock(return_value=MockArticle())
    # 模拟分类查询故障
    mock_repo.get_all_articlecategory = AsyncMock(side_effect=RuntimeError("Category table lock timeout"))

    svc = ArticleService(mock_repo)
    with pytest.raises(RuntimeError, match="Category table lock timeout"):
        await svc.get_by_slug("cat-err-test")


def test_ai_status_contract_endpoint():
    """测试 AI 状态探测端点契约：
    1. 挂载在 /api/admin/ai/status
    2. 未登录访问返回 401（符合管理员鉴权约定）
    3. 管理员鉴权访问返回 200，信封 data == {'enabled': False, 'modelName': ''}
    """
    from app.modules.misc.router import router as misc_router
    app = FastAPI()
    register_exception_handlers(app)
    app.include_router(misc_router, prefix="/api")

    client = TestClient(app)

    # 1. 未登录 -> 401
    resp_unauth = client.get("/api/admin/ai/status")
    assert resp_unauth.status_code == 401
    assert resp_unauth.json()["code"] == 0

    # 2. 管理员已登录 -> 200
    app.dependency_overrides[get_current_admin] = lambda: CurrentAdmin(admin_id=1, role=ROLE_ADMIN)
    auth_client = TestClient(app)
    resp = auth_client.get("/api/admin/ai/status")
    assert resp.status_code == 200
    res_data = resp.json()
    assert res_data == {
        "code": 1,
        "msg": None,
        "data": {
            "enabled": False,
            "modelName": ""
        }
    }


@pytest.mark.asyncio
async def test_service_create_article_populates_create_and_update_time():
    """测试创建文章时自动补齐 create_time 与 update_time，杜绝 NULL 产生"""
    mock_repo = MagicMock()
    mock_article = MagicMock()
    mock_article.id = 100
    mock_repo.insert_article = AsyncMock(return_value=mock_article)
    mock_repo.batch_insert_article_tag_relations = AsyncMock()

    svc = ArticleService(mock_repo)
    dto = ArticleDTO.model_validate({
        "title": "新时间文章",
        "slug": "time-art",
        "contentMarkdown": "MD",
        "categoryId": 1
    })

    await svc.create_article(dto)

    insert_data = mock_repo.insert_article.await_args[0][0]
    assert insert_data.get("create_time") is not None
    assert insert_data.get("update_time") is not None


@pytest.mark.asyncio
async def test_service_update_article_refreshes_update_time():
    """测试更新文章时自动刷新 update_time"""
    mock_repo = MagicMock()
    mock_repo.update_article = AsyncMock()

    svc = ArticleService(mock_repo)
    dto = ArticleDTO.model_validate({
        "id": 100,
        "title": "更新时间文章"
    })

    await svc.update_article(dto)

    update_data = mock_repo.update_article.await_args[0][0]
    assert update_data.get("update_time") is not None


def test_article_ordering_contract_rules():
    """测试排序规则定义：置顶优先、发布/创建时间降序、ID次级降序消除漂移"""
    import datetime
    from app.modules.article.repository import ArticleRepository

    mock_session = MagicMock()
    repo = ArticleRepository(mock_session)

    # 模拟多篇文章对象，包含置顶、普通、草稿、相同时间等场景
    t1 = datetime.datetime(2026, 10, 14, 12, 0, 0)
    t2 = datetime.datetime(2026, 10, 14, 10, 0, 0)
    t3 = datetime.datetime(2026, 9, 21, 23, 0, 0)

    # 排序优先级计算函数（模拟 SQL 中的 is_top desc, coalesce(publish_time, create_time) desc, id desc）
    def sort_key(a):
        primary_time = a.get("publish_time") or a.get("create_time")
        # is_top (0/1), primary_time, id
        return (a.get("is_top", 0), primary_time, a.get("id"))

    articles = [
        {"id": 19, "title": "旧文章", "is_top": 0, "publish_time": t3, "create_time": t3},
        {"id": 20, "title": "最新文章(原create_time为None)", "is_top": 0, "publish_time": t1, "create_time": None},
        {"id": 10, "title": "置顶旧文章", "is_top": 1, "publish_time": t3, "create_time": t3},
        {"id": 21, "title": "草稿新文章(无publish_time)", "is_top": 0, "publish_time": None, "create_time": t2},
        {"id": 22, "title": "同一秒发布的文章A", "is_top": 0, "publish_time": t1, "create_time": t1},
    ]

    # 按上述规则降序排序
    sorted_arts = sorted(articles, key=sort_key, reverse=True)

    # 1. 置顶文章必定在最前
    assert sorted_arts[0]["id"] == 10
    # 2. 最新发布的文章（ID 20 和 22 都是 t1）紧随其后，且 ID 较大者排前消除漂移
    assert sorted_arts[1]["id"] == 22
    assert sorted_arts[2]["id"] == 20
    # 3. 稍早创建的草稿（t2）在较旧文章之前
    assert sorted_arts[3]["id"] == 21
    # 4. 最旧的文章在最后
    assert sorted_arts[4]["id"] == 19

