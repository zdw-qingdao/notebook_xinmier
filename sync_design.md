# RTSP 推理结果与 WebRTC 画面的同帧同步方案

## 1. 目标

系统中的同一路相机流经过 MediaMTX 后分成两条消费链路：

```text
相机 RTSP
   │
   ▼
MediaMTX camera-{id}
   ├── RTSP/RTP ──► 后端解码 ──► 模型推理 ──► SSE 预测结果
   └── WHEP/WebRTC ──► 浏览器播放
```

同步目标不是获取相机真实采集时间，也不要求得到 Unix 时间。唯一目标是：

> 对于同一个视频帧，前端和后端得到完全相同的帧标识，并以这个标识配对画面与推理结果。

本方案使用 RTP 包头中的 32 位 `Timestamp` 作为帧标识。后文统一称为
`rtp_timestamp`。

## 2. 核心结论

前端通过 `HTMLVideoElement.requestVideoFrameCallback()` 获取：

```typescript
metadata.rtpTimestamp
```

后端必须在 RTSP 解码前，从同一路 MediaMTX RTSP 流的 RTP 包头获取：

```text
RTP Header.Timestamp
```

然后将该值一直绑定到解码帧、推理任务和预测结果。前端不需要把
`rtpTimestamp` 转换成毫秒；直接按整数相等进行匹配：

```text
前端帧 metadata.rtpTimestamp == 后端结果 rtp_timestamp
```

不能使用以下值进行同帧匹配：

- 前后端系统时间；
- `time.time()`、`performance.now()` 或 `performance.timeOrigin`；
- 浏览器的 `captureTime`、`receiveTime` 或 `expectedDisplayTime`；
- OpenCV 的 `CAP_PROP_PTS`、`CAP_PROP_POS_MSEC`；
- SSE 消息到达时间或模型推理完成时间。

这些值可以用于延迟统计，但不能作为同一帧的可靠标识。

## 3. 为什么 RTP timestamp 可以标识同一帧

H.264 RTP 使用 90 kHz 时钟。同一个 H.264 Access Unit，也就是同一个展示帧，
即使被拆成多个 RTP 包，这些包也具有相同的 RTP timestamp。

MediaMTX 1.19.2 在 H.264 RTSP 转 WebRTC 时会重新分包，但 WebRTC 输出包的
timestamp 仍以输入帧第一个 RTP 包的 timestamp 为基准：

```go
pkt.Timestamp += u.RTPPackets[0].Timestamp
track.WriteRTPWithNTP(pkt, ntp)
```

