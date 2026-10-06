"""
dev_productivity.py
Developer & technical productivity utilities:
- WHOIS & DNS lookup (A, AAAA, MX, TXT, Nameservers, SSL expiry)
- GitHub Repository Inspector (Stars, Forks, License, Commits, Issues)
- Network Latency & Speedtest
"""

import re
import ssl
import time
import socket
import datetime
import requests
import config

try:
    from google import genai
except ImportError:
    genai = None


def _get_client():
    if genai and config.GEMINI_API_KEY and config.GEMINI_API_KEY != "PASTE_YOUR_GEMINI_API_KEY_HERE":
        return genai.Client(api_key=config.GEMINI_API_KEY)
    return None


def dns_whois_lookup(domain: str) -> str:
    """
    Performs DNS resolution (A, AAAA, MX, NS), SSL certificate inspection,
    and domain intelligence for any domain name.
    """
    clean_domain = domain.strip().lower()
    clean_domain = re.sub(r'^(?:https?:\/\/)?(?:www\.)?', '', clean_domain)
    clean_domain = clean_domain.split('/')[0]

    output_lines = [f"🌐 DOMAIN & DNS INTELLIGENCE: {clean_domain}", "─" * 60]

    # 1. IP Resolution
    try:
        ip_addr = socket.gethostbyname(clean_domain)
        output_lines.append(f"📌 Primary IPv4: {ip_addr}")
    except Exception:
        ip_addr = "Could not resolve"
        output_lines.append(f"📌 Primary IPv4: {ip_addr}")

    # 2. DNS-over-HTTPS via Cloudflare 1.1.1.1 API
    dns_records = {}
    for rtype in ["A", "MX", "NS", "TXT"]:
        try:
            r = requests.get(
                f"https://cloudflare-dns.com/dns-query?name={clean_domain}&type={rtype}",
                headers={"Accept": "application/dns-json"},
                timeout=4
            )
            if r.status_code == 200:
                answers = r.json().get("Answer", [])
                dns_records[rtype] = [a.get("data", "") for a in answers if a.get("data")]
        except Exception:
            pass

    if dns_records:
        output_lines.append("\n📋 DNS RECORDS:")
        if dns_records.get("A"):
            output_lines.append(f" • A Records: {', '.join(dns_records['A'][:3])}")
        if dns_records.get("MX"):
            output_lines.append(f" • Mail Servers (MX): {', '.join(dns_records['MX'][:2])}")
        if dns_records.get("NS"):
            output_lines.append(f" • Name Servers (NS): {', '.join(dns_records['NS'][:2])}")
        if dns_records.get("TXT"):
            txts = [t[:40] + '...' if len(t) > 40 else t for t in dns_records['TXT'][:2]]
            output_lines.append(f" • TXT / Verification: {', '.join(txts)}")

    # 3. SSL Certificate Expiry Check
    try:
        ctx = ssl.create_default_context()
        with socket.create_connection((clean_domain, 443), timeout=4) as sock:
            with ctx.wrap_socket(sock, server_hostname=clean_domain) as ssock:
                cert = ssock.getpeercert()
                expiry_str = cert.get('notAfter')
                if expiry_str:
                    exp_date = datetime.datetime.strptime(expiry_str, '%b %d %H:%M:%S %Y %Z')
                    days_left = (exp_date - datetime.datetime.utcnow()).days
                    output_lines.append(f"\n🔒 SSL CERTIFICATE:")
                    output_lines.append(f" • Valid Until: {exp_date.strftime('%Y-%m-%d')} ({days_left} days remaining)")
                    issuer = dict(x[0] for x in cert.get('issuer', ()))
                    org = issuer.get('organizationName', 'Trusted CA')
                    output_lines.append(f" • Issuer: {org}")
    except Exception:
        output_lines.append("\n🔒 SSL Certificate: Could not verify port 443.")

    output_lines.append("─" * 60)
    return "\n".join(output_lines)


