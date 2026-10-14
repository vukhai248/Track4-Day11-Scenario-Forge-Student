MSSV: 202602786 

# Lab 11 · Scenario Forge — báo cáo

Mỗi câu: trả lời ngắn, **trích số từ `evidence/`** (ghi tên file và trường, ví dụ `mc.json: crashes = 4`). Grader chạy lại với MSSV của bạn; số không khớp `evidence/` thì mất điểm phần D (RUBRIC), và câu dựa trên số sai khó được điểm đầy đủ. Không cần văn hay: một bảng nhỏ và hai, ba câu giải thích là đủ.

Thị trấn của bạn (`meta.json: _run.town`): B (rainier: wet=0.30, pedLook=0.85, brakes=0.15, cut_gap_median=12.0)

## 1. Phát lại log có trung thực không? (bước A)

`replay.json`: n = 400, dropped_human_crash_logs = 0, n_used = 400. Planner trên log phát lại: crashes = 121 (rear = 108, side = 13). Planner trong thế giới phản ứng: crashes = 0. crash_in_both = 0.

Phần lớn va chạm phát lại là `rear` vì xe bám đuôi (TG) trong log chạy đúng như đã ghi, không biết planner phanh sớm hơn người lái thật nên đâm vào đuôi ego. Đó là va chạm **giả**: ngoài đời xe sau sẽ phanh theo (trong thế giới phản ứng cùng 400 kịch bản này có 0 va chạm, và mọi vụ replay-only đều an toàn khi phản ứng: ví dụ `replay_only[0]` scenario = 1, contact = rear, min_ttc_reactive = 2.42).

## 2. Kịch bản bất khả thi (bước B)

4 luật trong `feasible.is_feasible`:
- `a_lat = (pi/cutDur)^2*3.5/2 > mu*g` → loại: lạng làn cosine cần gia tốc ngang đỉnh vượt quá bám đường (ma sát) cho phép; xe thật sẽ trượt/văng.
- `cutBrake > mu*g` → loại: phanh sau nhập làn mạnh hơn lốp chịu được (kể cả ABS, giới hạn vật lý mu*g).
- `pedV > 2.5 m/s` → loại: người đi bộ không chạy nhanh hơn tốc độ chạy bộ (~2.5 m/s).
- `cutV` ngoài (0, 22] m/s → loại: tốc độ xe phố không âm/không đứng yên và không quá ~79 km/h.

`hunt.json: infeasible`: bus_bypass = 2, cut_in = 2, crosswalk_block = 0, rear_ended = 1. Hai cuộc săn bus_bypass và cut_in sinh nhiều nhất (2). CEM bị kéo về đó vì điểm nguy hiểm đơn điệu theo hướng cực đoan (cutDur càng ngắn / cutBrake càng mạnh / pedV càng nhanh thì "nguy hiểm" càng cao), mà chính vùng cực đoan đó là vùng bất khả thi — elite toàn kịch bản không thật. Nếu **đếm** chúng là va chạm: ước lượng lệch lên (cộng thất bại không thể xảy ra), q thắt quanh vùng ảo, ngân sách đổ vào kịch bản vô nghĩa.

## 3. Monte Carlo cho bạn biết gì (bước C1)

`mc.json`: k = 4, n = 3000, p̂ = 1.33e-03, khoảng Wilson 95% lo = 5.19e-04, hi = 3.42e-03 (infeasible = 23, đã loại trước khi đếm).

Để khoảng hẹp còn ±20% của p cần n ≈ 96/p̂ ≈ 96/1.33e-03 ≈ 72 000 lần chạy (vì nửa khoảng tương đối ≈ 1.96·sqrt((1-p)/(np)) = 0.2 → n ≈ 96/p).

3 kiểu chưa xuất hiện: cut_in (k = 0), rear_ended (k = 0), other (k = 0). Con số đúng cần báo là cận trên Wilson hi = 1.28e-03 cho mỗi kiểu (`per_mode.*.hi`), không báo 0.

## 4. Importance sampling, ESS và độ suy biến (bước C3)

`estimate.json` (budget = 16800; `other`: k = 0, p = 0, hi = 1.28e-03, source = mc.json):

