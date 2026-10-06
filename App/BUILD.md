# Kang Blog Admin 打包说明（Android APK · EAS Build）

Expo（React Native）编写的 **IMCJK 个人博客移动端管理后台**，与 `Frontend-Admin` 共用 FastAPI 后端接口，支持文章审核、评论留言管理、城市足迹与图集管理、数据看板。

打 APK 走 **EAS 云端构建**，本机不需要安装 Android Studio / SDK / JDK。

> 🌐 **默认服务器**：`https://admin.imcjk.top`（阿里云生产）
> 登录页内置「服务器切换」入口，可随时切到腾讯云测试环境或自定义地址，**无需重新打包**。

---

## 一、前置条件

- Node.js（建议 LTS 版本）
- pnpm：`npm i -g pnpm`
- Expo 账号（https://expo.dev 免费注册）
- 一个 EAS 项目（首次打包时创建，见"首次配置"）

## 二、首次配置（只需做一次）

### 1. 安装依赖

```bash
cd App
pnpm install
```

### 2. 关联你的 EAS 项目

仓库本身不包含任何人的 EAS 账号信息（projectId / owner 都不入库），需要你在本地创建一个 `App/.local.eas.json`：

```bash
cp .local.eas.example.json .local.eas.json
```

编辑 `.local.eas.json`，填入你自己的 EAS 项目信息：

```json
{
  "projectId": "你的项目 ID",
  "owner": "你的 Expo 用户名"
}
```

- 该文件已被 .gitignore 忽略，不会提交进仓库。
- 还不知道 projectId？先执行第 4 步的 `npx eas-cli init`，它会创建/关联项目并打印 projectId，再回来填。

### 3. 登录 Expo 并初始化 EAS 项目（仅首次）

```bash
npx eas-cli login
npx eas-cli init
```

- `eas init` 会在 EAS 服务端创建/关联项目，并把 projectId 打印在终端里，填进第 2 步的 `.local.eas.json`。
- 本仓库使用动态配置（`app.config.js`），`eas init` 不会自动写入 projectId，需要手动填写。
- 之后同一仓库再打包可跳过本步。

### 4. 配置服务器地址（可选）

> ℹ️ **打包时可以跳过这一步**：App 内置默认服务器 `https://admin.imcjk.top`，且登录页提供「服务器切换」入口，装好后可随时切换环境。

如需在构建期固化某个地址（EAS 云端构建**不读取本地 `.env`**，环境变量必须通过 `eas env:set` 存在 EAS 服务端）：

```bash
npx eas-cli env:set --name EXPO_PUBLIC_API_URL --value https://admin.imcjk.top --visibility plaintext
```

- `--name` / `--value` 是新版 eas-cli 的 flag 写法（不要写成 `eas env:set 名字 值`，会被当成位置参数而报错）。
- 环境范围按默认（`production`、`preview`、`development` 全部）即可。

> 本地用 Expo Go / `expo start` 调试时才需要项目根目录的 `.env`（不影响云端打包）：
>
> ```bash
> cp .env.example .env
> # 编辑 .env 的 EXPO_PUBLIC_API_URL
> ```

### 5. 应用图标

仓库已配置为站长专属的 **1024×1024 高清头像图标**（`assets/images/icon.png`），通常无需替换。

如需更换，准备一张 **1024×1024 的 PNG** 覆盖该文件即可：

- logo 放在画面中央约 2/3 范围内（系统自适应遮罩会裁掉边缘，贴边会被切掉）。
- 建议纯色/圆角背景、无透明边框。
- Expo 会自动基于 `icon.png` 生成 Android 自适应图标（背景色 `#f5f7fa`）。

## 三、打包 APK

```bash
npx eas-cli build -p android --profile preview
```

- `eas.json` 中 `preview` 已配置为 `distribution: internal` + `buildType: apk`，产出**可直接安装的 APK**（而非上架 Google Play 的 AAB）。
- 签名由 EAS 自动管理；同一项目后续更新复用同一 keystore，可覆盖安装旧包。
- 构建完成后终端会给出下载链接，手机浏览器打开下载安装即可。
- 或用数据线连接手机：`adb install app-release.apk`。

## 四、更新发布

1. 修改代码后重新构建：`npx eas-cli build -p android --profile preview`。
2. 若新包覆盖安装旧包失败，递增 `App/app.json` 里 `expo.version`（或补 `android.versionCode`），保持版本号上升。
3. 改了服务器地址：**无需重新打包**，在 App 登录页点击「🌐 当前服务器 → 切换」即可。

## 五、常见问题

| 现象 | 处理 |
|---|---|
| App 打开就闪退、登录页都看不到 | 确认 Node/Expo 版本与 `app.json` 配置正确；本地 `.env` 未配置时 App 会回退到默认生产地址，不会闪退 |
| APK 装到手机后连不上服务器 | 在登录页切换到手机当前网络可达的地址（腾讯云测试环境 `http://106.52.19.177:8081` 需在手机同网段或公网可达）；release 包默认拦截明文 `http://`，建议使用 `https://` |
| `eas build` 提示需要配置项目 | 检查 `.local.eas.json` 是否已创建并填好 projectId（见第 2 步） |
| 构建提示 expo-notifications 需要 FCM / google-services.json | 本 App 只使用**本地通知**，不依赖 FCM。检查 `app.json` 是否误加了 `googleServicesFile`，移除即可；仅做远程推送才需要 Firebase |
| 改了 `app.json` / 图标 / `eas.json` 没生效 | EAS 每次构建都会重新生成原生工程，重新构建即可 |
| 扫码后 Expo Go 提示"出问题了 try to reload" | 手机与电脑不在同一可互访网段（校园网/公司网 AP 隔离）。改用 `npx expo start --tunnel` 隧道模式，或让电脑连接手机热点 |
