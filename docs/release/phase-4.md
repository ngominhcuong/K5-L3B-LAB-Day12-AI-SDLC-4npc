# Chuẩn bị phát hành Quán Ăn Chợ Nổi v1.0.0

## Ghi chú phát hành

- Vòng chơi gồm Lặn & Hái, Mở Quán và Shop. Kho lưu theo từng cá thể, độ tươi ảnh hưởng giá chốt món và nâng cấp Shop có hiệu lực từ ngày kế tiếp.
- Test Contract v1.3 có soak chạy 10 ngày liên tiếp, tái hiện được kết quả theo seed. Benchmark render đo cảnh gather trên canvas thật ở 1280×720.
- Phím **H** bật/tắt **Tương phản cao**. Ba cảnh báo Thủy quái, Hết hơi và Sắp rời bàn có chữ vàng và biểu tượng ⚠ trên nền đen.
- [Changelog theo phase](../../CHANGELOG.md) · [Ma trận kiểm chứng](../verification/phase-4.md) · [Nguồn mã khung và công cụ](../../CREDITS.md)

## Kiểm tra trên Windows

Chạy từ thư mục gốc repo trong PowerShell. Các lệnh ghi kết quả vào thư mục tạm.

```powershell
$env:PYTHONPATH = 'tests;.'
$phaseOut = Join-Path ([System.IO.Path]::GetTempPath()) ('chonoi-p4-' + [guid]::NewGuid().ToString('N'))
New-Item -ItemType Directory -Path $phaseOut | Out-Null

python -X utf8 tools/check_team.py
python -X utf8 -m unittest discover -s tests -v
python -X utf8 -m chonoi.soak --seed 7 --days 10 --out (Join-Path $phaseOut 'soak.json')
python -X utf8 -m chonoi.soak --seed 7 --days 10 --out (Join-Path $phaseOut 'soak-run2.json')
python -X utf8 tools/qa_soak_trace.py 7 10

$first = Get-Content -Raw (Join-Path $phaseOut 'soak.json') | ConvertFrom-Json
$second = Get-Content -Raw (Join-Path $phaseOut 'soak-run2.json') | ConvertFrom-Json
if ($first.days_completed -ne 10 -or $first.crashes -ne 0) { throw 'Soak không đạt' }
$first.PSObject.Properties.Remove('duration_s')
$second.PSObject.Properties.Remove('duration_s')
if (($first | ConvertTo-Json -Depth 5 -Compress) -ne ($second | ConvertTo-Json -Depth 5 -Compress)) {
    throw 'Hai lần soak trả kết quả gameplay khác nhau'
}
```

Kỳ vọng `OK` với 92 test, `days_completed=10`, `crashes=0`, ID cá thể không trùng và đủ các pha `gather → quan → shop`. Bộ inputs hồi quy và kết quả mong đợi nằm trong [bằng chứng Phase 3](../proof/phase-3/integration.md).

Chạy nhanh một ngày hoàn chỉnh từ inputs do bot sinh.

```powershell
$dayInputs = Join-Path $phaseOut 'day-inputs.json'
$dayOutput = Join-Path $phaseOut 'day.jsonl'
python -X utf8 tools/qa_autoplay.py --mode day --days 1 --seed 1 --out-inputs $dayInputs
python -X utf8 -m chonoi.headless --mode day --days 1 --seed 1 --ticks 30000 --inputs $dayInputs --out $dayOutput
Get-Content $dayOutput -Tail 1
```

Dòng cuối phải có `type=end`, `reason=days_complete`, `days_completed=1`, `earned=189` và `score=589` với seed này.

Chạy benchmark trong môi trường ảo sau khi cài trình duyệt. Giữ `$phaseOut` từ bước trên.

```powershell
python -m venv .venv
$benchPython = '.\.venv\Scripts\python.exe'
& $benchPython -m pip install playwright
& $benchPython -m playwright install chromium
& $benchPython -X utf8 -m chonoi.bench --seed 42 --duration 30 --out (Join-Path $phaseOut 'bench.json')
if ($LASTEXITCODE -ne 0) { throw 'Benchmark thất bại' }
$bench = Get-Content -Raw (Join-Path $phaseOut 'bench.json') | ConvertFrom-Json
if ($bench.measured_s -lt 30 -or $bench.frames -le 0 -or
    [Math]::Abs($bench.avg_fps - ($bench.frames / $bench.measured_s)) -gt 0.001) {
    throw 'Báo cáo benchmark không hợp lệ'
}
$bench | Format-List
```

