# NVIDIA DeepStream 完整使用流程

> 更新日期：2026-07-13  
> 基准版本：NVIDIA DeepStream SDK 9.0  
> 范围：环境选择、安装、验证、运行示例、理解管线、接入自定义 ONNX 模型、输出结果、排错与性能检查。

## 1. DeepStream 是什么

DeepStream 是基于 GStreamer 的 NVIDIA 视频分析 SDK。典型流程为：

```text
视频/摄像头/RTSP
  -> 硬件解码
  -> nvstreammux 多路合批
  -> nvinfer TensorRT 推理
  -> nvtracker 目标跟踪（可选）
  -> nvinfer 二级分类（可选）
  -> nvdsanalytics 业务分析（可选）
  -> OSD 叠加
  -> 显示、文件、RTSP 或消息队列
```

常用组件：

- `deepstream-app`：官方参考应用，主要通过配置文件搭建管线。
- `gst-launch-1.0`：快速验证 GStreamer 插件和简单管线。
- `Gst-nvinfer`：使用 TensorRT 做本地推理。
- `Gst-nvinferserver`：通过 Triton Inference Server 推理。
- `nvstreammux`：将多路视频帧组成 batch。
- `nvtracker`：目标跟踪。
- `nvdsosd`：绘制检测框、标签等信息。
- `nvmsgconv`、`nvmsgbroker`：生成并发送结构化消息。

## 2. 先确认平台和版本

DeepStream 不能直接在 macOS 上运行。macOS 可以用于编辑代码、SSH 登录设备，但执行环境必须是支持的 NVIDIA 平台。

DeepStream 9.0 的主要环境如下：

| 平台 | 系统 | GPU/设备 | CUDA | TensorRT | 驱动/JetPack |
| --- | --- | --- | --- | --- | --- |
| x86_64 dGPU | Ubuntu 24.04 | Turing、Ampere、Ada、Hopper、Blackwell 等 | 13.1 | 10.14.1.48 | NVIDIA Driver 590.48.01 |
| Jetson | L4T Ubuntu 24.04 | Jetson AGX Thor | 13.0 | 10.13.2.6 | JetPack 7.1 GA / L4T 38.4 |

注意：

1. DeepStream 9.0 的 Jetson 支持对象是 **AGX Thor**。Jetson Orin 应使用与 JetPack 匹配的旧版 DeepStream，例如 DeepStream 7.1 + JetPack 6.1，不能机械照搬本文的 9.0 安装包。
2. 旧 TensorRT 生成的 `.engine` 文件通常不能跨 GPU、TensorRT 版本或精度环境直接使用，应在目标机器重新生成。
3. 从 TensorRT 8.x 迁移到 TensorRT 10.x 时，旧模型和 INT8 校准数据需要重新验证。
4. RHEL 在 DeepStream 9.0 中不受支持。

确认本机信息：

```bash
uname -m
lsb_release -a
nvidia-smi
nvcc --version
dpkg -l | grep -E 'nvinfer|tensorrt|deepstream'
```

Jetson 额外确认：

```bash
cat /etc/nv_tegra_release
apt-cache show nvidia-jetpack | grep Version
```

## 3. 选择安装方式

### 3.1 推荐策略

- 首次学习、需要编译自定义插件：使用原生安装。
- x86 服务器、需要固定环境和快速复现：优先使用官方 Docker。
- Jetson：先使用 SDK Manager 安装匹配的 JetPack，再安装 DeepStream。
- Jetson 9.0 容器主要用于部署，不适合在容器内完成 DeepStream 软件开发；应用可在设备原生环境编译后加入部署镜像。

### 3.2 不要混装版本

安装前先核对 DeepStream、CUDA、TensorRT、驱动和 JetPack 的兼容矩阵。系统中若已有其他版本，优先使用独立 Docker 环境；若必须原生升级，先按旧版本自带的 `uninstall.sh` 卸载。

## 4. Ubuntu x86_64 + NVIDIA dGPU 原生安装

### 4.1 安装基础依赖

```bash
sudo apt update
sudo apt install -y \
  libssl3 \
  libssl-dev \
  libcurl4-openssl-dev \
  libgles2-mesa-dev \
  libgstreamer1.0-0 \
  gstreamer1.0-tools \
  gstreamer1.0-plugins-good \
  gstreamer1.0-plugins-bad \
  gstreamer1.0-plugins-ugly \
  gstreamer1.0-libav \
  libgstreamer-plugins-base1.0-dev \
  libgstrtspserver-1.0-0 \
  libjansson4 \
  libyaml-cpp-dev \
  libjsoncpp-dev \
  protobuf-compiler \
  libmosquitto1 \
  gcc \
  make \
  git \
  python3
```

