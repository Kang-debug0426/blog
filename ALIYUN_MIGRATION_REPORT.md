# 阿里云 IMCJK 生产迁移完成报告

**服务器**：120.27.112.41（iZm5e622i5vxiledkrx31lZ，2C2G，Ubuntu 24.04.3）
**迁移结果**：老 Java（Spring Boot 5922）已下线，FastAPI 已接管全部正式域名
**报告时间**：2026-10-05 20:2x（CST）

---

## 一、最终架构

```
公网用户
   │
   ▼
Nginx 1.28.0  (80 / 443, TLS, 由宝塔管理)
   ├── blog.imcjk.top   → /www/wwwroot/blog.imcjk.top   + /api/ → 127.0.0.1:8082/api/
   ├── admin.imcjk.top  → /www/wwwroot/admin.imcjk.top  + /api/ → 127.0.0.1:8082/api/
   ├── imcjk.top        → /www/wwwroot/imcjk.top        + /api/ → 127.0.0.1:8082/api/
   └── cv.imcjk.top     → /www/wwwroot/cv.imcjk.top     + /api/ → 127.0.0.1:8082/api/
   │
   ▼
FastAPI / Uvicorn  127.0.0.1:8082  --workers 1   (systemd: imcjk-fastapi.service)
   ├── config : /www/server/imcjk-backend/.env  (600)
   ├── code   : /www/server/imcjk-backend/app
   ├── venv   : /www/server/imcjk-backend/.venv  (Python 3.12.3)
   ├── MySQL  : 127.0.0.1:3306  feitwnd  (19 表)
   └── Redis  : 127.0.0.1:6379  DB 1  prefix imcjk:
```

---

## 二、公网实测验收（全部通过）

| 项目 | 结果 |
|---|---|
| DNS 解析（4 域名） | 全部 → 120.27.112.41 |
| `https://blog.imcjk.top/api/health` | **200** `{"code":1,"msg":null,"data":"Server is running"}` |
| `https://admin.imcjk.top/api/health` | **200** |
| `https://imcjk.top/api/health` | **200** |
| `https://cv.imcjk.top/api/health` | **200** |
| 4 端首页 HTML | 全部 **200** |
| 文章分页 `/api/blog/article/page` | **200**，total=16，title/categoryName/tagNames/publishTime 完整 |
| CV 个人信息 `/api/cv/personalInfo` | **200** |
| 门户/博客个人信息 | **200** |
| Sitemap / RSS | **200**，XML 合法 |
| 管理后台登录 | **200**，签发 JWT（adminRole=1） |
| 后台写入 + 回读 | **200 / 200**，MySQL 物理落盘 `FastAPI cutover verified` |
| WebSocket 直连 `ws://127.0.0.1:8082/api/ws/online` | 首帧 `1`，ping→`pong` |
| WebSocket 公网 `wss://blog.imcjk.top/api/ws/online` | 首帧 `1` |
| 阿里云 OSS 真实上传 | **200**，返回真实 URL，公网读取 **200** 内容一致 |
| HTTP→HTTPS 跳转 | admin 301；其余沿用原行为 |

---

## 三、资源占用（2C2G）

```
Mem:  总 1.6Gi | 已用 1.0Gi | free 369Mi | buff/cache 377Mi | 可用 582Mi
Swap: 1.0Gi | 已用 0B
```

| 进程 | RSS |
|---|---|
| mysqld | 393 MB |
| uvicorn (FastAPI) | 104 MB |
| BT-Panel（宝塔） | 45 MB |
| dockerd | 33 MB |
| nginx × 2 worker | 63 MB |

**对比迁移前**：可用内存 179 MB → **582 MB（+225%）**；Java 单进程曾占用 344 MB，已完全释放。

---

## 四、本次实际变更清单（可回滚）