def git_inspect_repo(repo_input: str) -> str:
    """
    Inspects any GitHub repository via GitHub REST API.
    Supports formats: 'owner/repo', 'https://github.com/owner/repo', or search query.
    """
    clean = repo_input.strip()
    clean = re.sub(r'^(?:https?:\/\/)?(?:www\.)?github\.com\/', '', clean)
    clean = clean.rstrip('/')

    parts = clean.split('/')
    if len(parts) >= 2:
        owner, repo = parts[0], parts[1]
    else:
        # Search GitHub API
        try:
            sr = requests.get(f"https://api.github.com/search/repositories?q={clean}&sort=stars&order=desc", timeout=5)
            if sr.status_code == 200 and sr.json().get("items"):
                top_item = sr.json()["items"][0]
                owner = top_item["owner"]["login"]
                repo = top_item["name"]
            else:
                return f"⚠️ Could not find GitHub repository matching '{repo_input}'."
        except Exception as e:
            return f"⚠️ GitHub search failed: {e}"

    api_url = f"https://api.github.com/repos/{owner}/{repo}"
    try:
        res = requests.get(api_url, timeout=6)
        if res.status_code != 200:
            return f"⚠️ GitHub repository '{owner}/{repo}' not found or rate-limited (HTTP {res.status_code})."

        data = res.json()
        name = data.get("full_name", f"{owner}/{repo}")
        description = data.get("description", "No description provided.")
        stars = data.get("stargazers_count", 0)
        forks = data.get("forks_count", 0)
        open_issues = data.get("open_issues_count", 0)
        language = data.get("language", "Not specified")
        license_name = data.get("license", {}).get("name", "No license specified") if data.get("license") else "No license"
        updated_at = data.get("updated_at", "")[:10]
        html_url = data.get("html_url", f"https://github.com/{owner}/{repo}")

        # Fetch recent commits
        commit_lines = []
        try:
            cr = requests.get(f"{api_url}/commits?per_page=3", timeout=4)
            if cr.status_code == 200:
                for c in cr.json():
                    msg = c.get("commit", {}).get("message", "").split("\n")[0][:60]
                    author = c.get("commit", {}).get("author", {}).get("name", "Author")
                    commit_lines.append(f"  • {msg} ({author})")
        except Exception:
            pass

        commits_str = "\n".join(commit_lines) if commit_lines else "  (No commit details available)"

        return f"""🐙 GITHUB REPOSITORY: {name}
────────────────────────────────────────────────────────────
📝 Description: {description}
🌐 URL: {html_url}

⭐ Stars: {stars:,}    🍴 Forks: {forks:,}    ⚠️ Open Issues: {open_issues:,}
💻 Primary Language: {language}
📜 License: {license_name}
📅 Last Activity: {updated_at}

🔨 RECENT COMMITS:
{commits_str}
────────────────────────────────────────────────────────────"""
    except Exception as e:
        return f"Error inspecting repository: {e}"


def run_speedtest() -> str:
    """
    Measures real-time network latency (ping) and download bandwidth without external heavy binaries.
    """
    output = ["🚀 NETWORK & SPEED DIAGNOSTIC", "─" * 60]

    # 1. Latency Ping test across fast DNS servers
    hosts = [("Cloudflare (1.1.1.1)", "1.1.1.1", 53), ("Google (8.8.8.8)", "8.8.8.8", 53)]
    latencies = []
    for label, host, port in hosts:
        try:
            t0 = time.time()
            s = socket.create_connection((host, port), timeout=3)
            s.close()
            lat_ms = (time.time() - t0) * 1000
            latencies.append(lat_ms)
            output.append(f"📡 Ping to {label}: {lat_ms:.1f} ms")
        except Exception:
            output.append(f"📡 Ping to {label}: Timeout")

    avg_ping = sum(latencies) / len(latencies) if latencies else 0

    # 2. Download throughput benchmark (Cloudflare 10MB speed file)
    output.append("\n⏳ Testing download bandwidth throughput...")
    try:
        t_start = time.time()
        # Download 5MB chunk
        test_url = "https://speed.cloudflare.com/__down?bytes=5000000"
        res = requests.get(test_url, timeout=10)
        t_end = time.time()
        duration = t_end - t_start
        data_size_mb = len(res.content) / (1024 * 1024)
        mbps = (data_size_mb * 8) / duration

        output.append(f"⚡ Download Speed: {mbps:.2f} Mbps")
        output.append(f"⏱️ Transferred: {data_size_mb:.1f} MB in {duration:.2f}s")
    except Exception as e:
        output.append(f"⚠️ Bandwidth test error: {e}")

    output.append("─" * 60)
    return "\n".join(output)