### 4.2 安装 GPU 软件栈

DeepStream 9.0 x86_64 官方验证组合：

```text
Ubuntu 24.04
NVIDIA Driver 590.48.01
CUDA Toolkit 13.1
TensorRT 10.14.1.48
GStreamer 1.24.2
```

应优先按照 NVIDIA 官方 CUDA、驱动和 TensorRT 文档安装，不要仅依靠 Ubuntu 默认仓库猜测版本。安装后验证：

```bash
nvidia-smi
nvcc --version
dpkg -l | grep nvinfer
gst-launch-1.0 --version
```

### 4.3 安装 DeepStream

从 NVIDIA NGC 下载：

```text
deepstream-9.0_9.0.0-1_amd64.deb
```

安装：

```bash
cd ~/Downloads
sudo apt-get install ./deepstream-9.0_9.0.0-1_amd64.deb
sudo ldconfig
```

也可以下载 tar 包：

```bash
sudo tar -xvf deepstream_sdk_v9.0.0_x86_64.tbz2 -C /
cd /opt/nvidia/deepstream/deepstream-9.0
sudo ./install.sh
sudo ldconfig
```

## 5. Jetson 原生安装

### 5.1 安装 JetPack

在 Ubuntu 主机上安装 NVIDIA SDK Manager，通过恢复模式刷入与设备、DeepStream 版本匹配的 JetPack。

DeepStream 9.0 对应：

```text
Jetson AGX Thor
JetPack 7.1 GA
L4T 38.4
```

SDK Manager 的 `Additional SDKs` 中可以直接选择 `DeepStreamSDK`。如果已经装好 JetPack，也可以继续使用 Debian 包或 tar 包。

### 5.2 安装依赖

```bash
sudo apt update
sudo apt install -y \
  libssl3 \
  libssl-dev \
  libcurl4-openssl-dev \
  libgstreamer1.0-0 \
  gstreamer1.0-tools \
  gstreamer1.0-plugins-good \
  gstreamer1.0-plugins-bad \
  gstreamer1.0-plugins-ugly \
  gstreamer1.0-libav \
  libgstreamer-plugins-base1.0-dev \
  libgstrtspserver-1.0-0 \
  libjansson4 \
  libyaml-cpp-dev \
  libmosquitto1
```

### 5.3 安装 DeepStream

Debian 包方式：

```bash
cd ~/Downloads
sudo apt-get install ./deepstream-9.0_9.0.0-1_arm64.deb
sudo ldconfig
```

tar 包方式：

```bash
sudo tar -xvf deepstream_sdk_v9.0.0_jetson.tbz2 -C /
cd /opt/nvidia/deepstream/deepstream-9.0
sudo ./install.sh
sudo ldconfig
```

## 6. Docker 安装

### 6.1 主机准备

主机必须安装：

- 支持当前 DeepStream 的 NVIDIA 驱动；
- Docker Engine；
- NVIDIA Container Toolkit。

确认容器可以访问 GPU：

```bash
docker run --rm --gpus all ubuntu:24.04 nvidia-smi
```

### 6.2 拉取镜像

需要 Triton 时可使用：

```bash
docker pull nvcr.io/nvidia/deepstream:9.0-triton-multiarch
```

NGC 可能还提供 `samples`、`development` 等用途不同的镜像标签。实际使用前应在 NGC DeepStream 容器页面核对当前标签。

### 6.3 启动容器

有桌面显示：

```bash
xhost +local:docker

docker run --rm -it \
  --gpus all \
  --network host \
  -e DISPLAY="$DISPLAY" \
  -e NVIDIA_DRIVER_CAPABILITIES=compute,utility,video,graphics \
  -v /tmp/.X11-unix:/tmp/.X11-unix \
  -v "$PWD":/workspace \
  nvcr.io/nvidia/deepstream:9.0-triton-multiarch
```

无桌面服务器：

```bash
docker run --rm -it \
  --gpus all \
  --network host \
  -e NVIDIA_DRIVER_CAPABILITIES=compute,utility,video \
  -v "$PWD":/workspace \
  nvcr.io/nvidia/deepstream:9.0-triton-multiarch
```