对应源码：
[MediaMTX v1.19.2 `from_stream.go`](https://github.com/bluenviron/mediamtx/blob/v1.19.2/internal/protocols/webrtc/from_stream.go)。

因此，在当前 H.264 链路中：

```text
MediaMTX RTSP 输出帧的 RTP timestamp
          ==
MediaMTX WebRTC 输出帧的 RTP timestamp
```

上线前仍应使用实际相机和当前 MediaMTX 二进制做一次端到端验证，避免未来升级
MediaMTX、切换编码格式或增加转码后改变 timestamp 行为。

`useAbsoluteTimestamp` 与本方案无关。本方案只比较同一 RTP 时基中的帧标识，
不需要 RTCP Sender Report，也不需要保留相机绝对采集时间。

## 4. 当前实现为什么不能保证同帧

当前后端在
[`backend/preview_inference/rtsp_source.py`](backend/preview_inference/rtsp_source.py)
中使用 OpenCV：

```python
media_timestamp_ms = (
    capture_origin_ms
    + capture.get(CAP_PROP_PTS) / fps * 1000
)
```

`CAP_PROP_PTS` 是 FFmpeg/OpenCV 转换后的展示时间，使用 FPS time base，可能还经过
起点归一化。它不暴露原始 RTP timestamp 的 32 位随机初值。因此，仅凭
`CAP_PROP_PTS` 无法还原浏览器拿到的 `metadata.rtpTimestamp`。

当前前端在
[`frontend/src/pages/project/modelDetail/inference/MediaPredictionPreview.tsx`](frontend/src/pages/project/modelDetail/inference/MediaPredictionPreview.tsx)
中读取 `receiveTime` 或 `captureTime`，然后在
[`playoutDelay.ts`](frontend/src/pages/project/modelDetail/inference/playoutDelay.ts)
中按 100 ms 容差寻找相近帧。这属于延迟标定和近似匹配，不等价于同一帧。

结论：只使用 `cv2.VideoCapture` 不能实现本方案要求的完全同帧匹配。

## 5. 后端实现

### 5.1 必须在 RTP 层取值

后端需要引入能够访问 RTP 包头的 RTSP/RTP 接收层。可选实现包括：

- 使用 gortsplib 接收 MediaMTX RTSP 流；
- 使用 GStreamer，并在 `rtph264depay` 前解析 `GstRTPBuffer.timestamp`；
- 实现独立的 RTP-aware 媒体读取组件，再把解码后的图像及 timestamp 交给现有
  Python 推理运行时。

无论选择哪种库，必须遵循同一个数据流：

```text
接收 RTP 包
  → 读取 packet.Timestamp
  → 按 Timestamp 聚合属于同一帧的 RTP 包
  → H.264 depacketize，得到完整 Access Unit
  → 解码为 BGR/RGB 图像
  → 将原始 Timestamp 绑定到解码图像
  → 模型推理
  → 在预测结果中返回同一个 Timestamp
```

后端帧对象应增加原始 RTP timestamp：

```python
@dataclass
class Frame:
    image: Any
    rtp_timestamp: int
    frame_index: int
```

注意：timestamp 必须从组成该帧的 RTP 包中取得，不能在解码完成后根据 FPS、帧号
或接收时间重新计算。

### 5.2 推理事件协议

预测事件至少包含：

```json
{
  "session_id": "preview-session-id",
  "rtp_timestamp": 2918473920,
  "inference_ms": 35.2,
  "task": "detect",
  "items": []
}
```

建议使用下面的复合键：

```text
(session_id, rtp_timestamp)
```

`session_id` 用来隔离不同预览会话，避免 RTP timestamp 回绕或重新建流后与旧缓存
冲突。

如果 RTSP 或 WHEP 发生断开重连，第一版实现应结束旧预览会话并创建新会话，同时
清空前端帧缓存。不要在同一个 `session_id` 中静默跨越流重连。如果未来必须支持
无感重连，应再增加由统一媒体接收层产生的 `stream_epoch`：

```text
(session_id, stream_epoch, rtp_timestamp)
```

### 5.3 可选的 frame_started 事件

模型推理可能耗时较长。为了减少前端需要长期保存的所有 WebRTC 帧，后端可以在选中
一帧准备推理时，立即发送轻量事件：

```json
{
  "event": "frame_started",
  "rtp_timestamp": 2918473920
}
```

前端收到后保留对应画面，其他未进入推理的旧帧可以尽快释放。推理完成后再发送带有
相同 `rtp_timestamp` 的 `prediction` 事件。

## 6. 前端实现

### 6.1 获取帧标识

使用 `requestVideoFrameCallback`：

```typescript
const observeFrame = (
  _now: number,
  metadata: VideoFrameCallbackMetadata,
) => {
  const rtpTimestamp = metadata.rtpTimestamp;
  if (rtpTimestamp === undefined) {
    // 当前浏览器无法提供精确同帧同步能力。
    return;
  }

  // 在 video 仍指向该帧时复制到 Canvas、ImageBitmap 或 VideoFrame。
  saveFrame(rtpTimestamp, video);
  video.requestVideoFrameCallback(observeFrame);
};
```

`rtpTimestamp` 是可选浏览器能力。如果浏览器没有提供它，就不能声称实现了精确
同帧同步。可以显示原始视频或明确降级为近似模式，但不应继续用墙钟时间冒充精确
匹配。

### 6.2 按 timestamp 缓存和匹配

前端维护两个有界缓存：

```typescript
const videoFrames = new Map<number, BufferedVideoFrame>();
const predictions = new Map<number, PreviewPrediction>();
```

收到 WebRTC 帧时：

```typescript
videoFrames.set(metadata.rtpTimestamp, copiedFrame);
tryRender(metadata.rtpTimestamp);
```

收到 SSE 预测时：

```typescript
predictions.set(prediction.rtp_timestamp, prediction);
tryRender(prediction.rtp_timestamp);
```

配对逻辑只能使用严格相等：

```typescript
function tryRender(timestamp: number) {
  const frame = videoFrames.get(timestamp);
  const prediction = predictions.get(timestamp);
  if (!frame || !prediction) return;

  drawFrame(frame);
  drawPrediction(prediction);
  videoFrames.delete(timestamp);
  predictions.delete(timestamp);
}
```

不要使用“最近 timestamp”、毫秒容差或消息到达顺序匹配。网络丢包、浏览器丢帧或
后端跳帧时，无法配对的记录应过期删除，而不是错误地绑定到相邻帧。

### 6.3 显示策略

帧标识相同只能解决“哪一个预测属于哪一帧”，不能消除模型推理耗时。要让用户看到
严格同步的画面和检测框，前端必须缓存视频帧，等待相同 timestamp 的预测到达后再
显示。

当前后端只推理最新帧，模型速度也可能低于相机 FPS，因此不是所有 WebRTC 帧都会有
预测。可选择以下产品策略之一：

1. 只播放成功配对的预测帧，显示 FPS 等于推理 FPS；
2. 保持上一张已配对画面，直到下一张已配对画面到达；
3. 原始视频连续播放，但仅在完全配对时显示检测框，未配对帧不显示框。

如果要求“画面中的框始终属于当前画面”，推荐第 1 或第 2 种。将最新预测持续覆盖
在连续实时视频上虽然更流畅，但它不再是严格同帧同步。

缓存必须设置上限。过期条件可以同时包含：

- 最大缓存帧数；
- 最大保留时长；
- 预测完成后已经确定不会再使用的 timestamp；
- 会话停止、WHEP 断开或切换相机。

## 7. timestamp 回绕与断流

RTP timestamp 是无符号 32 位整数。H.264 使用 90 kHz 时钟，大约每 13.26 小时
回绕一次。

仅做同帧相等比较时，直接比较 32 位值即可。只有计算两个 timestamp 的相对时间时，
才需要按模 `2^32` 处理：

```typescript
const UINT32 = 2 ** 32;
const deltaTicks = (current - previous + UINT32) % UINT32;
const deltaMs = (deltaTicks * 1000) / 90000;
```

该换算只用于统计和缓存过期判断，不能代替同帧相等匹配。

出现以下情况时必须清空缓存并建立新会话或新 `stream_epoch`：

- RTSP 源重新连接；
- MediaMTX 路径重新创建；
- WHEP PeerConnection 重建；
- timestamp 出现不能解释为正常回绕的大幅跳变；
- 相机或编码格式切换。

## 8. 对现有代码的改造范围

后端：

1. 替换或封装
   [`LatestFrameSource`](backend/preview_inference/rtsp_source.py)，使其从 RTP 层返回
   `{image, rtp_timestamp}`；
2. 在 [`Frame`](backend/preview_inference/domain.py) 中增加 `rtp_timestamp`；
3. 在
   [`prediction_payload`](backend/preview_inference/controller.py) 中输出
   `rtp_timestamp`；
4. 保持 SSE 原有传输方式，但以 `rtp_timestamp` 作为帧关联字段；
5. 删除相机同步对 `capture_origin_ms + CAP_PROP_PTS / fps` 的依赖。

前端：

1. 在 `requestVideoFrameCallback` 中读取 `metadata.rtpTimestamp`；
2. 将当前按 `receiveTime/captureTime` 建立的时间线替换为按
   `rtpTimestamp` 建立的帧缓存；
3. SSE 预测结果按严格相等的 `rtp_timestamp` 查找视频帧；
4. 当前三秒延迟标定不再负责识别同一帧；显示延迟改为由实际等待配对的缓存自然产生；
5. 会话停止、相机切换和 WHEP 断开时释放全部缓存帧。

## 9. 验证标准

端到端验收必须检查整数 timestamp，而不是检查时间差：

```text
backend_prediction.rtp_timestamp
    === frontend_video_frame.metadata.rtpTimestamp
```

建议按以下步骤验证：

1. 使用画面内烧录递增帧号的 H.264 测试流；
2. 后端记录每个实际推理帧的 `rtp_timestamp`；
3. 前端记录每个 `requestVideoFrameCallback` 的 `rtpTimestamp`；
4. 确认每个预测结果都能找到整数完全相等的前端帧；
5. 人工核对烧录帧号与检测框所在画面一致；
6. 测试后端跳帧、浏览器丢帧、网络抖动和预测乱序；
7. 测试 RTSP/WHEP 断开后旧缓存不会与新会话匹配；
8. 长时间测试 timestamp 回绕处理。

验收时不得使用 `±100 ms` 等容差。找不到完全相同的 timestamp 时，应将该帧视为
未配对并记录指标，不能自动匹配相邻帧。

## 10. 最终方案摘要

```text
后端：从 RTP Header.Timestamp 取值
       ↓
解码帧携带原始 rtp_timestamp
       ↓
推理结果通过 SSE 返回相同 rtp_timestamp

前端：从 requestVideoFrameCallback.metadata.rtpTimestamp 取值
       ↓
缓存对应 WebRTC 画面
       ↓
按 rtp_timestamp 严格相等配对后显示画面和检测框
```

本方案不需要真实采集时间、不需要前后端时钟同步，也不需要估算网络延迟。它只要求
MediaMTX 的 RTSP 和 WebRTC 输出保留同一帧的 RTP timestamp，以及后端在 RTP 层读取
并贯穿传递这个值。
