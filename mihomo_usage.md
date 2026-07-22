# mihomo 代理使用指南

> 环境：Ubuntu 24.04 · `mihomo` 已安装在 `/usr/bin/mihomo` · 配置目录 `~/.config/mihomo/`
> 订阅链接：`https://services.cu-te.cn/link?token=26b374511d3c6f8f254f020f860fdad7`

---

## 关键结论（先看这个）

这个订阅链接有两个坑，直接 `wget`/`curl` 会失败：

1. **必须带客户端 User-Agent**。服务器按 UA 鉴权，默认的 curl/wget UA 会返回 **403 Forbidden**。必须用 `-A "mihomo/1.18.0"`（或其它 `clash...` 客户端 UA）。
2. **必须加 `&flag=clash` 参数**。不加时返回的是 base64 编码的节点列表（裸链接），mihomo **无法直接使用**；加上后才返回标准的 Clash/mihomo YAML 配置。

> 之前遇到的 `Unable to establish SSL connection` 只是临时网络抖动，链接本身是通的。

---

## 完整运行过程

### 第 1 步：下载订阅配置

```bash
# 确保目录存在
mkdir -p ~/.config/mihomo

# （可选）备份旧配置
cp ~/.config/mihomo/config.yaml ~/.config/mihomo/config.yaml.bak 2>/dev/null

# 下载配置：-A 客户端UA + &flag=clash 缺一不可
curl -sL -A "mihomo/1.18.0" \
  'https://services.cu-te.cn/link?token=26b374511d3c6f8f254f020f860fdad7&flag=clash' \
  -o ~/.config/mihomo/config.yaml


curl -sL -A "mihomo/1.18.0" \
  'https://0b96e976-9ec3-44c0-aa2b-30bf8b0792ea.com/api/v1/client/subscribe?token=271de1b7ac29bdde3e48645b64477f41&flag=clash' \
  -o ~/.config/mihomo/config_cat.yaml


好用：
curl -sL -A "mihomo/1.18.0" \
  'https://api.wd-blue.com/sub?target=clash&emoji=true&udp=true&scv=true&new_name=true&filename=WestData.yaml&url=https%3A%2F%2Fwd-blue.com%2Fsubscribe%2Fbvkyqr-tep5ipou-FqQnZx3bsffg' \
  -o ~/.config/mihomo/config_2.yaml

```

> 注意 URL 一定要用**单引号**包住 —— 里面有 `?`、`&`、`=`，不加引号会被 shell 错误解析。

### 第 2 步：校验配置

```bash
mihomo -d ~/.config/mihomo -t
```

看到 `test is successful` 即为成功。也可以确认节点数：

```bash
grep -c 'name:' ~/.config/mihomo/config.yaml
grep -c 'name:' ~/.config/mihomo/config_cat.yaml
```

### 第 3 步：启动 mihomo

**前台运行**（关掉终端就停，适合临时用、方便看日志）：

```bash
*mihomo -d ~/.config/mihomo*
```

**后台运行**（终端关了也不停，适合日常挂着）：

```bash
nohup mihomo -d ~/.config/mihomo > /tmp/mihomo.log 2>&1 &
```

启动成功后会监听：

- **混合代理端口（http + socks5）**：`127.0.0.1:7890`
- **控制面板 API**：`127.0.0.1:9090`

### 第 4 步：验证代理是否翻墙成功

```bash
# 直连出口 IP（国内）
curl -s https://api.ip.sb/ip

# 走代理出口 IP（应该变成国外 IP）
curl -s -x http://127.0.0.1:7890 https://api.ip.sb/ip

# 走代理访问 Google（应返回 HTTP 200）
curl -s -x http://127.0.0.1:7890 -o /dev/null -w "HTTP %{http_code}\n" https://www.google.com
```

两次 IP 不同、且 Google 返回 200，即代理正常工作。

---

## 让其它程序走代理

在**当前终端**临时生效：

```bash
export https_proxy=http://127.0.0.1:7890
export http_proxy=http://127.0.0.1:7890
export all_proxy=socks5://127.0.0.1:7890
```

取消代理：

```bash
unset https_proxy http_proxy all_proxy
```

想每次开终端自动生效，把上面 3 行 `export` 加到 `~/.bashrc` 末尾即可。

---

## 停止 mihomo

```bash
pkill -f 'mihomo -d'
```

确认已停止（端口应无输出）：

```bash
ss -tlnp | grep -E '7890|9090'
```

---

## 更新订阅（换节点、续费后刷新）

重复**第 1 步**重新下载 `config.yaml`，然后重启 mihomo：

```bash
pkill -f 'mihomo -d'
curl -sL -A "mihomo/1.18.0" \
  'https://services.cu-te.cn/link?token=26b374511d3c6f8f254f020f860fdad7&flag=clash' \
  -o ~/.config/mihomo/config.yaml
mihomo -d ~/.config/mihomo -t && nohup mihomo -d ~/.config/mihomo > /tmp/mihomo.log 2>&1 &
```

---

## 常见问题

| 现象 | 原因 / 解决 |
|------|-------------|
| `403 Forbidden` | 没带 `-A "mihomo/1.18.0"` UA |
| 配置校验失败 / mihomo 解析不了 | 下载时漏了 `&flag=clash`，拿到的是 base64 裸链接 |
| `Unable to establish SSL connection` | 临时网络抖动，重试即可 |
| 端口 7890 被占用 | 已有 mihomo 在跑，先 `pkill -f 'mihomo -d'` |
| 代理出口 IP 和直连一样 | mihomo 没起来，或程序没设置代理环境变量 |

---

## 附：可选进阶

- **开机自启（systemd 常驻服务）**：把 mihomo 做成 systemd service，开机自动启动、崩溃自动重启。
- **Web 管理面板**：搭配 `metacubexd` / `yacd` 面板（连 `127.0.0.1:9090`）可视化切换节点、看延迟和流量。

需要这两项时再单独配置。