无桌面环境不能使用显示 sink，应改用 `fakesink`、文件输出或 RTSP 输出。

## 7. 安装后验证

### 7.1 检查命令和插件

```bash
which deepstream-app
deepstream-app --version-all
gst-inspect-1.0 nvstreammux
gst-inspect-1.0 nvinfer
gst-inspect-1.0 nvtracker
```

若 `gst-inspect-1.0 nvinfer` 找不到插件：

```bash
sudo ldconfig
export GST_PLUGIN_PATH=/opt/nvidia/deepstream/deepstream/lib/gst-plugins:$GST_PLUGIN_PATH
export LD_LIBRARY_PATH=/opt/nvidia/deepstream/deepstream/lib:$LD_LIBRARY_PATH
rm -f ~/.cache/gstreamer-1.0/registry.*.bin
gst-inspect-1.0 nvinfer
```

### 7.2 运行官方参考应用

```bash
cd /opt/nvidia/deepstream/deepstream-9.0/samples/configs/deepstream-app
deepstream-app -c source30_1080p_dec_infer-resnet_tiled_display.txt
```

该示例会读取官方样例视频、执行解码和主检测，并以平铺方式显示多路结果。第一次运行可能需要生成 TensorRT engine，因此启动较慢；之后会复用 engine。

更完整的检测、跟踪和二级分类示例：

```bash
deepstream-app \
  -c source4_1080p_dec_infer-resnet_tracker_sgie_tiled_display.txt
```

成功标准：

- 终端没有持续的 `ERROR` 或 `not-negotiated`；
- GPU 有计算和显存占用；
- 有显示器时可以看到视频和检测框；
- 程序结束时正常收到 EOS；
- 模型目录生成与当前设备匹配的 `.engine` 文件。

### 7.3 无显示器时验证

复制一份配置，不要直接修改 SDK 自带文件：

```bash
mkdir -p ~/deepstream-work/configs
cp source30_1080p_dec_infer-resnet_tiled_display.txt \
  ~/deepstream-work/configs/headless.txt
```

编辑 `headless.txt`：

- 禁用显示 sink；
- 或将 sink 设为 `fakesink`；
- 需要远程查看时启用 RTSP sink；
- 需要保存结果时启用编码和文件 sink。

运行：

```bash
deepstream-app -c ~/deepstream-work/configs/headless.txt
```

## 8. 理解 deepstream-app 配置

建议先复制最接近需求的官方配置，再逐项修改。常见配置组：

```text
[application]       应用级设置和性能统计
[tiled-display]     多路画面平铺
[source0]           第一路输入
[source1]           第二路输入
[streammux]         多路合批、分辨率、超时
[primary-gie]       主检测模型
[tracker]           目标跟踪
[secondary-gie0]    二级分类模型
[osd]               检测框和文字
[sink0]             显示、文件、RTSP 或丢弃输出
```

关键原则：

1. `[streammux]` 的 `batch-size` 通常等于输入路数。
2. `[primary-gie]` 的 batch size 应与实际输入路数及 engine 支持能力匹配。
3. RTSP、摄像头等实时源应设置 live source 相关选项。
4. `streammux` 的 `width`、`height` 决定统一推理前尺寸；尺寸不一致时会发生缩放。
5. 需要保持宽高比时启用 padding。
6. 生产环境使用绝对路径，避免因工作目录变化找不到模型或配置。
7. DeepStream 配置中的布尔值通常使用 `0/1`，具体以相应插件文档为准。

## 9. 从单个视频改为自己的输入

### 9.1 本地文件

复制官方单路 URI 示例，将 `[source0]` 的 `uri` 改为：

```ini
uri=file:///home/user/videos/test.mp4
```

必须使用绝对路径，并保留 `file://` URI 格式。

### 9.2 RTSP

```ini
uri=rtsp://username:password@192.168.1.10:554/stream
```

先用 GStreamer 或 VLC 验证 RTSP 地址：

```bash
gst-launch-1.0 rtspsrc location="rtsp://..." latency=200 \
  ! rtph264depay ! h264parse ! avdec_h264 ! fakesink
```

实际生产中还需根据网络情况调整：

- RTSP latency；
- TCP/UDP 传输协议；
- 自动重连；
- 超时；
- 掉线后的 source 重建；
- 时间戳策略。

