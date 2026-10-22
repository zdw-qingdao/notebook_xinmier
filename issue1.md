# EdgeFlow 页面卡顿问题汇总

更新时间：2026-10-14  
服务地址：`http://120.48.26.246:10700`

## 结论概览

已确认存在两个相互独立、但最终表现相似的问题：

1. 删除项目或工作空间时，在数据库事务持锁期间全表扫描 Blob，并逐条解析 CFS 路径，造成长事务、锁链和连接池耗尽。
2. 创建数据集弹窗为每个图集分别请求预览图，一次产生数百个请求，造成数据库 Session 长时间占用和连接池耗尽。

两类问题最终都会触发：

```text
sqlalchemy.exc.TimeoutError:
QueuePool limit of size 5 overflow 10 reached,
connection timed out, timeout 30.00
```

此时静态首页仍可快速打开，但登录、工作空间、任务、图片和健康检查等后端 API 会等待约 30 秒后返回 500，`edgeflow-runtime-1` 变为 `unhealthy`。

服务器整机资源并不是瓶颈。两次现场中 CPU、内存和磁盘 I/O 都有大量余量，静态首页首字节约 8 ms。

---

## 问题一：删除项目时扫描数百万 Blob 和 CFS 路径

### 现象

- 删除项目或工作空间后，请求持续几十分钟没有完成。
- PostgreSQL 出现一个长期 `idle in transaction` 的事务。
- 该事务持有项目行锁，后续请求在 `SELECT ... FOR UPDATE` 上排队。
- 等待请求逐步占满 SQLAlchemy 的 15 个连接，最终全站 API 卡住。
- Docker 健康检查持续超时，并留下多个孤儿 `curl` 进程。

### 现场证据

- `blobs` 表约有 `2,352,674` 条记录。
- 根事务持有 `project_id=162` 的锁超过 30 分钟。
- 现场有 13 个数据库连接等待项目或工作空间行锁。
- 后端默认连接池为 `pool_size=5`、`max_overflow=10`，共 15 个连接。
- 主机有 208 核 CPU，现场 CPU 约 98%～99% 空闲，可用内存约 947 GiB。

### 根因代码

文件：

```text
/cfs/users/autopipe/code/main/backend/database/manager.py
```

项目删除先取得行锁：

```python
project = (
    self.session.query(Project)
    .filter(Project.id == project_id)
    .with_for_update()
    .first()
)
```

随后在同一个事务中调用 `_registered_video_cleanup_paths()`，其中存在 Blob 全表扫描：

```python
for (storage_key,) in self.session.query(Blob.storage_key).all():
    path = self._safe_storage_cleanup_path(str(storage_key or ""))
```

`_safe_storage_cleanup_path()` 会调用 `os.path.realpath()`。`/data` 位于 CFS 网络存储，因此这段代码实际上执行：

```text
数据库持有项目锁
→ 读取约 235 万条 storage_key
→ 对每条记录执行 CFS 路径解析
→ 数十分钟不能提交事务
→ 后续请求形成锁链
→ 连接池耗尽
```

数据库提交后的 `_delete_workspace_files()` 中还有第二处同类全表扫描：

```python
blob_paths = {
    path
    for (storage_key,) in self.session.query(Blob.storage_key).all()
    if (path := self._safe_storage_cleanup_path(str(storage_key or "")))
}
```

它虽然发生在第一次提交之后，但会重新开启数据库事务，并在长时间 CFS 文件处理期间继续占用数据库连接。

### 应急恢复

只重启后端 API，不要重启整个 runtime、Ray 或任务调度器：

```bash
docker exec edgeflow-runtime-1 supervisorctl restart autopipe
```

效果：

- 中断卡住的删除请求。
- 未提交事务自动回滚并释放锁。
- 清空后端连接池。
- Ray 和 `task-scheduler-3` 不重启。

