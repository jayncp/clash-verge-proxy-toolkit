# /// script
# requires-python = ">=3.10"
# dependencies = [
#     "requests>=2.31",
# ]
# ///
"""Clash Verge Rev 住宅IP链式代理检测工具

通过 Clash mihomo 的 unix socket API 临时切换到住宅链式代理组，
获取实际出口IP并检测纯净度，检测完毕后自动恢复原设置。
"""

import argparse
import http.client
import json
import socket
import sys
import time
from urllib.parse import quote

import requests

TIMEOUT = 10
CLASH_SOCKET = "/tmp/verge/verge-mihomo.sock"


def clash_socket_override(path: str) -> None:
    global CLASH_SOCKET
    CLASH_SOCKET = path
CLASH_MIXED_PORT = 7897
PROXY_GROUP_NAME = "Claude-住宅链式专线"

IP_SERVICES = [
    ("ip-api.com", "http://ip-api.com/json/?fields=query", lambda r: r.json()["query"]),
    ("httpbin.org", "https://httpbin.org/ip", lambda r: r.json()["origin"]),
    ("ip.sb", "https://api.ip.sb/ip", lambda r: r.text.strip()),
]


# ── Clash API (unix socket) ─────────────────────

class UnixHTTPConnection(http.client.HTTPConnection):
    """通过 unix socket 连接 mihomo API。"""
    def __init__(self, socket_path: str):
        super().__init__("localhost")
        self.socket_path = socket_path

    def connect(self):
        self.sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        self.sock.connect(self.socket_path)


def clash_api(method: str, path: str, body: dict | None = None) -> dict | None:
    conn = UnixHTTPConnection(CLASH_SOCKET)
    headers = {"Content-Type": "application/json"}
    data = json.dumps(body).encode() if body else None
    encoded_path = quote(path, safe="/:?&=")
    conn.request(method, encoded_path, body=data, headers=headers)
    resp = conn.getresponse()
    text = resp.read().decode()
    conn.close()
    if resp.status == 204:
        return {}
    if text:
        return json.loads(text)
    return {}


def get_clash_mode() -> str:
    data = clash_api("GET", "/configs") or {}
    return data.get("mode", "rule")


def set_clash_mode(mode: str) -> None:
    clash_api("PATCH", "/configs", {"mode": mode})


def get_global_proxy() -> str:
    data = clash_api("GET", "/proxies/GLOBAL") or {}
    return data.get("now", "")


def set_global_proxy(name: str) -> None:
    clash_api("PUT", "/proxies/GLOBAL", {"name": name})


def check_proxy_exists(group_name: str) -> bool:
    data = clash_api("GET", f"/proxies/{group_name}")
    return data is not None and "name" in (data or {})


# ── IP 检测 ──────────────────────────────────────

def get_session_with_clash() -> requests.Session:
    s = requests.Session()
    proxy_url = f"http://127.0.0.1:{CLASH_MIXED_PORT}"
    s.proxies = {"http": proxy_url, "https": proxy_url}
    s.headers["User-Agent"] = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"
    return s


def get_current_ip(session: requests.Session) -> str | None:
    for name, url, extract in IP_SERVICES:
        try:
            print(f"  尝试 {name} ({url})...")
            r = session.get(url, timeout=TIMEOUT)
            r.raise_for_status()
            ip = extract(r)
            if ip:
                return ip
        except Exception as e:
            print(f"  {name} 失败: {e}")
            continue
    return None


def check_ip_api(session: requests.Session, ip: str) -> dict | None:
    try:
        r = session.get(
            f"http://ip-api.com/json/{ip}?fields=status,country,regionName,city,isp,org,as,hosting,proxy",
            timeout=TIMEOUT,
        )
        data = r.json()
        if data.get("status") == "success":
            return data
    except Exception:
        pass
    return None


def check_getipintel(session: requests.Session, ip: str) -> dict | None:
    try:
        r = session.get(
            "http://check.getipintel.net/check.php",
            params={"ip": ip, "contact": "ipcheck@protonmail.com", "format": "json", "oflags": "b"},
            timeout=TIMEOUT,
        )
        data = r.json()
        if data.get("status") == "success":
            return data
    except Exception:
        pass
    return None


