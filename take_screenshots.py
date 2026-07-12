"""
Capture screenshots of all running services using Playwright headless browser.
Run: python3 take_screenshots.py
"""
import os
import time
from playwright.sync_api import sync_playwright

SCREENSHOTS_DIR = os.path.join(os.path.dirname(__file__), "screenshots")
os.makedirs(SCREENSHOTS_DIR, exist_ok=True)

VIEWPORT = {"width": 1440, "height": 900}


def save(page, name, wait_ms=1500):
    path = os.path.join(SCREENSHOTS_DIR, name)
    page.wait_for_timeout(wait_ms)
    page.screenshot(path=path, full_page=False)
    print(f"  Saved: {path}")
    return path


def setup_grafana(api_url="http://localhost:3000"):
    """Configure Grafana data source and create a dashboard via API."""
    import urllib.request, json, base64

    creds = base64.b64encode(b"admin:admin").decode()
    headers = {
        "Authorization": f"Basic {creds}",
        "Content-Type": "application/json",
    }

    # Add Prometheus datasource
    ds_payload = json.dumps({
        "name": "Prometheus",
        "type": "prometheus",
        "url": "http://prometheus:9090",
        "access": "proxy",
        "isDefault": True,
    }).encode()
    try:
        req = urllib.request.Request(
            f"{api_url}/api/datasources",
            data=ds_payload,
            headers=headers,
            method="POST",
        )
        urllib.request.urlopen(req)
        print("  Grafana: Prometheus datasource added")
    except Exception as e:
        print(f"  Grafana datasource (may already exist): {e}")

    # Import a simple dashboard
    dashboard = {
        "dashboard": {
            "title": "Heart Disease API Monitoring",
            "panels": [
                {
                    "id": 1, "type": "stat", "title": "Total API Requests",
                    "gridPos": {"x": 0, "y": 0, "w": 8, "h": 4},
                    "targets": [{
                        "expr": "sum(api_requests_total)",
                        "datasource": {"type": "prometheus", "uid": "prometheus"},
                    }],
                },
                {
                    "id": 2, "type": "stat", "title": "Total Predictions",
                    "gridPos": {"x": 8, "y": 0, "w": 8, "h": 4},
                    "targets": [{
                        "expr": "sum(predictions_total)",
                        "datasource": {"type": "prometheus", "uid": "prometheus"},
                    }],
                },
                {
                    "id": 3, "type": "timeseries",
                    "title": "Request Rate (req/s)",
                    "gridPos": {"x": 0, "y": 4, "w": 16, "h": 8},
                    "targets": [{
                        "expr": 'rate(api_requests_total[1m])',
                        "legendFormat": "{{endpoint}} {{status}}",
                        "datasource": {"type": "prometheus", "uid": "prometheus"},
                    }],
                },
            ],
            "schemaVersion": 36,
            "version": 1,
            "refresh": "10s",
        },
        "overwrite": True,
        "folderId": 0,
    }
    try:
        db_payload = json.dumps(dashboard).encode()
        req = urllib.request.Request(
            f"{api_url}/api/dashboards/db",
            data=db_payload,
            headers=headers,
            method="POST",
        )
        resp = urllib.request.urlopen(req)
        result = json.loads(resp.read())
        print(f"  Grafana: Dashboard created — uid={result.get('uid')}")
        return result.get("url", "/")
    except Exception as e:
        print(f"  Grafana dashboard error: {e}")
        return "/"