注意：当前登录 token 保存在 API 进程内存中，重启后用户需要重新登录；正在执行的 API 写请求也会被中断。

### 永久修复

#### 1. 禁止 Blob 全表扫描

只查询待清理的候选路径：

```python
target_keys = [...]
retained_keys = {
    key
    for (key,) in (
        db.query(Blob.storage_key)
        .filter(Blob.storage_key.in_(target_keys))
        .all()
    )
}
```

利用 `blobs_storage_key_key` 索引，将 235 万条全表扫描改为几十或几百个精确查询。

#### 2. 数据库逻辑删除与 CFS 物理删除分离

推荐流程：

```text
DELETE 请求
→ 标记资源为 deleting
→ 在数据库中写入 storage_gc_job/storage_gc_item
→ 提交事务并返回 HTTP 202
→ 独立 GC Worker 分批删除 CFS 文件
→ 更新任务进度和资源状态
```

任何 `realpath()`、`unlink()`、`rmtree()` 或大规模目录遍历都不得放在 `FOR UPDATE` 与 `commit()` 之间。

#### 3. GC Worker 要求

- 每批领取 200～1000 个文件。
- 使用 `FOR UPDATE SKIP LOCKED` 支持多个 Worker。
- CFS 删除并发从 4～8 开始压测，不要无限并发。
- `FileNotFoundError` 视为删除成功，保证幂等。
- 单文件失败记录错误并指数退避重试。
- 使用租约和心跳，Worker 重启后可以继续任务。
- 对共享 Blob，只有确认引用数为 0 后才允许进入 GC。
- 独立项目目录可先在同一 CFS 挂载点内原子重命名到 `.trash/<job_id>`，再异步清理。

---

## 问题二：创建数据集弹窗产生预览请求洪峰

### 现象

- 打开“创建数据集”弹窗后页面迅速变卡。
- `/api/annotation-versions/{version_id}/images?page=1&per_page=3&clip_id=...` 被大量并发调用。
- PostgreSQL 没有锁等待，但 15 个应用连接全部处于 `idle in transaction`。
- 最长事务占用超过 9 分钟。
- 后续请求无法从连接池取得连接，30 秒后大量返回 500。
- 请求洪峰消退后服务可以自行恢复。

### 现场证据

版本 `47` 当时包含：

- 220 个状态为 `approved` 且没有活动任务的图集。
- 679,018 张版本图片。

简单的单图集计数 SQL 执行时间约 0.78 ms，说明 PostgreSQL 单条查询本身并不慢。问题在于请求数量、Session 生命周期和连接池容量的组合。

### 根因代码

前端文件：

```text
/cfs/users/autopipe/code/main/frontend/src/pages/project/dataset/DatasetCreateModal.tsx
```

`availableSources.map(...)` 会为所有可用图集渲染 `SourceThumbnails`。每个组件挂载后立即执行独立的 React Query：

```typescript
dataSource.listVersionImages(versionId ?? '', {
  page: 1,
  per_page: 3,
  clip_id: versionClipId,
})
```

因此一次打开弹窗会发起或排队约 220 个预览 API 请求。

后端接口：

```text
/cfs/users/autopipe/code/main/backend/routers/annotations.py
GET /api/annotation-versions/{version_id}/images
```

数据库连接配置：

```text
/cfs/users/autopipe/code/main/backend/database/connection.py
```

当前使用 SQLAlchemy 默认值：

```python
create_engine(get_db_url(), pool_pre_ping=True)
```

即：

```text
pool_size=5
max_overflow=10
pool_timeout=30s
```

认证与 Authorizer 使用 `yield` 类型的同步 `get_db` 依赖。大量请求在多个同步依赖阶段之间继续持有 Session，形成连接池饥饿。

### 应急恢复

优先关闭创建数据集弹窗并停止产生新的预览请求。请求洪峰停止后，服务通常能逐步恢复。

如需立即恢复，可只重启 API：

