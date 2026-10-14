Anh Khải chụp 3 ảnh màn hình, mỗi ảnh ~2-3 phút (tôi không chụp được vì môi trường này không có trình duyệt):

1. Mở viewer/index.html bằng trình duyệt (offline, không cần mạng).
2. Sang chương "9 · phòng lab", kéo thả evidence/viewer.json vào.
3. Ảnh 1 → evidence/shots/ch9-bus-bypass.jpg (REPORT câu 5):
   bấm run B-01 (bus_bypass), kéo thanh thời gian tới đúng vạch đỏ (lúc va chạm) rồi chụp.
4. Ảnh 2 → evidence/shots/ch9-crosswalk-block.jpg (REPORT câu 5):
   bấm run C-01 (crosswalk_block), kéo tới lúc chặn lối (vạch vàng) rồi chụp.
5. Ảnh 3 → evidence/shots/ch9-fix-ghost.jpg (REPORT câu 6):
   bật bóng mờ (ghost = policy mới), bấm từng run B-01..B-04, tìm run mà xe đặc
   (policy gốc) đâm nhưng bóng mờ tránh được, kéo tới lúc va chạm rồi chụp.
6. Ảnh 4 → evidence/shots/ch10-hazard.jpg (REPORT câu 9):
   sang chương 10, mở hazard.json (nút Open), bấm chạy, kéo tới t ≈ 16.2 s
   (lúc ego đâm người băng ngang H0) rồi chụp.
7. Xong: git add evidence/shots, git commit --amend hoặc commit mới, git push.

Lưu ý: chụp đúng lúc va chạm (vạch đỏ/vàng trên thanh thời gian), thấy được cả hai xe/người liên quan.
