ARG DEEPSTREAM_VERSION=9.0
FROM nvcr.io/nvidia/deepstream:${DEEPSTREAM_VERSION}-samples-multiarch

# DeepStream 9.0 官方镜像基于 Ubuntu 24.04，并内置匹配版本的 CUDA、
# TensorRT、GStreamer NVIDIA 插件、参考应用和样例资源。
ARG DEEPSTREAM_VERSION
ENV DEEPSTREAM_VERSION=${DEEPSTREAM_VERSION}
ENV NVIDIA_VISIBLE_DEVICES=all
ENV NVIDIA_DRIVER_CAPABILITIES=compute,utility,video,graphics

ENV DEBIAN_FRONTEND=noninteractive
ENV TZ=Asia/Shanghai
ENV LANG=C.UTF-8
ENV LC_ALL=C.UTF-8

SHELL ["/bin/bash", "-c"]

# 先用官方 HTTP 源安装 CA 证书，再切换清华 HTTPS 源（避免证书未就绪时 apt 失败）
RUN apt-get update && \
    apt-get install -y --no-install-recommends ca-certificates && \
    sed -i 's|http://archive.ubuntu.com/ubuntu|https://mirror.sjtu.edu.cn/ubuntu|g' /etc/apt/sources.list && \
    sed -i 's|http://security.ubuntu.com/ubuntu|https://mirror.sjtu.edu.cn/ubuntu|g' /etc/apt/sources.list && \
    apt-get update

# ============================================================
# [1/6] 系统基础依赖
# ============================================================
RUN echo "========== [1/6] 安装系统基础依赖 ==========" && \
    apt-get update && \
    apt-get install -y --no-install-recommends \
        curl wget gnupg2 lsb-release \
        software-properties-common apt-transport-https \
        build-essential gcc g++ make cmake \
        libpq-dev libffi-dev libssl-dev \
        git unzip vim nano htop net-tools \
        supervisor ffmpeg \
        libgl1 libglib2.0-0 && \
    echo "========== [1/6] 系统基础依赖 ✓ =========="

# ============================================================
# [2/6] 安装 SeaweedFS
# ============================================================
RUN echo "========== [2/6] 安装 SeaweedFS ==========" && \
    apt-get install -y --no-install-recommends fuse3 && \
    ARCH=$(dpkg --print-architecture) && \
    WEED_VERSION="3.79" && \
    wget -q "https://github.com/seaweedfs/seaweedfs/releases/download/${WEED_VERSION}/linux_${ARCH}.tar.gz" -O /tmp/weed.tar.gz && \
    tar -xzf /tmp/weed.tar.gz -C /usr/local/bin/ && \
    chmod +x /usr/local/bin/weed && \
    rm /tmp/weed.tar.gz && \
    mkdir -p /data1 /data && \
    echo "========== [2/6] SeaweedFS ✓ =========="

# ============================================================
# [3/6] 安装 Miniconda
# ============================================================
ENV CONDA_DIR=/opt/miniconda
ENV CONDA_ENV=/opt/autopipe/venv
ENV PATH="${CONDA_DIR}/bin:${PATH}"

# PyPI 源（上海交大）
ENV PIP_INDEX_URL=https://mirror.sjtu.edu.cn/pypi/web/simple
ENV PIP_TRUSTED_HOST=mirror.sjtu.edu.cn

# Conda 源（上海交大）
ENV CONDA_MIRROR=https://mirror.sjtu.edu.cn/anaconda

RUN echo "========== [3/6] 安装 Miniconda ==========" && \
    ARCH=$(uname -m) && \
    if [ "$ARCH" = "x86_64" ]; then CONDA_ARCH="x86_64"; else CONDA_ARCH="aarch64"; fi && \
    wget -q "https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-${CONDA_ARCH}.sh" -O /tmp/miniconda.sh && \
    bash /tmp/miniconda.sh -b -p "${CONDA_DIR}" && \
    rm /tmp/miniconda.sh && \
    conda init bash && \
    printf '%s\n' \
        'channels:' \
        '  - defaults' \
        'show_channel_urls: true' \
        'default_channels:' \
        "  - ${CONDA_MIRROR}/pkgs/main" \
        "  - ${CONDA_MIRROR}/pkgs/r" \
        'custom_channels:' \
        "  conda-forge: ${CONDA_MIRROR}/cloud" \
        "  pytorch: ${CONDA_MIRROR}/cloud" \
        > /root/.condarc && \
    conda update -n base -c defaults conda -y && \
    echo "========== [3/6] Miniconda ✓ =========="