`measured_s` có thể vượt 30 giây một khoảng khung hình vì phép đo kết thúc ở khung hình kế tiếp. `p1_low_fps` bằng 1.000 chia cho khoảng cách trung bình của 1% khung hình chậm nhất, tính theo mili giây. Đối chiếu kết quả với các mốc 60/30 FPS và `load_ms ≤ 10000`. Số FPS phụ thuộc máy và trình duyệt. [Thiết lập Chromium trong Playwright](https://playwright.dev/python/docs/browsers)

Chạy `python -X utf8 -m chonoi.live --mode day --days 2`, vào `http://127.0.0.1:8000/` rồi nhấn **Enter**. Nhấn **H** để bật **Tương phản cao**. Lặn đến gần Cá Sấu và chờ oxy dưới 25% để thấy hai cảnh báo ở gather. Ở quán, để một khách chờ đến khi còn tối đa 20% kiên nhẫn. Cả ba nhãn có chữ vàng và biểu tượng ⚠ trên nền đen.

Để kiểm tra điều khiển trong luồng ngày, nhấn **E** khi ở bến để vào quán. **W/↑** phải đi lên và **S/↓** phải đi xuống. Giữ **W** trước khi nhấn **E** là một cách kiểm tra hướng tự cập nhật khi chuyển pha.

## Điều kiện trước khi tạo tag và Release

1. Kiểm tra `game.contract.json` khai `bench_cmd` và `soak_cmd` ở cấp gốc. Chạy benchmark thông qua giá trị manifest với `--seed 42 --duration 30 --out bench.json`.
2. Chủ repo kiểm tra Actions, chạy workflow trên PR và kích hoạt ruleset bảo vệ nhánh mặc định theo [cấu hình nhóm](../../.github/ruleset-main.json). Xác nhận kiểm tra `ci / test` cùng một review approve trước khi merge. Với lần rà `7fdce58`, GitHub có tệp workflow, chưa trả về lần chạy hay ruleset áp dụng cho `main`.
3. Xác nhận giấy phép và phạm vi mã được cấp phép với các chủ sở hữu, gồm mã starter của lab. Giữ điều khoản của starter nếu đơn vị cung cấp xác nhận có giấy phép. MIT là một lựa chọn cho phần mã nhóm sở hữu nếu nhóm muốn cho phép tái sử dụng và các chủ sở hữu đồng ý. Sau khi chốt, đặt `LICENSE` ở thư mục gốc trước khi phát hành gói ZIP. [Hướng dẫn của GitHub](https://docs.github.com/en/repositories/managing-your-repositorys-settings-and-features/customizing-your-repository/licensing-a-repository)
4. Chạy lại ma trận trên đúng commit đã merge vào `main`. Hai tag `phase-4` và `v1.0.0` phải trỏ về cùng commit đã kiểm chứng. Tạo GitHub Release v1.0.0 với ghi chú phía trên và tệp ZIP tải xuống.

Sau khi nhóm tạo tag, có thể kiểm tra và đóng gói như sau.

```powershell
git fetch origin main --tags
$phaseCommit = git rev-parse 'phase-4^{commit}'
if ($LASTEXITCODE -ne 0) { throw 'Thiếu tag phase-4' }
$releaseCommit = git rev-parse 'v1.0.0^{commit}'
if ($LASTEXITCODE -ne 0 -or $phaseCommit -ne $releaseCommit) { throw 'Hai tag phải trỏ cùng commit' }
git merge-base --is-ancestor $phaseCommit origin/main
if ($LASTEXITCODE -ne 0) { throw 'Commit phát hành chưa có trên main' }
git archive --format=zip --prefix=chonoi-v1.0.0/ --output=(Join-Path $phaseOut 'chonoi-v1.0.0.zip') $releaseCommit
```

Giải nén ZIP, vào `chonoi-v1.0.0` và chạy `python -X utf8 -m chonoi.live --mode day --days 2`. Kỳ vọng HTTP `200` ở `/` và `/state`. Snapshot `/state` bắt đầu với `mode=day`, `phase=gather`, `day=1`.
