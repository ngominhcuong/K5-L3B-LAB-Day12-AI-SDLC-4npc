"""Đo canvas của chonoi.live tại 1280×720 bằng Chromium thật qua Playwright."""

import argparse
import json
import math
from pathlib import Path
import sys

from .contract import load_contract
from .errors import BadInput
from .live import LiveGame, LiveServer

WIDTH, HEIGHT = 1280, 720
WARMUP_MS = 3000
START_TIMEOUT_MS = 15_000

# Đo nhịp của vòng vẽ hiện tại. lastFrameTime chỉ khớp timestamp sau khi callback
# frame của game đã chạy, nên menu, màn hình tải và các callback riêng của harness
# không thể tự tạo mẫu FPS. Mốc load bắt đầu ở navigation start của trình duyệt.
_MEASURE_CANVAS = """({durationMs, warmupMs, width, height, timeoutMs}) => new Promise((resolve, reject) => {
  const canvas = document.getElementById('c');
  const intervals = [];
  let loadMs, warmupEnd, firstSample, previousSample;
  let pendingFrame;
  let timeout;

  function fail(message) {
    clearTimeout(timeout);
    cancelAnimationFrame(pendingFrame);
    reject(new Error(message));
  }

  function sample(timestamp) {
    if (typeof snap !== 'undefined' && snap?.error) {
      fail('Mô phỏng báo lỗi: ' + snap.error);
      return;
    }
    const playing = typeof snap !== 'undefined' && snap?.phase === 'gather' &&
      !offline && !showMainMenu && !snap.finished;
    if (!playing && loadMs !== undefined) {
      fail('Cảnh gather dừng giữa bài đo');
      return;
    }

    if (playing && lastFrameTime === timestamp) {
      if (canvas.width !== width || canvas.height !== height) {
        fail(`Canvas có kích thước ${canvas.width}×${canvas.height}`);
        return;
      }
      if (loadMs === undefined) {
        loadMs = performance.now();
        warmupEnd = timestamp + warmupMs;
        clearTimeout(timeout);
        timeout = setTimeout(() => fail('Quá thời gian lấy mẫu khung hình'),
          warmupMs + durationMs + timeoutMs);
      } else if (timestamp >= warmupEnd) {
        if (firstSample === undefined) {
          firstSample = timestamp;
        } else {
          intervals.push(timestamp - previousSample);
          if (timestamp - firstSample >= durationMs) {
            clearTimeout(timeout);
            resolve({loadMs, intervals});
            return;
          }
        }
        previousSample = timestamp;
      }
    }
    pendingFrame = requestAnimationFrame(sample);
  }

  timeout = setTimeout(() => fail('Không tải được cảnh gather để bắt đầu đo'), timeoutMs);
  pendingFrame = requestAnimationFrame(sample);
})"""


def _metrics(intervals_ms: list[float], load_ms: float) -> dict[str, int | float]:
    """Tính FPS theo thời gian thực. 1% low dùng trung bình các khoảng cách dài nhất."""
    frames = len(intervals_ms)
    measured_s = sum(intervals_ms) / 1000
    count = math.ceil(frames * 0.01)
    slowest_ms = sorted(intervals_ms, reverse=True)[:count]
    return {
        "avg_fps": frames / measured_s,
        "p1_low_fps": 1000 * count / sum(slowest_ms),
        "frames": frames,
        "measured_s": measured_s,
        "load_ms": load_ms,
    }


def _render(url: str, duration_s: float) -> dict:
    # Playwright chỉ là phụ thuộc của benchmark. Live, headless và soak vẫn chạy
    # bằng thư viện chuẩn từ một bản clone sạch.
    try:
        from playwright.sync_api import Error, sync_playwright
    except ImportError as exc:
        raise RuntimeError("Cần cài Playwright và Chromium theo README.md") from exc

    try:
        with sync_playwright() as playwright:
            browser = playwright.chromium.launch(channel="chromium")
            try:
                page = browser.new_page(viewport={"width": WIDTH, "height": HEIGHT}, device_scale_factor=1)
                page.goto(url, wait_until="domcontentloaded", timeout=START_TIMEOUT_MS)
                page.keyboard.press("Enter")  # Vào cảnh chơi qua phím thật, giữ Út Sen ở điểm xuất phát.
                return page.evaluate(_MEASURE_CANVAS, {
                    "durationMs": duration_s * 1000,
                    "warmupMs": WARMUP_MS,
                    "width": WIDTH,
                    "height": HEIGHT,
                    "timeoutMs": START_TIMEOUT_MS,
                })
            finally:
                browser.close()
    except Error as exc:
        raise RuntimeError(f"Không đo được bằng Chromium: {exc}") from exc


def run_bench(seed: int, duration_s: float) -> dict[str, int | float]:
    """Dùng máy chủ live có sẵn trên cổng tạm để không ảnh hưởng phiên chơi khác."""
    tuning = load_contract()["tuning"]
    server = LiveServer(LiveGame("gather", tuning, {}, seed), port=0)
    server.start()
    try:
        sample = _render(server.url, duration_s)
        return _metrics(sample["intervals"], sample["loadMs"])
    finally:
        server.stop()


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(prog="chonoi.bench", description=__doc__)
    parser.add_argument("--seed", type=int, required=True)
    parser.add_argument("--duration", type=float, required=True, help="số giây đo sau khi làm nóng")
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args(argv)
    if not math.isfinite(args.duration) or args.duration <= 0:
        parser.error("--duration phải là số hữu hạn lớn hơn 0")

    try:
        report = run_bench(args.seed, args.duration)
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    except BadInput as exc:
        print(f"đầu vào sai: {exc}", file=sys.stderr)
        return 2
    except (OSError, RuntimeError) as exc:
        print(f"lỗi benchmark: {exc}", file=sys.stderr)
        return 1
    print(f"bench avg_fps={report['avg_fps']:.2f} p1_low_fps={report['p1_low_fps']:.2f} "
          f"frames={report['frames']} measured_s={report['measured_s']:.3f} load_ms={report['load_ms']:.1f}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
