# low-code-platform 开发容器

## 一次性 build（宿主机，有 devel 时）

```bash
cd devel
docker compose build nodejs-dev
```

首次在数据盘放**两个清单**（改插件只改这里，不用 rebuild 镜像）：

```bash
mkdir -p /media/hdd/data/svap-designer
cp devel/container/dev-plugin-packages.txt devel/container/dev-userDir-package.json /media/hdd/data/svap-designer/
```

`install-svap-designer` / `start-svap-designer` 在**镜像里**，不用拷到数据盘。

## 启动容器

```bash
docker compose up -d nodejs-dev
```

## 容器内

```bash
docker exec -it svap-nodejs-devel bash
install-svap-designer    # 首次
start-svap-designer      # 开/重启 21880
```

- 清单：宿主机 `/media/hdd/data/svap-designer/` 下上述两个文件  
- Node-RED 数据：`/data/node-red/`（宿主机 `/media/hdd/data/node-red/`）  
- 改清单：`FULL_REBUILD=1 install-svap-designer`

## 新增插件包

改数据盘两个清单 → `FULL_REBUILD=1 install-svap-designer` → `start-svap-designer`。

## 改代码

不用 build → 重启 `start-svap-designer`；要先 build → build 后重启。