| # | 变更 | 回滚方式 |
|---|---|---|
| 1 | 新建 `/www/server/imcjk-backend/`（代码 + .venv + .env） | 删除目录即可 |
| 2 | 新建 `/etc/systemd/system/imcjk-fastapi.service` | `systemctl disable --now` |
| 3 | 4 个正式 vhost 反代 5922 → `8082/api/` | `cp *.bak_pre_fastapi` 覆盖并 reload |
| 4 | 4 个前端 `index.html` 注入 `<meta name="referrer" content="no-referrer">` | 删除该行 |
| 5 | MySQL `feitwnd.admin` 新增列 `password_algo varchar(20) NOT NULL DEFAULT 'sha256'` | 老 Java 自动忽略，可保留 |
| 6 | 禁用 4 个 `spring_FeiTwnd-*.service`（systemd） | `systemctl enable --now` |
| 7 | 宝塔 Supervisor `home-java` 配置改名为 `home-java.ini.disabled` | 改名还原 + `supervisorctl reread/update` |
| 8 | 新增 `/www/server/panel/vhost/nginx/imcjk_staging_coexist.conf`（9090-9093 测试入口，现已冗余） | 删除该文件 + reload |

---

## 五、一键回滚到老 Java（约 60 秒）

```bash
# 1) 恢复 Nginx 反代
cd /www/server/panel/vhost/nginx
for v in admin.imcjk.top.conf www.blog.imcjk.top.conf imcjk.top.conf cv.imcjk.top.conf; do
  [ -f "$v.bak_pre_fastapi" ] && cp "$v.bak_pre_fastapi" "$v"
done
/www/server/nginx/sbin/nginx -t && /www/server/nginx/sbin/nginx -s reload

# 2) 恢复 Java（Supervisor）
cd /www/server/panel/plugin/supervisor/profile
mv home-java.ini.disabled home-java.ini
SC=/www/server/panel/pyenv/bin/supervisorctl; CFG=/etc/supervisor/supervisord.conf
$SC -c $CFG reread && $SC -c $CFG update

# 3) 验证
for d in blog.imcjk.top admin.imcjk.top imcjk.top cv.imcjk.top; do
  echo "$d -> $(curl -sk -o /dev/null -w %{http_code} --resolve $d:443:127.0.0.1 https://$d/api/health)"
done
```

也可直接停 FastAPI 后拉起 Java：
```bash
systemctl stop imcjk-fastapi.service
cd /www/server && nohup /usr/bin/java -Xms256m -Xmx512m \
  -jar /www/server/FeiTwnd-server-single-20260319-final-v2.jar >> /www/server/backend.log 2>&1 &
```

---

## 六、事故记录（必须知悉）

**发生时段**：约 19:25 – 20:21（CST），**正式站点不可访问约 55 分钟**。

**根因**：2C2G 物理内存被 Java(344MB) + MySQL(393MB) + 宝塔(124MB) + FastAPI(104MB) 占满，
触发内存耗尽 + Swap 抖动，内核存活（ping/TCP 正常）但**所有用户态进程（sshd/nginx/mysql）无法调度**，
表现为 SSH 无横幅、HTTP 全超时。

**恢复**：实例重启后自动恢复；随后禁用 Java 自动拉起，内存释放至可用 582MB，彻底消除复发条件。

> **结论：2C2G 下 Java 与 FastAPI 绝不可同时常驻** —— 现已只保留 FastAPI。

---

## 六·补、切换后修复：F12 控制台 400 报错（已解决）

**现象**：每个域名 F12 都报 `Failed to load resource: the server responded with a status of 400`。

**定位**：400 来自 `POST /api/{blog,home,cv}/visitor/record`（访客指纹上报），最近日志 8 次全部命中该端点。

**根因**（Pydantic v2 严格校验 vs 旧 Java Jackson 宽松转换）：

| 前端实际发送 | 后端原声明 | 结果 |
|---|---|---|
| `deviceMemory: 8`（数字） | `str \| None` | ✗ 校验失败 → 400 |
| `hardwareConcurrency: 8`（数字） | `str \| None` | ✗ 校验失败 → 400 |
| `colorDepth: 24`（数字，部分端） | `str \| None` | ✗ 校验失败 → 400 |

旧 Java 的 Jackson 会把数字自动转成字符串，所以旧系统不报错。

**同批发现的 3 个数据保真缺陷**：