# ============================================================
# [4/6] 创建 Python 3.12 环境并手动安装后端依赖
# ============================================================
RUN echo "========== [4/6] 安装后端 Python 依赖 ==========" && \
    conda create -p "${CONDA_ENV}" python=3.12 pip -y && \
    "${CONDA_ENV}/bin/pip" install --no-cache-dir \
        alembic \
        boto3 \
        "celery" \
        fastapi \
        httpx \
        numpy \
        onnx \
        onnxruntime \
        onnxslim \
        opencv-python-headless \
        packaging \
        Pillow \
        psycopg2-binary \
        pydantic \
        python-multipart \
        "ray[default]" \
        redis \
        sqlalchemy \
        typing_extensions \
        ultralytics \
        "uvicorn[standard]" && \
    "${CONDA_ENV}/bin/python" --version && \
    echo "========== [4/6] 后端 Python 依赖 ✓ =========="

ENV PATH="${CONDA_ENV}/bin:${CONDA_DIR}/bin:${PATH}"
ENV CONDA_DEFAULT_ENV="${CONDA_ENV}"
ENV CONDA_PREFIX="${CONDA_ENV}"
RUN echo "conda activate ${CONDA_ENV}" >> /root/.bashrc

# ============================================================
# [5/6] 安装 Node.js & pnpm，拉取依赖并构建前端
# ============================================================
ENV NODE_MAJOR=24
RUN echo "========== [5/6] 安装 Node.js & pnpm ==========" && \
    curl -fsSL https://deb.nodesource.com/setup_${NODE_MAJOR}.x | bash - && \
    apt-get update && \
    apt-get install -y --no-install-recommends nodejs && \
    apt-get clean && rm -rf /var/lib/apt/lists/* && \
    corepack enable && \
    corepack prepare pnpm@latest --activate && \
    node --version && pnpm --version

COPY frontend/package.json frontend/pnpm-lock.yaml frontend/pnpm-workspace.yaml frontend/.npmrc /opt/autopipe/project/frontend/
WORKDIR /opt/autopipe/project/frontend
ENV HUSKY=0
RUN pnpm install --frozen-lockfile && \
    echo "========== [5/6] 前端依赖安装 ✓ =========="

# MediaMTX：RTSP 拉流 + WHEP/WebRTC 播放
ARG MEDIAMTX_VERSION=1.19.2
RUN ARCH=$(dpkg --print-architecture) && \
    MTX_ARCH="${ARCH}" && \
    wget -q \
      "https://github.com/bluenviron/mediamtx/releases/download/v${MEDIAMTX_VERSION}/mediamtx_v${MEDIAMTX_VERSION}_linux_${MTX_ARCH}.tar.gz" \
      -O /tmp/mediamtx.tar.gz && \
    tar -xzf /tmp/mediamtx.tar.gz -C /usr/local/bin mediamtx && \
    chmod +x /usr/local/bin/mediamtx && \
    rm /tmp/mediamtx.tar.gz

# ============================================================
# [6/6] 配置 supervisor & 环境
# ============================================================
RUN echo "========== [6/6] 配置服务管理 ==========" && \
    mkdir -p /var/log/supervisor /opt/autopipe

COPY docker/supervisord.conf /etc/supervisor/conf.d/supervisord.conf

RUN echo "========== [6/6] 服务管理配置 ✓ =========="

WORKDIR /opt/autopipe/project
ENV CI=true

# ============================================================
# [7/7] 向 Conda Python 注入 DeepStream 的系统 Python 绑定
# ============================================================
# DeepStream 镜像的 /usr/bin/python3.12 已有 gi 及 GStreamer introspection
# 绑定。${CONDA_ENV} 同为 Python 3.12，通过 .pth 复用该 ABI 兼容的系统包，
# 原生 DeepStream/GStreamer 插件仍由镜像全局库路径加载。
RUN echo "========== [7/7] 配置 DeepStream Python 绑定 ==========" && \
    printf '%s\n' /usr/lib/python3/dist-packages \
        > "${CONDA_ENV}/lib/python3.12/site-packages/deepstream-system-bindings.pth" && \
    "${CONDA_ENV}/bin/python" -c 'import gi; gi.require_version("Gst", "1.0"); from gi.repository import Gst; Gst.init(None); print("PyGObject/GStreamer OK")' && \
    echo "========== [7/7] DeepStream Python 绑定 ✓ =========="

COPY docker/entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

ENTRYPOINT ["/entrypoint.sh"]
