"""Kiểm tra công thức báo cáo benchmark mà không cần cài trình duyệt trong CI."""

import unittest

from chonoi.bench import _metrics


class BenchMetricsTest(unittest.TestCase):
    def test_uses_measured_duration_and_slowest_one_percent(self):
        # 101 khoảng cách nghĩa là phải lấy 2 mẫu chậm nhất, kể cả khi chúng
        # nằm ở hai đầu cửa sổ đo. Đây là 1% low FPS, không phải FPS trung bình.
        report = _metrics([50.0] + [10.0] * 99 + [100.0], 200.0)
        self.assertEqual(report["frames"], 101)
        self.assertAlmostEqual(report["measured_s"], 1.14)
        self.assertAlmostEqual(report["avg_fps"], 101 / 1.14)
        self.assertAlmostEqual(report["p1_low_fps"], 1000 / 75)
        self.assertEqual(report["load_ms"], 200.0)
