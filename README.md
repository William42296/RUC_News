# RUC News 校园信息智能中报系统

面向人大（RUC）校园的信息聚合与智能推荐 H5 应用。数据来源于校园集市小程序（`ys.qimiaoyuanfen.com`），后端定时抓取、分类并推荐，前端以移动端 H5 呈现。

## 目录结构

- `frontend/` — 前端（Vue 3 + Vite + Vant 4）
- `backend/` — 后端（Flask + SQLAlchemy + SQLite + Redis）

## 技术栈

### 前端 frontend/

- Vue 3（Composition API）+ Vite 5 + Vant 4（按需引入）
- Vue Router 4（Hash 模式）+ Pinia + Axios
- 主题：米黄底 + 血红色字（柔化简洁）

### 后端 backend/

- Flask + SQLAlchemy + SQLite（数据持久化）
- Redis（列表 / 搜索 / 详情缓存，RESP2 协议，需 `redis==4.6.0`）
- JWT（HS256）鉴权
- jieba + pandas + numpy：帖子分类与协同过滤推荐
- 爬虫：定时抓取校园集市（默认 60s），附带 `mitm_proxy` 抓包脚本

## 快速开始

### 后端

```bash
cd backend
pip install -r requirements.txt
# 确保本机 Redis 运行于 127.0.0.1:6379（Windows 建议 tporadowski/redis 5.0.14.1）
# 如需真实抓取数据，放置 session.json：{"ys_ysxy_sess": "..."}
python app.py
```

### 前端

```bash
cd frontend
npm install
npm run dev   # 开发服务器 http://127.0.0.1:5173
```

## 主要页面

- 首页分类：最新 / 推荐 / 悬赏 / 大事件（时间轴）/ 分区
- 搜索、帖子详情、评论、消息中心、我的、反馈

## 说明

- `backend/session.json` 与 `backend/ruc_news.db` 已加入 `.gitignore`，不会入库。
- 生产部署前请通过环境变量 `SECRET_KEY` 覆盖默认开发密钥。
