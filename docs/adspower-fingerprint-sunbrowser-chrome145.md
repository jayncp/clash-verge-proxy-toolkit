# AdsPower 指纹参数示例（SunBrowser · Chrome 145）

> 这是公开仓库示例。真实噪音种子、设备名称、MAC 地址等可复现身份信息不要提交到 Git。

硬件与 WebGL 等需自洽为同一台真实机型。以下模板以 MacBook Air（M4）常见规格为例，并与 AdsPower 内可选的 16 GB 内存预设对齐；若模板只有「M4」而无 Pro/Max，按 M4 填写即可。

```text
浏览器:        SunBrowser [Chrome 145]
User-Agent:    Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.xxxx.xxx Safari/537.36
WebRTC:        替换
时区:          基于 IP
地理位置:      [询问] 基于 IP
语言:          基于 IP
界面语言:      基于语言
分辨率:        基于 User-Agent
字体:          默认
Canvas:        噪音 [填写本地种子]
WebGL图像:     噪音 [填写本地种子]
AudioContext:  噪音 [填写本地种子]
媒体设备:      噪音 [Auto]
ClientRects:   噪音 [填写本地种子]
SpeechVoices:  噪音
WebGL元数据:   Google Inc. (Apple)
              ANGLE (Apple, ANGLE Metal Renderer: Apple M4, Unspecified Version)
WebGPU:        基于 WebGL
CPU:           10 核
RAM:           16 GB
设备名称:      [填写本地设备名称]
MAC地址:       [填写本地 MAC 地址]
Do Not Track:  关闭
端口扫描保护:   [启用]
硬件加速:      默认
禁用TLS特性:   [关闭]
```

如需记录真实配置，请放入 `docs/local/`；该目录已在 `.gitignore` 中忽略。
