# RUC News 校园信息智能中报系统 · 前端

移动端 H5（适配 iOS / Android 微信浏览器与手机浏览器）。

## 技术栈

Vue 3 (Composition API) · Vite · Vant 4 · Vue Router 4 (Hash) · Pinia · Axios · Day.js · Lodash-es

## 快速开始

```bash
# 安装依赖
npm install

# 启动开发服务器（默认 http://localhost:5173）
npm run dev

# 生产构建（输出 dist/）
npm run build
```

## 目录结构

```
ruc-news/
├── src/
│   ├── api/            # Axios 封装 + 接口统一管理（@/api）
│   │   ├── request.js  # 拦截器：Token 注入 / 401 跳转 / 统一 Toast
│   │   ├── post.js     # 帖子/资讯/评论
│   │   ├── search.js   # 全文搜索
│   │   ├── user.js     # 登录/登出/用户信息
│   │   ├── notification.js
│   │   └── feedback.js # 埋点上报
│   ├── stores/         # Pinia：user / loading / notification
│   ├── router/         # 路由 + 全局权限守卫
│   ├── layout/         # 底部 Tab 导航
│   ├── views/          # 页面（Home/Search/Publish/Notifications/My/Detail）
│   ├── utils/          # storage / cache(TTL) / format
│   ├── constants/      # 缓存键、分类、上限等常量
│   └── styles/         # 设计系统变量 + 全局样式
├── .env.development    # 开发环境（API 代理）
├── .env.production     # 生产环境（API 域名）
└── vite.config.js      # 代理 / 按需引入 / 代码分割
```

## 环境配置

| 变量 | 说明 |
| --- | --- |
| `VITE_APP_API_BASE_URL` | 请求基础路径。开发为 `/api`（走 Vite 代理），生产为后端完整域名 |
| `VITE_APP_API_TARGET` | 开发环境代理转发目标（后端真实地址） |

**后端路由前缀**：若后端接口带 `/api` 前缀（如 `/api/latest`），代理无需改写；若接口直接为 `/latest`，取消 `vite.config.js` 中 `rewrite` 行的注释。

## 约定

- **接口响应**：后端统一返回 `{ code, message, data }`，`code === 200`（或 `0`）为成功；`401` 触发重新登录。
- **请求配置**：支持 `silent`（静默请求不弹 Toast，用于轮询/埋点）、`skipAuth`（跳过 Token 注入，用于登录）。
- **缓存**：`utils/cache.js` 提供 `setCache(key, data, ttl)` / `getCache(key)`，TTL 默认 5 分钟。
- **权限**：`publish` / `notifications` / `post-detail` 需登录（路由守卫拦截）；首页/搜索/我的可匿名访问。如需全局强制登录，把路由 `meta.requiresAuth` 全部置 `true` 即可。

## 待实现（任务拆解）

- [ ] 任务 4：首页列表 + 缓存
- [ ] 任务 5：分区详情页
- [ ] 任务 6：搜索页（防抖 / 历史 / 高亮）
- [ ] 任务 7：发帖页（表单 / 草稿 / 悬赏开关）
- [ ] 任务 8：帖子详情页（正文 + 评论）
- [ ] 任务 9：消息页
- [ ] 任务 10：我的页面（登录 / 用户信息 / 反馈上报）
- [ ] 任务 11：全局埋点 + 性能优化
