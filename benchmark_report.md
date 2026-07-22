# OpenCV/PyTorch 与 DeepStream/TensorRT 对比报告

## 实验状态
- 结果目录：`/mnt/data0/liuyu/autopipe/experiments/opencv_deepstream_benchmark/results/raw/formal_20260714`
- 输入路数：10
- 输入说明：当前十路由两个物理视频各重复五次，正式报告不得描述为十个独立视频。
- 统计原则：模型加载、TensorRT engine 构建和 warm-up 不计入稳态吞吐。

## 环境基线
- CPU：2 路 Intel Xeon Platinum 8582C，共 120 物理核、240 逻辑核。
- GPU：NVIDIA GeForce RTX 5090，实验固定使用 GPU 5。
- CPU 软件：Python 3.12、OpenCV 4.13、PyTorch 2.13 CPU。
- GPU 软件：DeepStream 8.0、CUDA 12.8、TensorRT 10.9；DeepStream 7.1 因不支持 Blackwell 未纳入测试。
- 模型：TrafficCamNet ResNet18 ONNX，输入 960×544，十路 batch；首个视频的固定首帧在 PyTorch 转换模型与 ONNX Runtime FP32 间已通过容差校验。

## 汇总
- OpenCV 串行解码 + PyTorch CPU 单 worker：总吞吐 17.41 ± 1.25 FPS；P95 延迟 1974.28 ms；CPU 累计核占用 430.1%
- OpenCV 串行解码 + PyTorch CPU 8 workers：总吞吐 91.51 ± 4.40 FPS；P95 延迟 373.87 ms；CPU 累计核占用 3220.2%
- DeepStream + TensorRT FP32 十路：十路总吞吐 3463.71 ± 3.40 FPS；GPU 60.9%；NVDEC 9.8%
- DeepStream + TensorRT FP16 十路：十路总吞吐 8828.33 ± 21.26 FPS；GPU 43.7%；NVDEC 15.7%

## 关键结论
- TensorRT FP32 相对 CPU 8 workers 的吞吐倍数：37.85 倍。
- TensorRT FP16 相对 CPU 8 workers 的吞吐倍数：96.48 倍。
- TensorRT FP16 相对 TensorRT FP32 的吞吐倍数：2.55 倍。
- GPU PERF 采用十路当前 FPS 之和，并丢弃全零行和首个十路均非零的 warm-up 行。

## 解释边界
- CPU 使用单一调度线程轮询解码十路文件，并发仅用于 PyTorch 推理；GPU 使用十路 NVDEC 并行解码和批量推理。
- FP32 组用于统一数值精度下的系统对比；FP16 组用于衡量实际 GPU 部署收益。
- 当前十路由两个物理视频重复组成，只能验证十路并发能力，不能代表十种码流的兼容性。
- 若运行时 GPU 上有其他任务，结果无效，应清空目标 GPU 后重跑三轮正式实验。
- GPU 资源均值覆盖容器启动与退出过程，峰值更能表示稳态压力；本轮未提供逐帧 GPU 端到端延迟，因此不与 CPU P95 延迟做数值比较。
- TensorRT 检测框未通过逐框数值复核；本轮确认了 FP32/FP16 engine 成功构建及十路推理完成，精度结论仅覆盖 PyTorch 与 ONNX Runtime。