def run():
    dashboard_url = setup_grafana()

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        ctx = browser.new_context(viewport=VIEWPORT)

        # ── 1. MLflow Experiments List ───────────────────────────────────────────
        print("\n[1/6] MLflow experiments list...")
        pg = ctx.new_page()
        pg.goto("http://127.0.0.1:5000", timeout=15000)
        pg.wait_for_selector("text=heart_disease_classification", timeout=10000)
        save(pg, "mlflow_experiments.png", wait_ms=1000)
        pg.close()

        # ── 2. MLflow Run Detail ─────────────────────────────────────────────────
        print("[2/6] MLflow run detail...")
        pg = ctx.new_page()
        pg.goto("http://127.0.0.1:5000", timeout=15000)
        pg.wait_for_selector("text=heart_disease_classification", timeout=8000)
        pg.click("text=heart_disease_classification")
        pg.wait_for_timeout(2000)
        # Click on first run
        try:
            pg.locator("table tbody tr").first.click()
            pg.wait_for_timeout(3000)
        except Exception:
            pass
        save(pg, "mlflow_run_detail.png", wait_ms=1000)
        pg.close()

        # ── 3. Docker container — Swagger UI ─────────────────────────────────────
        print("[3/6] Docker container Swagger UI...")
        pg = ctx.new_page()
        pg.goto("http://localhost:8000/docs", timeout=15000)
        pg.wait_for_selector("text=Heart Disease Prediction API", timeout=8000)
        save(pg, "docker_build.png", wait_ms=1500)

        # Expand and try /predict
        try:
            pg.locator("text=/predict").first.click()
            pg.wait_for_timeout(800)
            pg.locator("text=Try it out").first.click()
            pg.wait_for_timeout(500)
            pg.locator("button:has-text('Execute')").first.click()
            pg.wait_for_timeout(2000)
        except Exception:
            pass
        save(pg, "docker_predict.png", wait_ms=1000)
        pg.close()

        # ── 4. Prometheus Metrics ─────────────────────────────────────────────────
        print("[4/6] Prometheus metrics...")
        pg = ctx.new_page()
        pg.goto("http://localhost:9090/graph", timeout=15000)
        pg.wait_for_selector("input[placeholder]", timeout=8000)
        # Type a query
        inp = pg.locator("input[placeholder]").first
        inp.fill("api_requests_total")
        pg.keyboard.press("Enter")
        pg.wait_for_timeout(2000)
        save(pg, "prometheus_metrics.png", wait_ms=1000)

        # Also get the targets page
        pg.goto("http://localhost:9090/targets", timeout=10000)
        pg.wait_for_timeout(2000)
        save(pg, "prometheus_targets.png", wait_ms=500)
        pg.close()

        # ── 5. Grafana Dashboard ──────────────────────────────────────────────────
        print("[5/6] Grafana dashboard...")
        pg = ctx.new_page()
        pg.goto("http://localhost:3000/login", timeout=15000)
        pg.wait_for_selector("input[name='user']", timeout=8000)
        pg.fill("input[name='user']", "admin")
        pg.fill("input[name='password']", "admin")
        pg.click("button[type='submit']")
        pg.wait_for_timeout(3000)

        # Skip the change-password prompt if shown
        try:
            pg.click("text=Skip", timeout=3000)
        except Exception:
            pass

        # Navigate to the dashboard
        if dashboard_url and dashboard_url != "/":
            pg.goto(f"http://localhost:3000{dashboard_url}", timeout=15000)
        else:
            pg.goto("http://localhost:3000/dashboards", timeout=15000)
        pg.wait_for_timeout(4000)
        save(pg, "grafana_dashboard.png", wait_ms=2000)
        pg.close()

        # ── 6. API Health + Predict response ─────────────────────────────────────
        print("[6/6] API health and predict endpoints...")
        pg = ctx.new_page()
        pg.goto("http://localhost:8000/health", timeout=10000)
        pg.wait_for_timeout(1000)
        save(pg, "api_health.png", wait_ms=500)

        pg.goto("http://localhost:8000/metrics", timeout=10000)
        pg.wait_for_timeout(1000)
        save(pg, "api_metrics_raw.png", wait_ms=500)
        pg.close()

        browser.close()

    print("\nAll screenshots saved to:", SCREENSHOTS_DIR)
    import os
    files = sorted(os.listdir(SCREENSHOTS_DIR))
    for f in files:
        size = os.path.getsize(os.path.join(SCREENSHOTS_DIR, f))
        print(f"  {f:40s}  {size//1024} KB")


if __name__ == "__main__":
    run()
