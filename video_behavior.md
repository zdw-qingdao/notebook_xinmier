# 视频行为分析开源模型与端侧选型

先区分两类：“视频大模型”适合开放式问答、描述和零样本判断；如果只是识别跌倒、打架、抽烟、打电话等固定行为，端侧通常用轻量动作识别模型更快、更准、更稳定。

## 可处理视频的开源/开放权重大模型

- [SmolVLM2](https://huggingface.co/blog/smolvlm2)：256M、500M、2.2B，Apache 2.0。最适合端侧尝试；官方称 256M/500M 视频推理约需 1.38GB/1.8GB GPU 显存。中文能力相对一般。
- [LLaVA-OneVision](https://github.com/LLaVA-VL/LLaVA-NeXT)：0.5B、7B、72B，支持图片和视频。0.5B 很小，但视频帧产生的视觉 token 较多，官方仍建议视频任务使用约 16GB 显存。
- [Qwen2.5-VL](https://qwenlm.github.io/zh/blog/qwen2.5-vl/)：3B、7B、72B，中文和时间定位能力较好。3B 量化后适合 Jetson Orin、带独显的小主机，不适合普通摄像头芯片。注意 [3B 模型当前是研究许可](https://huggingface.co/Qwen/Qwen2.5-VL-3B-Instruct/blob/main/LICENSE)，商用需要确认授权。
- [VideoLLaMA3](https://github.com/DAMO-NLP-SG/VideoLLaMA3)：2B、7B，支持长视频理解和时间定位。2B 可在较强端侧 GPU 上量化运行，但项目说明主要面向非商用研究。
- [InternVideo2](https://github.com/OpenGVLab/InternVideo)：覆盖动作识别、检索、时序定位、视频问答，模型效果较强，但 1B 级编码器也不算轻，更适合服务器或高端 Jetson。

## 真正适合实时端侧的行为模型

- [MoViNet-A0/A1 Stream](https://github.com/tensorflow/models/tree/master/official/projects/movinet)：专门为手机和流式视频设计，支持量化 TFLite，首选。
- [X3D-XS/S](https://github.com/facebookresearch/SlowFast/blob/main/MODEL_ZOO.md)：XS 约 3.8M 参数、0.6 GFLOPs，适合 ONNX/TensorRT。
- [TSM + MobileNetV2](https://github.com/mit-han-lab/temporal-shift-module)：时间建模几乎不增加参数和计算量，官方已有 Jetson Nano 实时示例。
- [ST-GCN / CTR-GCN](https://github.com/open-mmlab/mmaction2)：基于人体骨骼序列，适合跌倒、挥手、打斗等肢体行为，需要搭配轻量姿态模型。
- PoseC3D：比普通骨骼模型抗关键点噪声更强，但计算量稍高。

## 推荐选择

- 手机、树莓派、摄像头 NPU：`MoViNet-A0 Stream INT8` 或 `TSM-MobileNetV2`
- Jetson Nano/Orin：`X3D-XS`、轻量姿态模型 + `ST-GCN`
- 需要自然语言描述：`SmolVLM2-500M`
- 中文问答、复杂行为推理：`Qwen2.5-VL-3B 4bit`，建议至少 Orin 8GB 级别
- 实际监控系统：`YOLO-N + ByteTrack + MoViNet/X3D`，大模型只负责二次复核和生成说明

端侧实时分析不建议让大模型逐帧处理。通常每秒抽取少量帧或短片段，否则视觉 token、显存和延迟会迅速增加。