| kiểu | seed 0 (p / hits / ess / top_share) | seed 1 | seed 2 |
|---|---|---|---|
| bus_bypass | 5.1e-04 / 28 / 138 / 0.29 | 1.7e-03 / 36 / 137 / 0.50 | 9.4e-04 / 28 / 143 / 0.37 |
| cut_in | 0 / 0 / 117 / 0 (upper 0.025) | 0 / 0 / 116 / 0 (0.025) | 0 / 0 / 122 / 0 (0.025) |
| crosswalk_block | 2.0e-05 / 54 / 104 / 0.37 | 1.7e-05 / 55 / 117 / 0.40 | 5.5e-06 / 45 / 107 / 0.78 |
| rear_ended | 0 / 0 / 104 / 0 (upper 0.025) | 0 / 0 / 126 / 0 (0.025) | 0 / 0 / 123 / 0 (0.025) |
| total | 5.26e-04 [1.77e-04, 2.15e-03] | 1.69e-03 [0, 4.69e-03] | 9.50e-04 [1.58e-04, 3.02e-03] |

Ba seed chênh nhau ~3x ở total (5.3e-04 vs 1.69e-03); trung vị 9.50e-04 khớp Monte Carlo (1.33e-03) trong ~1.4x — đồng ý ở mức độ lớn, đúng như cảnh báo "thường thấp hơn sự thật 1.5–4x, seed chênh vài lần". `top_share` > 0.5 ở crosswalk_block seed 2 (0.78): 78% ước lượng do một mẫu nặng nhất mang — con số thực ra là trọng số của một mẫu, khoảng ±1.96·se khi đó hẹp sai.

Ngân sách: IS tốn 16 800 lần chạy cho cả 4 kiểu × 3 seed; Monte Carlo cần ~72 000 lần cho cùng ±20% ở p ~ 1e-3 — IS rẻ hơn ~4x nhưng mong manh (top_share cao, seed phân tán). Phần `other` lấy từ `mc.json` vì các kiểu chia nhau tập va chạm mà `other` không được săn (nó là rổ hỗn hợp, không có điểm nguy hiểm riêng để dẫn CEM); săn nó cũng không hiệu quả vì hiếm và phân tán.

## 5. Các kiểu thất bại (bước C2 + 3D)

- bus_bypass (`hunt.json: found` = 137 đúng kiểu): C2 lách qua xe buýt đang đỗ (x < 112 m, v < 6 m/s) để vào làn, ego tới cùng lúc → đâm trực diện `front`. Ảnh: `evidence/shots/ch9-bus-bypass.jpg` (chương 9, chạy B-01, kéo đến đúng lúc va chạm).
- crosswalk_block (10 đúng kiểu trong cuộc săn của nó): người đi bộ bước ra từ sau xe buýt đỗ (planner không thấy vì bị che), ego phanh gấp và dừng nhưng thân xe đã nằm trên vạch qua đường, chắn lối P1 đang qua → sự kiện `kind == "block"`. Ảnh: `evidence/shots/ch9-crosswalk-block.jpg`.
- Không tìm thấy: cut_in (cuộc săn của nó tìm 38 bus_bypass, 0 cut_in) và rear_ended (15 bus_bypass + 10 crosswalk_block, 0 rear_ended). Mức tin: Monte Carlo 3000 lần không thấy vụ nào → mỗi kiểu < 1.28e-03 (95%); IS 0 hits chỉ cho cận yếu 0.025 — tin ở mức "hiếm hơn ~1e-3", không chứng minh được hiếm hơn nữa với ngân sách này.
- Nếu chỉ chạy **một** cuộc săn chung: CEM co về kiểu dễ nhất (bus_bypass) và lặp mãi nó — bằng chứng là cuộc săn cut_in và rear_ended cũng chỉ ra bus_bypass. Vì vậy mỗi kiểu cần một cuộc săn với điểm nguy hiểm riêng.

## 6. Sửa planner (bước E + 3D)

