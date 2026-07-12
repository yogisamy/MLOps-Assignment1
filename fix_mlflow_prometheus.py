"""Fix MLflow run detail and Prometheus screenshots using direct URLs."""
import os
from playwright.sync_api import sync_playwright

SCREENSHOTS_DIR = os.path.join(os.path.dirname(__file__), "screenshots")
EXPERIMENT_ID = "1"
RUN_ID = "af9e04d2"  # Random Forest run (best model)

def save(page, name, wait_ms=1500):
    path = os.path.join(SCREENSHOTS_DIR, name)
    page.wait_for_timeout(wait_ms)
    page.screenshot(path=path, full_page=False)
    print(f"  {name}  {os.path.getsize(path)//1024} KB")


def main():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        ctx = browser.new_context(viewport={"width": 1440, "height": 900})

        # ── MLflow: Training runs list ─────────────────────────────────────────
        print("[1] MLflow — training runs list...")
        pg = ctx.new_page()
        # Direct URL to the experiment's training runs in MLflow 3.x
        pg.goto(f"http://127.0.0.1:5000/#/experiments/{EXPERIMENT_ID}", timeout=15000)
        pg.wait_for_timeout(2000)
        # Dismiss any popup
        try:
            pg.locator("text=Got it").click(timeout=2000)
            pg.wait_for_timeout(500)
        except Exception:
            pass
        # Click "Training runs" in left sidebar
        try:
            pg.locator("text=Training runs").click(timeout=3000)
            pg.wait_for_timeout(2000)
        except Exception:
            pass
        save(pg, "mlflow_experiments.png", wait_ms=1500)
        pg.close()

        # ── MLflow: Individual run detail ──────────────────────────────────────
        print("[2] MLflow — run detail (Random Forest)...")
        pg = ctx.new_page()
        pg.goto(f"http://127.0.0.1:5000/#/experiments/{EXPERIMENT_ID}/runs/{RUN_ID}", timeout=15000)
        pg.wait_for_timeout(3000)
        try:
            pg.locator("text=Got it").click(timeout=2000)
            pg.wait_for_timeout(500)
        except Exception:
            pass
        save(pg, "mlflow_run_detail.png", wait_ms=2000)
        pg.close()

        # ── Prometheus: query with results ─────────────────────────────────────
        print("[3] Prometheus — api_requests_total query...")
        pg = ctx.new_page()
        # Use the direct query URL — this pre-populates the expression
        pg.goto(
            "http://localhost:9090/graph?g0.expr=api_requests_total&g0.tab=1&g0.stacked=0",
            timeout=15000
        )
        pg.wait_for_timeout(3000)
        save(pg, "prometheus_metrics.png", wait_ms=1000)
        pg.close()

        # ── Prometheus: targets page ───────────────────────────────────────────
        print("[4] Prometheus — targets page...")
        pg = ctx.new_page()
        pg.goto("http://localhost:9090/targets", timeout=10000)
        pg.wait_for_timeout(2500)
        save(pg, "prometheus_targets.png", wait_ms=500)
        pg.close()

        # ── Swagger: /predict with actual response ─────────────────────────────
        print("[5] Docker Swagger — /predict response...")
        pg = ctx.new_page()
        pg.goto("http://localhost:8000/docs", timeout=15000)
        pg.wait_for_selector(".swagger-ui", timeout=8000)
        pg.wait_for_timeout(1200)

        # Click on POST /predict to expand it
        pg.locator("#operations-default-predict_predict_post").click()
        pg.wait_for_timeout(800)

        # Click Try it out
        pg.locator(".opblock-section-request-body button.btn.try-out__btn").click()
        pg.wait_for_timeout(500)

        # Execute
        pg.locator(".execute-wrapper .btn.execute").click()
        pg.wait_for_timeout(3000)

        # Scroll to show the response section
        pg.evaluate("document.querySelector('.responses-wrapper')?.scrollIntoView()")
        pg.wait_for_timeout(800)
        save(pg, "docker_predict.png", wait_ms=500)
        pg.close()

        browser.close()
    print("\nDone.")


if __name__ == "__main__":
    main()
