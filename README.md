# Clash Verge Rev 住宅IP链式代理工具

这个项目用于把住宅 IP 代理作为链式出口注入 Clash Verge Rev，并可把桌面端当前配置导出成 Clash Meta for Android 可导入的 YAML。

## 项目结构

| 路径 | 作用 |
|------|------|
| `injection_component.example.yaml` | 公开配置示例。复制为 `injection_component.yaml` 后填入本地代理信息。 |
| `injection_component.yaml` | 本地真实配置文件，已被 `.gitignore` 忽略，不应提交。 |
| `scripts/proxy/inject.py` | 将住宅链式代理节点、代理组和规则注入 Clash Verge Rev 的 Script 增强。 |
| `scripts/proxy/export_android.py` | 读取桌面端当前生效配置，导出 Clash Meta for Android 可导入配置。 |
| `scripts/proxy/check.py` | 临时切换到链式代理组，检测出口 IP 和纯净度，完成后恢复原设置。 |
| `scripts/local/codex_fast.sh` | 本地 Codex.app fast 功能补丁脚本。会修改本机应用包、关闭部分 Electron fuses 并重新签名，仅供本地实验使用。 |
| `docs/adspower-fingerprint-sunbrowser-chrome145.md` | AdsPower / SunBrowser 指纹参数公开示例。真实值请保存在 `docs/local/`。 |
| `docs/clean_claude_code.md` | Claude Code 本地数据清理参考。 |
| `docs/plans/` | 任务计划文档目录。 |
| `PROCESS.md` | 复杂任务执行记录。 |

`docs/local/`、`injection_component.yaml`、`system_profile*.txt`、`clash-meta-android*.yaml` 均不会被 Git 跟踪。

## 工作原理

住宅 IP 代理无法从本机直连时，可以通过订阅节点作为第一跳中转，再由住宅代理作为出口：

```text
你的电脑 -> 订阅节点(中转) -> 住宅IP代理 -> 目标网站
你的电脑 <- 订阅节点(中转) <- 住宅IP代理 <- 目标网站
```

`dialer-proxy` 负责指定第一跳中转代理组。匹配规则的流量走 `Claude-住宅链式专线`，其他流量继续走原订阅规则。

## 前提条件