1. 前端发 `screen`，后端字段别名是 `screenResolution` → **屏幕信息永远丢失**；
2. 前端发 `timezone` / `platform` / `cookiesEnabled` → DTO 中不存在，**被静默丢弃**；
3. `ops/service.py` 中 `ip = "127.0.0.1"  # Mock getting IP` → **所有访客 IP 都写成 127.0.0.1**。

**修复内容**：

| 文件 | 修改 |
|---|---|
| `app/modules/ops/schemas.py` | `VisitorRecordDTO` 数值类字段放宽为 `str \| int \| float \| None`；`screen_resolution` 使用 `AliasChoices('screenResolution','screen')`；新增 `timezone` / `platform` / `cookies_enabled` |
| `app/modules/ops/service.py` | 新增 `_real_client_ip()`，依次取 `X-Real-IP` → `X-Forwarded-For` 首段 → socket 对端 |

**验证（阿里云 + 腾讯云）**：

| 项目 | 结果 |
|---|---|
| 三端 `visitor/record` 数字载荷 | **全部 200** |
| 前端真实字段载荷（screen/timezone/platform/cookiesEnabled/deviceMemory/hardwareConcurrency） | **全部 200** |
| 修复后日志残留 4xx | **NONE** |
| 公网本机上报后查库 | 记录真实公网 IP `120.194.123.242`（不再是 127.0.0.1），`views` 表同步正确 |
| 部署安全 | 导入自检 `IMPORT_OK` 通过才重启，失败自动回滚 `app.bak` |

---

## 六·补二、切换后修复：管理后台 401 / 400（已解决）

### A. 401 —— 不是 Bug

日志时间线（阿里云 `120.194.123.242` 真实浏览器）：

```
20:54:01  6 个 /api/admin/report/*      -> 401   （尚未登录）
20:54:13  /api/admin/article/page?...   -> 400   （已有 token，说明此时已登录）
```

**带合法 token 复测：6 个报表接口 + `/api/admin/systemConfig/key/start-time` 全部 200。**
不带 token 才 401（`{"code":0,"msg":"未登录,请先登录"}`）—— 这是**正确的鉴权行为**。

**根因**：浏览器 localStorage 里是**旧 Java 系统签发的 token**。新系统 JWT 密钥不同、
且 token 白名单存于 Redis，旧 token 必然失效 → 跳转登录即可。

**已核对：JWT 有效期与旧系统完全一致**
| | 旧 Java `application.yml` | 新 FastAPI `.env` |
|---|---|---|
| TTL | `ttl: 7200000`（2 小时） | `JWT__TTL_MS=7200000` |
| 头名 | `Authorization` | `JWT__TOKEN_NAME=Authorization` |

⇒ 会话时长无差异，登录后不会比旧系统更早掉线。

### B. 400 —— 真实 Bug（已修复）

**现象**：`/api/admin/article/page?page=1&pageSize=15&title=&categoryId=&isPublished=` → 400

**根因**：旧 Spring 把**空字符串**绑定为 null；Pydantic v2 把 `""` 当非法整数 → 400。

**修复**：新增 `app/core/query.py`
- `LenientQueryModel`：空串「有默认值→默认值，无默认值→null」
- `OptionalIntQuery` / `PageNumberQuery` / `PageSizeQuery` / `BeginDateQuery` / `EndDateQuery`
- 7 个分页 DTO 改为继承 `LenientQueryModel`；`MusicPageQueryDTO` 多重继承 `CamelModel + LenientQueryModel`
- 报表 `begin`/`end` 空值回落「最近 7 天」；`article/search` 分页空值回落默认

**同时修复一个隐藏功能缺失**：`ArticlePageQueryDTO` **根本没有 `isPublished` 字段**，
导致后台「按发布状态筛选」被静默忽略。已补上并接入 repository。

**回归结果（阿里云生产实测）**

| 用例 | 结果 |
|---|---|
| 用户报错的原始 URL | **200**，total=19 |
| `isPublished=true` / `false` / 不传 | **16 / 3 / 19**（筛选真正生效） |
| openapi 全部 11 个管理端 GET 路由 + **全空参数** | **11/11 = 200，0 失败** |
| 博客端 `?visitorId=` 空值 | **200** |
| 6 个报表接口（带 token） | **全部 200** |
| 4 个正式域名 | **全部 200** |

