"""Retake the two screenshots that need fixing: MLflow run detail and Prometheus."""
import os
from playwright.sync_api import sync_playwright

SCREENSHOTS_DIR = os.path.join(os.path.dirname(__file__), "screenshots")

def save(page, name, wait_ms=1500):
    path = os.path.join(SCREENSHOTS_DIR, name)
    page.wait_for_timeout(wait_ms)
    page.screenshot(path=path, full_page=False)
    size = os.path.getsize(path) // 1024
    print(f"  Saved: {name}  ({size} KB)")


def retake_mlflow_runs(pg):
    """Navigate: Experiments sidebar → heart_disease_classification → Training runs → first run."""
    pg.goto("http://127.0.0.1:5000/", timeout=15000)
    pg.wait_for_timeout(1500)

    # Click "Experiments" in left sidebar (exact match to avoid ambiguity)
    pg.get_by_role("link", name="Experiments", exact=True).first.click()
    pg.wait_for_timeout(1500)

    # Click the experiment row
    pg.get_by_text("heart_disease_classification").first.click()
    pg.wait_for_timeout(2000)

    # Should now be on the experiment page with runs listed — take screenshot here
    save(pg, "mlflow_experiments_detail.png", wait_ms=1500)

    # Click "Training runs" tab if visible
    try:
        pg.get_by_role("tab", name="Training runs").click()
        pg.wait_for_timeout(1500)
    except Exception:
        pass

    # Click the first run row (the table body rows)
    try:
        rows = pg.locator("table tbody tr")
        rows.first.click()
        pg.wait_for_timeout(3000)
        save(pg, "mlflow_run_detail.png", wait_ms=2000)
    except Exception as e:
        print(f"  Could not click run row: {e}")
        save(pg, "mlflow_run_detail.png", wait_ms=1000)


def retake_prometheus(pg):
    """Load Prometheus graph page, type query, click Execute, wait for results."""
    pg.goto("http://localhost:9090/graph", timeout=15000)
    pg.wait_for_timeout(2000)

    # The new Prometheus UI uses a CodeMirror input — find it
    try:
        # Try the modern textarea/input approach
        editor = pg.locator(".cm-content").first
        editor.click()
        pg.wait_for_timeout(300)
        editor.fill("api_requests_total")
    except Exception:
        try:
            inp = pg.locator("input[type='text']").first
            inp.click()
            inp.fill("api_requests_total")
        except Exception:
            pg.keyboard.type("api_requests_total")

    pg.wait_for_timeout(500)
    # Click Execute button
    pg.get_by_role("button", name="Execute").click()
    pg.wait_for_timeout(3000)

    # Switch to Table view to show the actual values clearly
    try:
        pg.get_by_role("tab", name="Table").click()
        pg.wait_for_timeout(1500)
    except Exception:
        pass

    save(pg, "prometheus_metrics.png", wait_ms=1000)

    # Also take targets screenshot
    pg.goto("http://localhost:9090/targets", timeout=10000)
    pg.wait_for_timeout(2000)
    save(pg, "prometheus_targets.png", wait_ms=500)


def retake_predict_response(pg):
    """Show the actual predict response body in Swagger UI."""
    pg.goto("http://localhost:8000/docs", timeout=15000)
    pg.wait_for_selector(".swagger-ui", timeout=8000)
    pg.wait_for_timeout(1000)

    # Expand the POST /predict section
    pg.locator("text=/predict").first.click()
    pg.wait_for_timeout(700)

    pg.locator("text=Try it out").first.click()
    pg.wait_for_timeout(500)

    # Click Execute
    pg.locator("button.btn.execute").click()
    pg.wait_for_timeout(3000)

    # Scroll to show the response
    pg.evaluate("window.scrollBy(0, 400)")
    pg.wait_for_timeout(500)
    save(pg, "docker_predict.png", wait_ms=1000)


def main():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        ctx = browser.new_context(viewport={"width": 1440, "height": 900})

        print("[1/3] MLflow run detail...")
        pg = ctx.new_page()
        retake_mlflow_runs(pg)
        pg.close()

        print("[2/3] Prometheus with query results...")
        pg = ctx.new_page()
        retake_prometheus(pg)
        pg.close()

        print("[3/3] Swagger /predict with response...")
        pg = ctx.new_page()
        retake_predict_response(pg)
        pg.close()

        browser.close()

    print("\nDone. Retaken screenshots:")
    for f in ["mlflow_experiments_detail.png", "mlflow_run_detail.png",
              "prometheus_metrics.png", "prometheus_targets.png", "docker_predict.png"]:
        p = os.path.join(SCREENSHOTS_DIR, f)
        if os.path.exists(p):
            print(f"  {f}  {os.path.getsize(p)//1024} KB")


if __name__ == "__main__":
    main()