`fix.json`: chọn ứng viên #11 `chosen.policy = {cutinLat: 3.0, cautionV: 7.0}` (thấp nhất `fail_hi` trên TRAIN trong các ứng viên giữ ≥95% quãng đường baseline).
- TRAIN: chosen fail = 5.06e-07 (hi = 9.06e-07), progress = 208.9 m; baseline fail = 1.13e-03 (hi = 1.87e-03), progress = 215.1 m.
- TEST (seed mới + săn lại nhắm vào từng policy — con số để báo cáo): chosen fail = 1.65e-05, `fail_hi_seen` = 4.66e-05, `fail_hi` (hợp lệ) = 3.88e-02, unseen = [bus_bypass], progress = 207.1 m, harsh = 8.83. Baseline TEST: fail = 4.03e-04, `fail_hi_seen` = 7.06e-04, `fail_hi` = 1.98e-03, unseen = [], progress = 214.6 m, harsh = 8.23.
- Quãng đường chỉ giảm (214.6−207.1)/214.6 = 3.5% ≤ 5% ✓. Dữ liệu cho thấy bản sửa tốt hơn ~15x (`fail_hi_seen` 4.66e-05 vs 7.06e-04): bus_bypass biến mất dưới ngưỡng phát hiện (TEST re-hunt 8 vòng không tìm thấy vụ bus_bypass nào cho policy mới), crosswalk_block còn lại p = 1.65e-05 (nhưng top_share = 0.93 — một mẫu quyết định).
- Vì sao `fail_hi` của bản sửa (3.88e-02) lớn hơn `fail` của policy gốc (4.03e-04) dù bản sửa tốt hơn thật: kiểu `unseen` cộng cận `upper_zero_hits` = 3/(0.2·400) = 0.0375 vào `fail_hi`. Xoá hẳn một kiểu khỏi tầm phát hiện với n = 400 vẫn để lại cận ~15/n — đó là giá của chứng nhận, không phải bằng chứng bản sửa tệ. Muốn chứng nhận p < 1e-3 cần ~15 000 lần chạy đúng chỗ đó.
- Ảnh bóng mờ: `evidence/shots/ch9-fix-ghost.jpg` (chương 9, một run B mà baseline đâm nhưng ghost = policy mới tránh được).
- Núm "nghe an toàn hơn" nhưng phản tác dụng: `T = 2.0` (giữ khoảng cách thời gian lớn hơn). TRAIN fail = 1.32e-03, tệ hơn baseline 1.13e-03, quãng đường 205.7 m. Vì thế giới phản ứng lại: giữ gap lớn → chạy chậm, dừng sớm/lâu trước vạch và trước xe cắt làn → xe bám đuôi (tgT nhỏ) áp sát trong lúc ego phanh cho người đi bộ, và thân xe nằm lâu trong vùng nguy hiểm. Tương tự `cautionV = 5.0` bò quá chậm (progress 173.6 m, −19%) với số lần phanh gấp cao nhất (harsh = 13.88) mà không an toàn hơn.

## 7. Từ mô phỏng ra đường thật

Ba giả định ảnh hưởng nhất (town B):
1. Khe chấp nhận của xe chuyển làn `cutGap` ~ lognormal median 12 m. Dữ liệu thật: phân bố gap-acceptance đo bằng camera/lidar đặt bên đường tại các điểm nhập làn ở Hà Nội (đo khe xe trước/sau tại thời điểm bắt đầu chuyển làn, tách theo giờ cao điểm/thấp điểm). Sai theo hướng nào: nếu lái xe thật chấp nhận khe nhỏ hơn (hung hăng hơn), p(bus_bypass/cut_in) thật lớn hơn số lab.
2. Tỉ lệ đường ướt 0.30 (mu = 0.5 thay vì 0.8). Dữ liệu thật: tỉ lệ thời gian mặt đường ướt từ trạm khí tượng + cảm biến mặt đường (kết hợp lưu lượng theo giờ). Nếu tỉ lệ ướt thật thấp hơn (mùa khô), quãng phanh thật ngắn hơn → p thật nhỏ hơn số lab (lab đang bi quan).
3. Tỉ lệ người đi bộ ngó qua xe buýt `pedLook` = 0.85. Dữ liệu thật: quan sát tại vạch có xe buýt đỗ (đếm người thò đầu nhìn trước khi bước xuống). Nếu người thật ít cẩn thận hơn (tỉ lệ thấp hơn), họ bước ra bất ngờ hơn → p(crosswalk_block) thật lớn hơn số lab.