---

## 六·补三、切换后修复：音乐管理无数据 / 归档 undefined-null / 首页背景（已解决）

### 1. 管理端音乐管理页无数据 —— Pydantic union 把记录吃成 `{}`

**现象**：`/api/admin/music/page` 返回 `total=3` 但 `records: [{},{},{}]`（前端"有总数无数据"）。

**根因**：`app/modules/site_content/admin_schemas.py`

```python
records: list[dict] | list[CamelModel]   # ← union 走 dict 分支，每条被压成 {}
```

**修复**：改为 `records: list[Any]`（与 article / comments / ops 三处 PageResult 一致）。

**验证**：现在返回 3 条完整记录 × 13 字段。

| title | artist | duration | musicUrl |
|---|---|---|---|
| 玫瑰少年 | 五月天 | 235s | OSS audio ✅ |
| 水星记 | 郭顶 | 325s | OSS audio ✅ |
| 关键词 | 林俊杰 | 212s | OSS audio ✅ |

### 2. 博客归档页显示 `undefined-null`

**前端契约**（`blog.imcjk.top/js/index-DCPna--Z.js`）：

```js
month: a.month,
displayDate: `${String(a.month).padStart(2,"0")}-${String(s.publishDay).padStart(2,"0")}`
```

**根因**（两个叠加）：
1. 后端归档只返回 `{year, articles}`，**没有 `month`** → 渲染成 `undefined`；
2. `publish_day` 是库中 19/19 全 NULL 的死字段 → 渲染成 `null`。
⇒ 合起来就是 `undefined-null`。

**修复**：`get_archive()` 改为**按 (年,月) 分组**，并由 `publish_time` **只读推导**
`publish_year / publish_month / publish_day`（严格遵守"不写死字段"的既定约束）。

**验证**：5 个分组全部 `month` 有值、`publishDay` 零缺失，前端渲染出正确日期：

```
09-21  9.21跟进计划…
09-11  9.10日跟进计划…
08-24  8.24迟来的打卡…
07-31  7.31续上…
03-22  COPY版博客部署完成！
```

### 3. 博客首页 Hero 背景图已替换

| | 内容 |
|---|---|
| 位置 | `/www/wwwroot/blog.imcjk.top/assets/bgc-IXDcA65l.webp` |
| 引用 | `HeroBanner` 默认值 `n.coverImage \|\| "/assets/bgc-IXDcA65l.webp"` |
| 原图 | 3562×1704，523 KB（已备份为 `.bak_orig`） |
| 新图 | **1920×1096 WebP，549 KB**（用户提供，树/蓝天） |
| 公网验证 | `http=200 type=image/webp size=549118` |

> 文件名未变，浏览器可能命中旧缓存 —— 请 **Ctrl + F5** 强制刷新查看。

### 4. WebSocket `Page entered Back-Forward Cache` —— 良性提示，非故障

这是 **Chrome 自己打印**的信息，不是服务端错误：当页面带着未关闭的 WebSocket
进入**往返缓存（BFCache）**时，Chrome 会主动断开该连接并记录此句。

已实测确认 WebSocket 完全正常：
- 直连 `ws://127.0.0.1:8082/api/ws/online` → 首帧 `1`，`ping` → `pong`
- 公网 `wss://blog.imcjk.top/api/ws/online` → 首帧 `1`

前端已正确实现 `onUnmounted` 关闭 + 5 秒重连，返回页面后在线人数会自动恢复。

---

## 七、后续建议

1. **移除冗余测试入口**：删除 `imcjk_staging_coexist.conf`（9090-9093），减少暴露面。
2. **观察 24–48 小时**：关注 `free -h`、`uptime` 与 `journalctl -u imcjk-fastapi`。
3. **宝塔可选优化**（非必须）：稳定 1–2 个月且无回滚需求后，可停用宝塔面板回收 124MB。
4. **FastAPI 保持 `--workers 1`**：2C2G 下不要加 worker。
5. **备份保留**：本地桌面全量备份与服务器 `.bak_pre_fastapi` 至少保留 1 个月。