```bash
docker exec edgeflow-runtime-1 supervisorctl restart autopipe
```

### 永久修复

#### 1. 使用批量预览接口

最佳方案是在现有图集列表接口中直接返回每个图集最多 3 张预览图，或者新增：

```text
GET /api/annotation-versions/{version_id}/clips/previews?limit=3
```

数据库可通过窗口函数一次返回所有图集预览：

```sql
row_number() over (
    partition by version_clip_id
    order by image_id
) <= 3
```

目标是把约 220 个请求减少为 1 个请求。

#### 2. 前端增加懒加载和并发限制

- 只加载视口内可见图集的预览图。
- 同时最多执行 4～6 个预览请求。
- 弹窗关闭或版本切换时取消未完成请求。
- 不要让所有 `SourceThumbnails` 在挂载时无条件请求后端。
- 图集很多时使用虚拟列表。

#### 3. 缩短数据库 Session 生命周期

对认证、Authorizer 和只读接口使用函数作用域依赖：

```python
Depends(get_db, scope="function")
```

确保接口函数完成后立即关闭 Session，不要让数据库连接跨响应发送阶段长期存活。文件下载和流式响应尤其不能持有普通业务 Session。

#### 4. 连接池保护性配置

在解决请求洪峰和 Session 生命周期后，再设置明确的连接池参数：

```python
create_engine(
    get_db_url(),
    pool_size=20,
    max_overflow=20,
    pool_timeout=5,
    pool_pre_ping=True,
)
```

扩大连接池只能提高短时容错，不能作为根治方案；否则只会把请求洪峰进一步传递给 PostgreSQL。

---

## 通用加固建议

### 数据库保护

- 配置合理的 `idle_in_transaction_session_timeout`。
- 配置 `lock_timeout`，避免请求无限等待行锁。
- 监控 SQLAlchemy pool checked-out 数量和 checkout 等待时间。
- 监控 PostgreSQL `idle in transaction` 数量、最老事务和锁等待链。

### 健康检查

- `/api/health/live` 不访问数据库，并改为不会依赖同步线程池的轻量接口。
- `/api/health/ready` 的数据库探测必须快速失败。
- `runtime-healthcheck.sh` 中的 `curl` 增加：

```bash
--connect-timeout 1 --max-time 3
```

避免 Docker 杀死健康检查外层进程后留下孤儿 `curl`。

### Nginx

当前普通 API 的 `proxy_read_timeout` 为 3600 秒，容易让故障请求长时间占用连接。建议普通 API 调整到 30～60 秒，仅为确实需要长连接的流式接口单独配置较长超时。

### 日志和监控

Nginx access log 增加：

```text
$request_time $upstream_connect_time $upstream_header_time $upstream_response_time
```

同时记录接口名、状态码和请求 ID，便于快速区分：

- 前端请求洪峰
- 数据库连接池等待
- PostgreSQL 锁等待
- CFS 文件系统等待

---

## 修复验收标准

### 项目/工作空间删除

- DELETE API 在数秒内返回 `202 Accepted`。
- 删除期间不出现超过 30 秒的数据库事务。
- CFS 删除任务可查询进度、失败重试并在重启后恢复。
- 删除数十万或数百万文件时，普通 API 仍能正常响应。

### 创建数据集弹窗

- 打开包含 220 个图集的版本时，预览 API 请求总数不超过数个。
- 数据库连接池使用量不会持续达到上限。
- 不出现持续超过 30 秒的 `idle in transaction`。
- 弹窗打开期间 `/api/health/live` 和 `/api/health/ready` 保持快速响应。

---

## 部署路径说明

提供的 `/cfs/users/autopipe/code/autopipe` 在服务器上不存在。当前运行容器的 Compose 标签显示实际部署来自：

```text
/cfs/users/autopipe/code/main/production/compose.yaml
```

对应启动脚本为：

```text
/cfs/users/autopipe/code/main/docker/docker_run.sh
```