- 已安装 [Clash Verge Rev](https://github.com/clash-verge-rev/clash-verge-rev)
- 已有活跃远程订阅配置
- Clash Verge Rev 已启用 Script 增强
- 需要进程规则时，Clash Verge Rev 已开启 TUN 模式
- 已安装 [uv](https://docs.astral.sh/uv/)

## 初始化配置

复制示例配置：

```bash
cp injection_component.example.yaml injection_component.yaml
```

编辑 `injection_component.yaml`，只填入本地住宅代理字段：

```yaml
server: ""
port: 0
username: ""
password: ""
```

`dialer-proxy` 默认使用 `__DIALER_PROXY__` 占位符。`inject.py` 会自动读取每个订阅的主代理组名并替换，无需手动写死订阅名称。

## 脚本用法

### 注入 Clash Verge Rev

预览将要写入的 Script 内容：

```bash
uv run scripts/proxy/inject.py --dry-run
```

执行注入：

```bash
uv run scripts/proxy/inject.py
```

清除已注入内容，恢复为空脚本：

```bash
uv run scripts/proxy/inject.py --clean
```

常用参数：

| 参数 | 说明 | 默认值 |
|------|------|--------|
| `--profiles-dir` | Clash Verge profiles 目录 | `~/Library/Application Support/io.github.clash-verge-rev.clash-verge-rev/profiles` |
| `--component` | 注入配置文件路径 | `./injection_component.yaml` |
| `--dry-run` | 预览模式，不写文件 | - |
| `--clean` | 清除已注入内容 | - |

### 导出 Android 配置

导出到默认路径：

```bash
uv run scripts/proxy/export_android.py
```

只看摘要，不写文件：

```bash
uv run scripts/proxy/export_android.py --dry-run
```

指定输出路径：

```bash
uv run scripts/proxy/export_android.py --output ./clash-meta-android.yaml
```

覆盖 Claude Android 包名：

```bash
uv run scripts/proxy/export_android.py --package-name com.anthropic.claude
```

常用参数：

| 参数 | 说明 | 默认值 |
|------|------|--------|
| `--verge-dir` | Clash Verge Rev 配置目录 | `~/Library/Application Support/io.github.clash-verge-rev.clash-verge-rev` |
| `--component` | 链式代理组件定义文件 | `./injection_component.yaml` |
| `--output` | 导出文件路径 | `./clash-meta-android.yaml` |
| `--package-name` | Claude Android 包名 | `com.anthropic.claude` |
| `--dry-run` | 只打印导出摘要，不写文件 | - |

导入手机后的建议：

- 使用 Clash Meta for Android 的 VPN/TUN 模式
- 打开系统级 Always-on VPN
- 打开 Block connections without VPN
- 不要在 Android 系统里手填第三方 Private DNS
- 先在手机端手动选择主代理组的第一跳上游节点
- 确认第一跳上游节点和住宅 SOCKS5 都支持 UDP

### 检测出口 IP 纯净度

自动切换到住宅链式代理，检测完成后恢复：

```bash
uv run scripts/proxy/check.py
```

直接检测指定 IP：

```bash
uv run scripts/proxy/check.py --ip 1.2.3.4
```

指定代理组名：

```bash
uv run scripts/proxy/check.py --group Claude-住宅链式专线
```

检测源包括 `ip-api.com`、`GetIPIntel`、`proxycheck.io`、`ipinfo.io`。

### 本地 Codex.app fast 补丁

```bash
sudo scripts/local/codex_fast.sh
```

这个脚本会解包并修改 `/Applications/Codex.app`，关闭部分 Electron fuses，并进行 ad-hoc 重签名。它只适合本地实验；应用更新后可能失效，也可能导致应用无法启动。公开仓库保留它是为了记录本地工具链，不建议在不了解风险时运行。

## Clash Verge 配置建议

使用规则模式（Rule）：

- Claude 域名、AdsPower / SunBrowser 进程、Codex / Claude 进程走住宅链式代理
- 其他流量走原订阅规则

启用 TUN 模式：

- `PROCESS-NAME` 规则依赖 TUN 模式识别进程
- AdsPower 内部不需要单独配置代理，可选择“不使用代理”

## AdsPower 指纹

公开示例见 [docs/adspower-fingerprint-sunbrowser-chrome145.md](docs/adspower-fingerprint-sunbrowser-chrome145.md)。

真实指纹种子、设备名、MAC 地址等可复现身份信息请只保存在 `docs/local/`。需要生成本机系统信息时，直接运行：

```bash
system_profiler > ./system_profile.txt
```

`system_profile.txt` 已忽略，不需要提交。

## Q&A

**Q: 订阅更新后注入内容会消失吗？**  
A: 不会。工具写入 Clash Verge Rev 的 Script 增强，独立于远程订阅文件。

**Q: 可以多次运行注入脚本吗？**  
A: 可以。脚本每次重新生成 Script 文件，天然幂等。

**Q: 如何恢复原状？**  
A: 运行 `uv run scripts/proxy/inject.py --clean`，然后在 Clash Verge Rev 中刷新配置。

**Q: 修改 `injection_component.yaml` 后怎么更新？**  
A: 再次运行 `uv run scripts/proxy/inject.py`，然后刷新 Clash Verge Rev 配置。

**Q: 为什么本地配置不提交？**  
A: `injection_component.yaml` 包含住宅代理地址、端口、用户名和密码。公开仓库只提交 `injection_component.example.yaml`。

**Q: Android 导出为什么继续保留 `dialer-proxy`？**  
A: 手机端需要自行选择第一跳上游节点。导入后先在主代理组里切到目标节点，住宅链式代理会按该选择生效。

**Q: Android 为什么默认让 UDP 也走住宅链式代理？**  
A: 导出的 Android 配置会把 `com.anthropic.claude*` 的 TCP 和 UDP 都指向 `Claude-住宅链式专线`。前提是第一跳上游节点和住宅 SOCKS5 都支持 UDP。

**Q: AdsPower 需要设置代理吗？**  
A: 不需要。TUN 模式配合 `PROCESS-NAME` 规则会在系统层面拦截 AdsPower / SunBrowser 流量。

**Q: 为什么用 `dialer-proxy` 而不是 `relay`？**  
A: mihomo 新版已移除 `relay` 类型，`dialer-proxy` 是当前推荐的链式代理方式。