def check_proxycheck(session: requests.Session, ip: str) -> dict | None:
    try:
        r = session.get(
            f"https://proxycheck.io/v2/{ip}?vpn=1&asn=1&risk=1",
            timeout=TIMEOUT,
        )
        data = r.json()
        if data.get("status") == "ok" and ip in data:
            return data[ip]
    except Exception:
        pass
    return None


def check_ipinfo(session: requests.Session, ip: str) -> dict | None:
    try:
        r = session.get(f"https://ipinfo.io/{ip}/json", timeout=TIMEOUT)
        if r.status_code == 200:
            return r.json()
    except Exception:
        pass
    return None


# ── 输出格式 ─────────────────────────────────────

def print_header(title: str) -> None:
    print(f"\n{'='*50}")
    print(f"  {title}")
    print(f"{'='*50}")


def print_section(title: str) -> None:
    print(f"\n--- {title} ---")


def label_value(label: str, value, width: int = 18) -> None:
    print(f"  {label:<{width}} {value}")


def risk_bar(score: float, max_score: float = 1.0) -> str:
    normalized = score / max_score
    filled = int(normalized * 10)
    bar = "█" * filled + "░" * (10 - filled)
    if normalized <= 0.3:
        level = "低风险"
    elif normalized <= 0.6:
        level = "中风险"
    else:
        level = "高风险"
    return f"[{bar}] {score:.2f}/{max_score:.0f} ({level})"


# ── 纯净度检测 ───────────────────────────────────

def run_purity_checks(session: requests.Session, ip: str) -> None:
    results = {}
    checks_passed = 0
    checks_total = 0

    # ip-api.com
    print_section("ip-api.com (地理位置 + 托管检测)")
    data = check_ip_api(session, ip)
    if data:
        results["ip-api"] = data
        label_value("国家", data.get("country", "未知"))
        label_value("地区", f"{data.get('regionName', '')} {data.get('city', '')}")
        label_value("ISP", data.get("isp", "未知"))
        label_value("组织", data.get("org", "未知"))
        label_value("AS", data.get("as", "未知"))
        hosting = data.get("hosting", False)
        proxy_detected = data.get("proxy", False)
        label_value("数据中心IP", "是 (非住宅)" if hosting else "否 (住宅)")
        label_value("代理检测", "检测到代理" if proxy_detected else "未检测到代理")
        checks_total += 1
        if not hosting:
            checks_passed += 1
    else:
        print("  检测失败")

    time.sleep(0.5)

    # GetIPIntel
    print_section("GetIPIntel (代理/VPN 置信度评分)")
    data = check_getipintel(session, ip)
    if data:
        results["getipintel"] = data
        score = float(data.get("result", 0))
        label_value("代理置信度", risk_bar(score, 1.0))
        bad_ip = data.get("BadIP")
        if bad_ip is not None:
            label_value("恶意IP标记", "是" if int(bad_ip) else "否")
        checks_total += 1
        if score < 0.5:
            checks_passed += 1
    else:
        print("  检测失败")

    time.sleep(0.5)

    # proxycheck.io
    print_section("proxycheck.io (代理类型识别)")
    data = check_proxycheck(session, ip)
    if data:
        results["proxycheck"] = data
        label_value("代理检测", data.get("proxy", "未知"))
        label_value("类型", data.get("type", "未知"))
        label_value("提供商", data.get("provider", "无"))
        risk = data.get("risk")
        if risk is not None:
            label_value("风险评分", risk_bar(float(risk), 100))
        label_value("ASN", data.get("asn", "未知"))
        label_value("运营商", data.get("organisation", "未知"))
        checks_total += 1
        if data.get("proxy", "no") == "no":
            checks_passed += 1
    else:
        print("  检测失败")

    time.sleep(0.5)

    # ipinfo.io
    print_section("ipinfo.io (IP 信息)")
    data = check_ipinfo(session, ip)
    if data:
        results["ipinfo"] = data
        label_value("主机名", data.get("hostname", "无"))
        label_value("组织", data.get("org", "未知"))
        label_value("位置", f"{data.get('city', '')} {data.get('region', '')} {data.get('country', '')}")
        privacy = data.get("privacy", {})
        if privacy:
            label_value("VPN", "是" if privacy.get("vpn") else "否")
            label_value("代理", "是" if privacy.get("proxy") else "否")
            label_value("Tor", "是" if privacy.get("tor") else "否")
            label_value("中继", "是" if privacy.get("relay") else "否")
            label_value("托管", "是" if privacy.get("hosting") else "否")
            checks_total += 1
            if not privacy.get("hosting") and not privacy.get("proxy") and not privacy.get("vpn"):
                checks_passed += 1
    else:
        print("  检测失败 (可能需要 API token)")

    # 综合报告
    print_header("综合检测报告")
    label_value("出口IP", ip)
    if results.get("ip-api"):
        d = results["ip-api"]
        label_value("位置", f"{d.get('country', '')} {d.get('city', '')}")
        label_value("ISP", d.get("isp", "未知"))
    if checks_total > 0:
        label_value("纯净度评分", f"{checks_passed}/{checks_total} 项通过")

    ip_api_data = results.get("ip-api", {})
    hosting = ip_api_data.get("hosting", None)
    getipintel_data = results.get("getipintel", {})
    intel_score = float(getipintel_data.get("result", -1))
    proxycheck_data = results.get("proxycheck", {})
    pc_proxy = proxycheck_data.get("proxy", "unknown")

    print()
    if hosting is False and intel_score < 0.5 and pc_proxy == "no":
        print("  [结论] 住宅IP - 纯净度高")
        print("  该IP被识别为住宅IP，各检测源均未标记为代理/VPN/数据中心。")
    elif hosting is False and (intel_score < 0.9 or pc_proxy == "no"):
        print("  [结论] 疑似住宅IP - 纯净度中等")
        print("  该IP可能为住宅IP，但部分检测源有标记，建议进一步验证。")
    elif hosting is True:
        print("  [结论] 数据中心IP - 非住宅")
        print("  该IP被识别为数据中心/托管IP，不是住宅IP。")
    else:
        print("  [结论] 检测数据不足，无法判定")
        print("  部分检测源未返回结果，请稍后重试。")
    print()