## 8. Giới hạn

1. Thế giới chỉ có một con phố với đúng một bộ diễn viên cố định — xác suất báo không nói gì về ngã tư, đường cong, xe máy, hay mật độ giao thông khác.
2. Xe khác chỉ là IDM + luật nhường cứng nhắc (không hung hăng, không mất tập trung, không say) — không có hành vi đuôi dài ngoài đời.
3. Cảm biến hoàn hảo trừ che khuất bởi xe buýt (không nhiễu, không mưa/lóa, không điểm mù radar) — p đo được là cận dưới của rủi ro cảm biến thật.
Nếu có thêm một tuần: đo độ nhạy với mật độ giao thông (scale số xe) và thêm nhiễu cảm biến (bỏ sót detection theo khoảng cách) để xem kiểu nào bùng lên.

Trong `replay.json`: bao nhiêu kịch bản bị bỏ vì người lái gây va chạm, bao nhiêu va chạm khi planner chạy trên log phát lại, bao nhiêu trong thế giới phản ứng, theo từng loại tiếp xúc. Giải thích vì sao phần lớn va chạm của "phát lại" là `rear`, và vì sao đó là va chạm **giả**. Chọn một kịch bản trong `replay_only` và nói chuyện gì đã xảy ra.

## 2. Kịch bản bất khả thi (bước B)

Liệt kê các luật trong `is_feasible` và căn cứ vật lý của từng luật (ma sát, gia tốc, tốc độ người). Trong `hunt.json`, cuộc săn nào sinh nhiều kịch bản bất khả thi nhất, và vì sao CEM lại bị kéo về phía đó? Điều gì xảy ra với ước lượng nếu bạn **đếm** chúng là va chạm?

## 3. Monte Carlo cho bạn biết gì (bước C1)

`mc.json`: k, n, p̂ và khoảng Wilson 95 %. Với p̂ đó, cần bao nhiêu lần chạy để khoảng tin cậy hẹp lại còn ±20 % của p? Có kiểu thất bại nào **chưa hề xuất hiện** trong 3 000 lần chạy không? Con số đúng cần báo cho kiểu đó là gì?

## 4. Importance sampling, ESS và độ suy biến (bước C3)

Bảng: với từng kiểu và từng seed trong `estimate.json`, ghi `p`, `hits`, `ess`, `top_share`. Ba seed có đồng ý với nhau không, và có đồng ý với Monte Carlo không? Ở đâu `top_share` lớn (> 0,5), và vì sao khi đó con số thực ra chỉ là trọng số của một mẫu? So ngân sách (`budget`) với số lần chạy Monte Carlo cần để có cùng độ chính xác. Phần `other` trong tổng lấy từ đâu, và vì sao không săn nó?

## 5. Các kiểu thất bại (bước C2 + 3D)

Mỗi kiểu bạn tìm thấy: một ảnh chụp trình xem 3D (chương 9) ở đúng lúc va chạm, và một câu mô tả chuỗi sự kiện (ai thấy gì, ai chờ gì). Kiểu nào cuộc săn **không** tìm thấy, và bạn tin điều đó ở mức nào? Nếu chỉ chạy **một** cuộc săn chung cho mọi kiểu thì điều gì xảy ra (gợi ý: `hunt.json: found` của từng cuộc săn)?

## 6. Sửa planner (bước E + 3D)

`fix.json`: policy được chọn, `fail` và `fail_hi` trên TRAIN, trên TEST (`fail_hi_seen` và `fail_hi`), và của policy gốc trên TEST; vì sao `fail_hi` của bản sửa có thể lớn hơn `fail` của policy gốc dù bản sửa tốt hơn thật? quãng đường và số lần phanh gấp. Một ảnh chụp 3D có **bóng mờ** (policy gốc) cho một kịch bản mà bản sửa tránh được. Có núm chỉnh nào "nghe thì an toàn hơn" nhưng thực tế làm tăng thất bại? Giải thích bằng cách thế giới phản ứng lại.