### 9.3 USB 摄像头

先查看设备：

```bash
v4l2-ctl --list-devices
v4l2-ctl --device=/dev/video0 --list-formats-ext
```

然后复制 SDK 中最接近的 V4L2 camera 示例，修改设备节点、分辨率和帧率。

## 10. 接入自定义 ONNX 检测模型

这是从官方示例进入真实项目的核心步骤。

### 10.1 准备模型

模型导出要求：

- 使用 DeepStream 9.0 对应 TensorRT 支持的 ONNX opset；
- 输入尺寸固定或明确配置动态 shape；
- 明确输入 tensor 名称、输出 tensor 名称；
- 明确预处理：RGB/BGR、缩放系数、均值、归一化；
- 明确后处理：输出布局、类别数、NMS、置信度阈值；
- 在目标设备生成 TensorRT engine。

先用 TensorRT 工具验证 ONNX：

```bash
trtexec \
  --onnx=/home/user/models/model.onnx \
  --saveEngine=/home/user/models/model_fp16.engine \
  --fp16
```

若这里失败，应先修复 ONNX/TensorRT 兼容问题，不要直接归因于 DeepStream。

### 10.2 建立项目目录

```bash
mkdir -p ~/deepstream-work/{configs,models,output,src}
cp /home/user/models/model.onnx ~/deepstream-work/models/
cp /home/user/models/labels.txt ~/deepstream-work/models/
```

建议结构：

```text
deepstream-work/
├── configs/
│   ├── app.txt
│   └── infer_primary.txt
├── models/
│   ├── model.onnx
│   ├── labels.txt
│   └── model_b1_gpu0_fp16.engine
├── output/
└── src/
```

### 10.3 编写 nvinfer 配置

创建 `configs/infer_primary.txt`：

```ini
[property]
gpu-id=0
onnx-file=/home/user/deepstream-work/models/model.onnx
model-engine-file=/home/user/deepstream-work/models/model_b1_gpu0_fp16.engine
labelfile-path=/home/user/deepstream-work/models/labels.txt
batch-size=1
network-mode=2
network-type=0
num-detected-classes=80
gie-unique-id=1
interval=0
process-mode=1

# 以下预处理值必须与模型训练/导出时一致
net-scale-factor=0.003921568627
model-color-format=0

[class-attrs-all]
pre-cluster-threshold=0.25
nms-iou-threshold=0.45
topk=300
```

常用值：

- `network-mode=0/1/2/3`：FP32、INT8、FP16、BEST，实际取值以当前 `Gst-nvinfer` 文档为准。
- `network-type=0`：检测；分类、分割等任务使用其他类型。
- `process-mode=1`：主推理；`2` 为二级推理。
- `interval=0`：每帧推理；设为 `N` 时跳过若干帧，可结合 tracker 提升吞吐。
- `num-detected-classes` 必须与模型一致。

配置值只是模板，不能直接假设适用于任意模型。尤其是 YOLO 等模型通常需要自定义输出解析器。

### 10.4 配置自定义输出解析器

如果模型输出不是 DeepStream 内置解析器直接支持的格式，需要实现或使用与该模型完全匹配的 C/C++ parser，并编译为 `.so`：

```ini
custom-lib-path=/home/user/deepstream-work/lib/libnvdsinfer_custom_impl.so
parse-bbox-func-name=NvDsInferParseCustomModel
```

自定义 parser 负责：

- 读取模型输出 tensor；
- 解码 bbox；
- 应用或配合 NMS；
- 输出类别、置信度和坐标；
- 保证坐标系与网络输入尺寸一致。

不能因为模型名称都是 “YOLO” 就复用任意 parser。不同 YOLO 版本、导出仓库、输出头和是否包含 NMS 都可能不同。

官方接口头文件：

```text
/opt/nvidia/deepstream/deepstream/sources/includes/nvdsinfer_custom_impl.h
```

SDK 内可参考：

```text
/opt/nvidia/deepstream/deepstream/sources/libs/nvdsinfer_customparser
```

### 10.5 将模型接入应用配置

复制一个单路检测配置为 `configs/app.txt`，修改：

```ini
[streammux]
batch-size=1

[primary-gie]
enable=1
gpu-id=0
batch-size=1
config-file=/home/user/deepstream-work/configs/infer_primary.txt
```

再修改 `[source0]` 和 `[sink0]`，运行：

