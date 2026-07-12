"""Capture Kubernetes pod and service state as terminal-style screenshots."""
import os, subprocess
from playwright.sync_api import sync_playwright

SCREENSHOTS_DIR = os.path.join(os.path.dirname(__file__), "screenshots")

def run_cmd(cmd):
    return subprocess.check_output(cmd, shell=True, text=True, stderr=subprocess.STDOUT)

def html_terminal(title, content):
    lines = content.strip().split("\n")
    rows = ""
    for i, line in enumerate(lines):
        # first line is the header row
        if i == 0:
            rows += f'<div class="header-row">{line}</div>'
        else:
            rows += f'<div class="row">{line}</div>'
    return f"""<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<style>
  * {{ margin:0; padding:0; box-sizing:border-box; }}
  body {{ background:#1e1e2e; font-family:'Courier New',monospace; padding:20px; }}
  .window {{ background:#1e1e2e; border-radius:10px; overflow:hidden;
             box-shadow:0 4px 32px rgba(0,0,0,.6); max-width:900px; margin:auto; }}
  .titlebar {{ background:#313244; display:flex; align-items:center;
               padding:10px 14px; gap:8px; }}
  .btn {{ width:12px; height:12px; border-radius:50%; }}
  .red   {{ background:#ff5f57; }}
  .yellow{{ background:#febc2e; }}
  .green {{ background:#28c840; }}
  .title {{ color:#cdd6f4; font-size:13px; margin-left:8px; }}
  .body  {{ padding:16px 20px; }}
  .cmd   {{ color:#89b4fa; margin-bottom:10px; font-size:13px; }}
  .cmd::before {{ content:"$ "; color:#a6e3a1; }}
  .header-row {{ color:#cba6f7; font-weight:bold; font-size:12px;
                 border-bottom:1px solid #45475a; padding-bottom:4px;
                 margin-bottom:4px; white-space:pre; }}
  .row   {{ color:#cdd6f4; font-size:12px; white-space:pre; line-height:1.6; }}
  .row:nth-child(even) {{ color:#a6adc8; }}
</style>
</head>
<body>
<div class="window">
  <div class="titlebar">
    <div class="btn red"></div>
    <div class="btn yellow"></div>
    <div class="btn green"></div>
    <span class="title">{title}</span>
  </div>
  <div class="body">
    <div class="cmd">{title}</div>
    {rows}
  </div>
</div>
</body>
</html>"""

def take_terminal_screenshot(title, content, filename):
    html = html_terminal(title, content)
    html_path = f"/tmp/{filename}.html"
    with open(html_path, "w") as f:
        f.write(html)
    out_path = os.path.join(SCREENSHOTS_DIR, filename)
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page(viewport={"width": 960, "height": 600})
        page.goto(f"file://{html_path}")
        page.wait_for_timeout(500)
        page.screenshot(path=out_path, full_page=False)
        browser.close()
    size = os.path.getsize(out_path) // 1024
    print(f"  Saved: {out_path}  ({size} KB)")

def main():
    print("[K8s 1/3] kubectl get pods...")
    pods = run_cmd("kubectl get pods -o wide --context kind-heart-disease")
    take_terminal_screenshot(
        "kubectl get pods -o wide --context kind-heart-disease",
        pods, "k8s_pods.png"
    )

    print("[K8s 2/3] kubectl get services...")
    svcs = run_cmd("kubectl get services --context kind-heart-disease")
    take_terminal_screenshot(
        "kubectl get services --context kind-heart-disease",
        svcs, "k8s_service.png"
    )

    print("[K8s 3/3] kubectl get all...")
    all_res = run_cmd(
        "kubectl get all --context kind-heart-disease"
    )
    take_terminal_screenshot(
        "kubectl get all --context kind-heart-disease",
        all_res, "k8s_all_resources.png"
    )

    print("\nK8s screenshots done.")

if __name__ == "__main__":
    main()