## 7. Từ mô phỏng ra đường thật

Phân phối tự nhiên trong `space.py` là giả định. Chọn **ba** giả định ảnh hưởng nhiều nhất đến con số của bạn (ví dụ khe chấp nhận của xe chuyển làn, tỉ lệ người đi bộ ngó qua xe buýt, ma sát đường ướt). Với mỗi cái: dữ liệu thật nào sẽ thay nó, lấy từ đâu, và nếu nó sai thì con số của bạn sai theo hướng nào?

## 8. Giới hạn

Ba điều mà xác suất bạn báo **không** nói, ví dụ: thế giới chỉ có một con phố; người lái chỉ là IDM; cảm biến hoàn hảo trừ phần bị xe buýt che. Nếu được thêm một tuần, bạn sẽ đo gì tiếp?

## 9. Rắc rối của bạn (bước G + chương 10)

- **Rắc rối:** người đi bộ băng ngang đường ở chỗ **không có vạch**, từ lề nam (`hazard.json`: một hazard `ped` H0, side = S). Ngoài đời giống người tạt qua đường phố đông ở Hà Nội, ngoài vạch, trước đầu ôtô.
- **Căn cứ:** planner chỉ có logic nhường người ở vạch (yield gắn `WALK` + `pedBuffer`) và chỉ coi người ngoài vạch là xe trước khi họ đã vào hành lang (lat ≤ 1.9 m) — tức là khi đã quá muộn ở 12 m/s.
- **Giả định** (`hazard.json: space/exposure/why`): `h0_x` = [100, 180] (đoạn phố trước mặt ego), `h0_v` = [1.0, 2.2] m/s (dải đi bộ người lớn), `h0_trig` = [20, 45] m (bắt đầu đi khi ego còn cách từng đó); `exposure` = 0.04 (4 chuyến/100 chuyến gặp một người băng ngoài vạch trước đầu xe; căn cứ khảo sát camera + tỉ lệ trong `why`).
- **Kết quả** (`mine.json`, accepted = 1484/1500 = 99%, cảnh gốc planner đâm ego–H0 ở t = 16.2 s):
  - baseline: crashes = 75 = 68 `avoidable` + 1 `unavoidable` + 6 `unattributed` (`low_speed` = 5); P(lỗi planner | rắc rối) = 4.58e-02, Wilson [3.63e-02, 5.77e-02]; × exposure = 1.83e-03/chuyến (cận trên 2.31e-03).
  - chosen ({cutinLat 3.0, cautionV 7.0}): crashes = 58 = 58 + 0 + 0 (`low_speed` = 1); P = 3.91e-02 [3.04e-02, 5.02e-02]; 1.56e-03/chuyến (cận trên 2.01e-03).
  - `avoidable_foreknown` bằng đúng `avoidable` (68/68 và 58/58): người này luôn nhìn thấy từ đầu nên che khuất không tốn gì ở đây.
  - Đặt cạnh tần suất lách xe buýt (~1e-3 theo IS/MC): rắc rối này ~1.8e-03/chuyến — nguy hiểm tương đương hoặc hơn kiểu chính của thị trấn.
- **Hình:** `evidence/shots/ch10-hazard.jpg` (chương 9/10 ở lúc va chạm t ≈ 16.2 s).
- **Bạn tự lái thì sao:** chưa tự lái trong viewer; người lái thật sẽ nhả ga/phanh ngay khi thấy người trên lề có hướng đi ra (đọc ý định), điều planner thiếu — planner chỉ phản ứng khi người đã vào hành lang.
- **Cách sửa:** không núm nào sửa triệt để (`pedBuffer` chỉ tác dụng ở vạch; `cautionRange` chỉ cho vùng bị xe buýt che). Cần logic mới: nhường mọi người đi bộ có vectơ di chuyển cắt làn ego trong vòng ~40 m (dự đoán ý định qua đường ngoài vạch), chứ không chỉ người ở vạch.