```bash
deepstream-app -c ~/deepstream-work/configs/app.txt
```

### 10.6 首次运行检查

首次生成 engine 时重点观察：

```bash
GST_DEBUG=2 deepstream-app -c ~/deepstream-work/configs/app.txt
```

检查：

- ONNX 是否解析成功；
- 输入输出 tensor 名称和 shape 是否正确；
- parser 函数是否成功加载；
- engine 是否写入预期目录；
- 检测框坐标是否正确；
- 类别名称是否与 `labels.txt` 对齐；
- 前处理是否与训练时一致。

## 11. 增加目标跟踪

管线顺序通常是：

```text
PGIE 检测 -> nvtracker -> SGIE 分类
```

复制官方 tracker 示例配置。DeepStream 9.0 提供 IOU、NvSORT、NvDeepSORT、NvDCF 等配置示例，通常位于：

```text
/opt/nvidia/deepstream/deepstream-9.0/samples/configs/deepstream-app/
```

应用配置示意：

```ini
[tracker]
enable=1
tracker-width=960
tracker-height=544
ll-lib-file=/opt/nvidia/deepstream/deepstream/lib/libnvds_nvmultiobjecttracker.so
ll-config-file=/opt/nvidia/deepstream/deepstream-9.0/samples/configs/deepstream-app/config_tracker_NvDCF_perf.yml
```

选择建议：

- IOU：依赖少、速度快，遮挡场景较弱。
- NvSORT：速度与稳定性折中。
- NvDeepSORT：使用外观特征，遮挡和重识别更好，计算量更高。
- NvDCF：准确率与性能可通过配置调节。

跟踪稳定后，可以增大 PGIE 的 `interval`，让 tracker 补充未执行检测的帧，但必须重新评估漏检、漂移和业务准确率。

## 12. 读取检测结果和自定义业务逻辑

DeepStream 将推理结果放入附着在 `GstBuffer` 上的 metadata：

```text
NvDsBatchMeta
  -> NvDsFrameMeta
    -> NvDsObjectMeta
      -> class_id
      -> confidence
      -> object_id
      -> rect_params
      -> text_params
```

常见做法是在某个插件的 sink/src pad 上添加 probe：

1. 从 `GstBuffer` 获取 `NvDsBatchMeta`；
2. 遍历每一帧；
3. 遍历每一帧中的目标；
4. 读取类别、置信度、跟踪 ID、坐标；
5. 执行业务逻辑或写入消息队列；
6. 不要在 probe 内执行长时间阻塞的网络请求。

生产环境建议将事件写入队列，由独立线程或服务发送到数据库、Kafka、MQTT 或 HTTP 服务。

## 13. 应用开发路线

### 13.1 配置优先

如果需求只是：

- 更换输入源；
- 更换模型；
- 增加 tracker；
- 输出文件或 RTSP；
- 发送标准事件消息；

优先使用 `deepstream-app` 配置完成，开发和维护成本最低。

### 13.2 C/C++ 自定义应用

需要动态增删流、复杂分支、深度控制 metadata 或编写插件时，参考：

```text
/opt/nvidia/deepstream/deepstream/sources/apps/sample_apps/
```

建议学习顺序：

```text
deepstream-test1：单路检测
deepstream-test2：检测 + 跟踪 + 二级分类
deepstream-test3：多路输入
deepstream-test4：消息发送
deepstream-test5：更完整的多流和消息场景
```

构建一般形式：

```bash
cd /opt/nvidia/deepstream/deepstream/sources/apps/sample_apps/deepstream-test1
make
./deepstream-test1 /opt/nvidia/deepstream/deepstream/samples/streams/sample_720p.h264
```

### 13.3 Python

DeepStream 9.0 已弃用传统 Python bindings，并不再发布官方预编译 wheel，NVIDIA 推荐新项目使用 PyServiceMaker。若维护旧 Python 应用：

```bash
cd /opt/nvidia/deepstream/deepstream/sources
git clone https://github.com/NVIDIA-AI-IOT/deepstream_python_apps.git
```

DeepStream 9.0 Python 环境要求包括 Ubuntu 24.04、Python 3.12、gst-python 1.24.1。bindings 需要按仓库说明从源码构建：

```bash
cd deepstream_python_apps/bindings
export CMAKE_BUILD_PARALLEL_LEVEL="$(nproc)"
python3 -m build
```

