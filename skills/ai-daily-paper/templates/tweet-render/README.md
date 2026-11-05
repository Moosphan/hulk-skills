# X 帖子渲染（react-tweet）

开源项目：`vercel/react-tweet`（X 官方风格组件，带媒体、时间、互动数）。

## 用法
```bash
npm i && npx vite build
python3 -m http.server 4399 -d dist
# 另一终端
node render.mjs <tweet-id> out.png
```

## 说明
- 组件通过 react-tweet 的公开接口取数，无需登录
- 渲染时浏览器需走代理访问该接口；本地 127.0.0.1 要 bypass
- 截图元素用 `article`，2–3x，最后裁到卡片
- 比自绘卡片更接近 X 原样，且能显示图/视频封面