# ── 主流程 ───────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="住宅IP链式代理纯净度检测")
    parser.add_argument(
        "--ip",
        type=str,
        default=None,
        help="直接检测指定IP的纯净度 (跳过链式代理检测)",
    )
    parser.add_argument(
        "--group",
        type=str,
        default=PROXY_GROUP_NAME,
        help=f"要检测的 Clash 代理组名 (默认: {PROXY_GROUP_NAME})",
    )
    parser.add_argument(
        "--socket",
        type=str,
        default=CLASH_SOCKET,
        help=f"mihomo unix socket 路径 (默认: {CLASH_SOCKET})",
    )
    args = parser.parse_args()

    clash_socket_override(args.socket)

    # 直接检测指定 IP
    if args.ip:
        print_header("住宅IP纯净度检测")
        print(f"\n  检测指定IP: {args.ip}")
        session = requests.Session()
        session.headers["User-Agent"] = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"
        run_purity_checks(session, args.ip)
        return

    # 通过 Clash API 检测链式代理出口IP
    print_header("链式代理出口IP检测")

    # 1. 检查代理组是否存在
    print(f"\n  检测代理组: {args.group}")
    if not check_proxy_exists(args.group):
        print(f"\n  错误: 代理组 '{args.group}' 不存在", file=sys.stderr)
        print("  请先运行 `uv run scripts/proxy/inject.py` 注入配置并刷新 Clash Verge", file=sys.stderr)
        sys.exit(1)
    print("  代理组已找到")

    # 2. 保存当前状态
    original_mode = get_clash_mode()
    original_global = get_global_proxy()
    print(f"  当前模式: {original_mode}, 全局代理: {original_global}")

    # 3. 临时切换到 Global 模式 + 选中住宅代理组
    print(f"\n  临时切换: Global 模式 -> {args.group}")
    set_clash_mode("global")
    set_global_proxy(args.group)
    time.sleep(1)  # 等待切换生效

    session = get_session_with_clash()

    try:
        # 4. 获取出口 IP
        ip = get_current_ip(session)
        if not ip:
            print("\n  错误: 无法获取出口IP，链式代理可能未生效", file=sys.stderr)
            sys.exit(1)

        print(f"  链式代理出口IP: {ip}")

        # 5. 运行纯净度检测
        run_purity_checks(session, ip)

    finally:
        # 6. 恢复原设置
        print("  恢复 Clash 设置...")
        set_global_proxy(original_global)
        set_clash_mode(original_mode)
        print(f"  已恢复: {original_mode} 模式, 全局代理: {original_global}")


if __name__ == "__main__":
    main()