不要默认执行以上命令就一定成功；还需要先按仓库 `bindings/README.md` 安装构建依赖和初始化子模块。

## 14. 输出方式

### 14.1 本地显示

适合开发调试。需要有效的 X11/Wayland 环境，并正确传递 `DISPLAY`。

### 14.2 文件输出

通常经过：

```text
OSD -> video convert -> encoder -> parser -> muxer -> file sink
```

要检查：

- 编码器是否为当前平台支持的硬件编码器；
- 文件容器与编码格式是否匹配；
- 程序是否正常收到 EOS，否则文件尾可能不完整。

### 14.3 RTSP 输出

适合无显示器设备。启动后 `deepstream-app` 会输出 RTSP URL，可用 VLC 或 GStreamer 打开。

### 14.4 结构化消息

使用 `nvmsgconv` 将 metadata 转为消息，再由 `nvmsgbroker` 发送到 Kafka、MQTT 等系统。发送前定义：

- 事件 schema；
- 摄像头和设备 ID；
- 时间戳来源；
- 重试与离线缓存；
- 消息频率和去重策略；
- 隐私数据处理。

## 15. 性能测试

### 15.1 启用 FPS 统计

在应用配置中启用性能统计：

```ini
[application]
enable-perf-measurement=1
perf-measurement-interval-sec=5
```

### 15.2 排除显示和 OSD 影响

测纯推理吞吐时：

- 关闭 tiled display；
- 关闭 OSD；
- 使用 fakesink；
- 固定输入路数、分辨率、编码和帧率；
- 先预生成 engine；
- 预热后再记录结果。

### 15.3 监控资源

x86：

```bash
watch -n 1 nvidia-smi
nvidia-smi dmon
```

Jetson：

```bash
sudo tegrastats
```

Jetson 做基准测试前可根据设备能力设置性能模式：

```bash
sudo nvpmodel -q
sudo jetson_clocks
```

记录：

- 每路 FPS 和总吞吐；
- 端到端延迟；
- GPU 利用率和显存；
- 解码器、编码器利用率；
- CPU、内存、温度和功耗；
- 掉帧、重连和错误次数。

## 16. 常见问题

### 16.1 找不到 DeepStream 插件

```text
No such element or plugin 'nvinfer'
```

处理：

```bash
sudo ldconfig
rm -f ~/.cache/gstreamer-1.0/registry.*.bin
export GST_PLUGIN_PATH=/opt/nvidia/deepstream/deepstream/lib/gst-plugins:$GST_PLUGIN_PATH
gst-inspect-1.0 nvinfer
```

### 16.2 TensorRT engine 反序列化失败

常见原因：

- engine 由其他 GPU 生成；
- TensorRT/CUDA/DeepStream 版本变化；
- batch size 或输入 shape 改变；
- engine 文件损坏或没有读取权限。

处理：

```bash
rm /path/to/model.engine
deepstream-app -c app.txt
```

让 DeepStream 在目标设备重新生成 engine。

### 16.3 没有检测框

按顺序检查：

1. 原始 ONNX 用 `trtexec` 是否能运行；
2. 模型输入 shape 和颜色顺序；
3. `net-scale-factor`、均值和归一化；
4. 输出 tensor 和 parser 是否匹配；
5. 类别数是否正确；
6. 阈值是否过高；
7. 坐标解码和 NMS 是否正确；
8. OSD 是否启用。

### 16.4 显示相关错误

```text
Could not open display
No EGL Display
```

无桌面环境使用 fakesink、文件或 RTSP。Docker 中显示时确认：

```bash
echo "$DISPLAY"
ls -l /tmp/.X11-unix
```

### 16.5 RTSP 卡住或 EOS 异常

DeepStream 9.0 官方说明中提到 `rtpjitterbuffer` 可能导致 RTSP 到 EOS 时卡住。原生安装可在安装依赖后执行一次：

```bash
cd /opt/nvidia/deepstream/deepstream
sudo ./update_rtpmanager.sh
```

容器内按官方说明使用 `user_additional_install.sh`。

### 16.6 GStreamer 协商失败

```text
not-negotiated
Internal data stream error
```

使用以下方式定位：

```bash
GST_DEBUG=3 deepstream-app -c app.txt
GST_DEBUG_DUMP_DOT_DIR=/tmp/ds-dot deepstream-app -c app.txt
```

重点核对插件间的格式、分辨率、内存类型和 caps。

### 16.7 配置路径错误

DeepStream 配置经常包含多层相对路径。程序从不同目录启动时可能找不到模型、标签或 parser。项目配置优先使用绝对路径，并检查：

```bash
realpath /path/to/file
ls -l /path/to/file
```

## 17. 从零到项目可用的执行清单

1. 确认 GPU/Jetson 型号。
2. 查询对应 DeepStream、系统、JetPack、CUDA、TensorRT 和驱动版本。
3. 选择原生安装或 Docker，不混装不兼容版本。
4. 用 `nvidia-smi` 或 `tegrastats` 验证 GPU。
5. 用 `gst-inspect-1.0 nvinfer` 验证插件。
6. 跑通官方单路检测示例。
7. 跑通检测 + tracker 示例。
8. 将输入替换为自己的本地视频。
9. 将输入替换为真实 RTSP/摄像头。
10. 用 `trtexec` 单独验证自定义 ONNX。
11. 编写 `nvinfer` 配置。
12. 如有需要，编译与模型输出完全匹配的自定义 parser。
13. 在目标设备生成 TensorRT engine。
14. 核对检测框、类别、置信度和坐标。
15. 增加 tracker 并验证 ID 稳定性。
16. 添加文件、RTSP 或消息输出。
17. 无显示和关闭 OSD 条件下测试纯性能。
18. 测试断流、重连、坏帧、磁盘满和进程重启。
19. 固化镜像、配置、模型 checksum 和版本信息。
20. 上线前做长时间稳定性测试。

## 18. 建议保留的项目记录

每个部署版本至少记录：

```text
设备/GPU：
系统版本：
JetPack/L4T：
NVIDIA Driver：
CUDA：
TensorRT：
DeepStream：
容器镜像及 digest：
模型来源和 git commit：
ONNX SHA256：
TensorRT engine 生成设备：
输入分辨率/帧率/路数：
推理尺寸/精度/batch：
parser 版本：
tracker 配置：
平均 FPS/P95 延迟：
已知问题：
```

生成 checksum：

```bash
sha256sum model.onnx
docker image inspect nvcr.io/nvidia/deepstream:9.0-triton-multiarch \
  --format '{{index .RepoDigests 0}}'
```

## 19. 官方资料

- DeepStream 9.0 Developer Guide：  
  https://docs.nvidia.com/metropolis/deepstream/9.0/
- Installation：  
  https://docs.nvidia.com/metropolis/deepstream/9.0/text/DS_Installation.html
- Quickstart：  
  https://docs.nvidia.com/metropolis/deepstream/9.0/text/DS_Quickstart.html
- deepstream-app 参考：  
  https://docs.nvidia.com/metropolis/deepstream/9.0/text/DS_ref_app_deepstream.html
- Gst-nvinfer：  
  https://docs.nvidia.com/metropolis/deepstream/9.0/text/DS_plugin_gst-nvinfer.html
- 使用自定义模型：  
  https://docs.nvidia.com/metropolis/deepstream/9.0/text/DS_using_custom_model.html
- Docker Containers：  
  https://docs.nvidia.com/metropolis/deepstream/9.0/text/DS_docker_containers.html
- Python 示例与 bindings：  
  https://github.com/NVIDIA-AI-IOT/deepstream_python_apps
- NVIDIA NGC DeepStream：  
  https://catalog.ngc.nvidia.com/orgs/nvidia/resources/deepstream

## 20. 最短实践路线

如果只想最快跑通：

```bash
# 1. 确认环境
nvidia-smi
deepstream-app --version-all

# 2. 验证插件
gst-inspect-1.0 nvinfer

# 3. 跑官方示例
cd /opt/nvidia/deepstream/deepstream-9.0/samples/configs/deepstream-app
deepstream-app -c source30_1080p_dec_infer-resnet_tiled_display.txt

# 4. 复制配置
mkdir -p ~/deepstream-work/configs
cp source30_1080p_dec_infer-resnet_tiled_display.txt \
  ~/deepstream-work/configs/app.txt

# 5. 修改 app.txt 的 source、primary-gie 和 sink
# 6. 运行自己的管线
deepstream-app -c ~/deepstream-work/configs/app.txt
```

实际项目中应遵循：

```text
先跑通官方样例
-> 再替换输入
-> 再替换模型
-> 再增加 tracker/业务逻辑
-> 最后做输出、性能和稳定性优化
```
