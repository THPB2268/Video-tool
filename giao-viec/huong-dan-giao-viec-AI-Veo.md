# Cách giao việc cho AI để Veo làm đúng kịch bản

## 1. Năm nguyên tắc

1. **Chia việc, không bắt một AI làm hết.** Biên kịch → đạo diễn (shot list) → kiểm tra → Veo → chấm điểm. Mỗi bước một lời giao việc riêng.
2. **Veo không nhớ gì và không đọc kịch bản.** Mỗi lần gọi Veo là một lần làm lại từ đầu. Cái gì cần giống nhau giữa các clip phải được **chép nguyên văn** vào từng prompt, và quan trọng hơn: **đưa ảnh** cho nó.
3. **Chữ không giữ được mặt người và sản phẩm, ảnh thì giữ được.** Mô tả bằng chữ kỹ đến đâu, mỗi clip vẫn ra một khuôn mặt và một kiểu sản phẩm hơi khác. Cách chắc chắn: tạo ảnh khung đầu từ ảnh sản phẩm thật và ảnh nhân vật cố định, rồi cho Veo làm chuyển động từ ảnh đó.
4. **AI bắt chước ví dụ nhiều hơn nghe luật.** Luôn đưa kèm một ví dụ mẫu đúng (đã có sẵn trong prompt đạo diễn).
5. **Đừng tin AI tự kiểm tra.** Kiểm bằng code (đếm, dò từ cấm) và bằng một AI khác xem clip (Gemini).

## 2. Quy trình 5 bước

| Bước | Ai làm | Đưa vào | Nhận về |
|---|---|---|---|
| 1. Viết kịch bản | LLM "biên kịch" | Thông tin sản phẩm + góc bán hàng | Kịch bản tiếng Việt quay được |
| 2a. Tả ảnh thật (một lần cho mỗi sản phẩm, mỗi nhân vật) | Gemini xem ảnh | Ảnh sản phẩm thật, ảnh nhân vật | `product_look`, `character_look` |
| 2b. Chuyển thành shot list | LLM "đạo diễn" + **Prompt đạo diễn** (file `prompt-dao-dien.txt`) | Kịch bản + thông tin sản phẩm + product_look + character_look + thời lượng | JSON: bible, từng shot, lời đọc, chữ chèn, ảnh cần đính kèm |
| 3. Kiểm tra JSON | Code (hoặc `lint.py`) | JSON | Đạt / danh sách lỗi → gửi lại cho LLM sửa |
| 4. Tạo clip | Model ảnh (Nano Banana) rồi Veo | keyframe_prompt + các ảnh trong `images_to_attach` → ảnh khung đầu; veo_prompt + negative_prompt + ảnh khung đầu → clip | Clip 4/6/8 giây |
| 5. Chấm clip | Gemini (xem video) | Clip + JSON của shot + ảnh sản phẩm | PASS / FAIL + gợi ý sửa |

Sau đó mới dựng:
- Cắt mỗi clip lấy đoạn từ giây `trim_start_seconds`, dài `use_seconds`.
- Bỏ tiếng Veo. Đọc `voiceover_vi` của từng shot thành một đoạn TTS riêng (cùng một giọng tiếng Việt), đặt ở đầu shot đó, để lời khớp với hình.
- Thêm nhạc nền chung, tiếng động `sfx_edit`, chữ chèn `overlay_text_vi`, và nhãn "Video tạo bằng AI".

## 3. Bước 1: thêm vào lời giao việc cho AI viết kịch bản

Dán thêm đoạn này vào prompt bạn đang dùng để viết kịch bản:

```
Kịch bản này sẽ được quay bằng AI tạo video, nên mỗi ý phải là thứ QUAY ĐƯỢC:
- Mỗi cảnh: một người làm MỘT việc đơn giản với sản phẩm (cầm, đặt, nhấn nút, rót chậm), hoặc sản phẩm tự hoạt động một mình.
- Không dùng: chữ/số/giá trên hình, màn hình điện thoại, nhiều người tương tác, trẻ em, gương, cảnh trước/sau, "X phút sau" trong cùng cảnh, thao tác tay tinh vi (bóc hộp, vặn nắp, lắp đặt, thoa kem), ăn uống cận cảnh.
- Giá, khuyến mãi, con số: chỉ đưa vào lời đọc và chữ chèn.
- Nhân vật không nói trước máy quay; toàn bộ lời là giọng đọc (voiceover), tối đa 3 âm tiết mỗi giây video.
- Không để nhân vật tự nhận đã dùng sản phẩm ("mình dùng 1 tuần rồi"); viết lời giới thiệu sản phẩm, không giả làm khách hàng.
- Không dùng "nhất", "số 1", "duy nhất", "tốt nhất" khi không có giấy tờ chứng minh; không so sánh với sản phẩm đối thủ khi không có bằng chứng.
- Ghi rõ từng ý bán hàng và cảnh nào thể hiện nó.
```

## 4. Bước 2: prompt đạo diễn

**2a. Tả ảnh thật, làm một lần cho mỗi sản phẩm và mỗi nhân vật.** Lỗi lớn khi chạy thử: AI đạo diễn tự bịa chi tiết sản phẩm (thêm đèn, đổi màu tay cầm). Chữ tả khác với ảnh thì Veo sẽ biến hình sản phẩm giữa clip. Vì vậy gửi ảnh cho Gemini với lời dặn:

```
Nhìn ảnh này. Viết MỘT câu tiếng Anh, tối đa 30 từ, bắt đầu bằng "The [tên sản phẩm] is ...", tả đúng những gì thấy: hình dạng, màu, kích thước so với một vật quen thuộc (ví dụ kettle-sized), các bộ phận nhìn thấy, và kết thúc bằng góc chụp và trạng thái trong ảnh (ví dụ "shown from the front with the lid closed"). Không đoán thứ không thấy. Chữ, số, logo trên sản phẩm chỉ gọi là "small printed markings".
```

Với ảnh nhân vật: "... bắt đầu bằng "The woman is ..." / "The man is ...", tả tuổi (viết bằng chữ), tóc, quần áo và màu, móng tay, tay áo."

Nếu video cần cảnh sản phẩm đang mở (mở nắp, kéo ngăn kéo), hãy **chụp thêm một ảnh thật lúc mở** và tả tương tự thành `product_open_look`. Không có ảnh này thì AI đạo diễn sẽ đánh dấu các cảnh đó là "cần quay thật", vì model ảnh tự vẽ phần bên trong sẽ mỗi lần một kiểu.

Lưu các câu này, dùng lại cho mọi video của sản phẩm đó.

**2b. Gọi AI đạo diễn.** Dán **toàn bộ** file `prompt-dao-dien.txt` làm system prompt (lời dặn hệ thống) cho LLM. Mỗi lần chạy chỉ cần gửi:

```
Sản phẩm: ...
product_look: The ... is ..., shown from the front with ...
product_open_look: (nếu có) The open ... shows ...
character_look: The woman is ...
Thời lượng: 20 giây. Độ phân giải: 720p.
Kịch bản: ...
```

Cài đặt nên dùng:
- Bật chế độ trả JSON (structured output / JSON mode) nếu API có.
- Nhiệt độ (temperature): nếu LLM là Gemini 3 trở lên thì **giữ mặc định**, vì Google khuyên không chỉnh. Model khác (GPT, Claude...) để thấp, khoảng 0.2–0.4.

Những điểm chính prompt này ép AI làm (đều đến từ lỗi thật khi chạy thử):
- **Bible**: mô tả cố định nhân vật, sản phẩm, đồ vật, bối cảnh, ánh sáng; chép nguyên văn vào mọi prompt.
- **Mỗi shot một hành động**, chia 3 pha: đứng yên 1 giây → làm một việc chậm → đứng yên đến hết clip. Veo hết chỗ để bịa thêm động tác. Khi dựng cắt bỏ giây đứng yên đầu (`trim_start_seconds`).
- **start_state / end_state** theo mẫu cố định. Shot sau khớp shot trước; thứ gì thay đổi ngoài hình (mở nắp, đổi chỗ) phải ghi "Ngoài hình: ..." trong note. Đây là thứ chữa lỗi "ghép rời rạc".
- **Tay nào làm**: người quay mặt về máy quay thì tay phải của họ ở bên trái khung hình. Tay làm việc phải là tay ở cùng phía với đồ vật, không vắt chéo qua người. Đây là một nguyên nhân chính của "hành động phi logic" mà vòng chạy thử cuối phát hiện.
- **Hướng thao tác đúng**: người chỉ chạm vào mặt sản phẩm đang quay về phía họ (lỗi thật khi chạy thử: người đứng sau nồi chiên mà kéo ngăn kéo quay ra máy quay).
- **Shot cơ chế** (đá rơi, đèn bật): quay sản phẩm một mình, và thứ sắp rơi phải có sẵn ngay khung đầu. Không để Veo tự "biến" ra đá.
- **Ảnh đính kèm cho từng shot** (`images_to_attach`): ảnh sản phẩm (đóng hoặc mở), ảnh nhân vật, ảnh bối cảnh, keyframe hoặc khung cuối của shot trước, để giữ cùng người, cùng căn phòng.
- **Cảnh khó được viết lại** thành cảnh dễ cùng ý (trộm → một người đứng một mình che mắt khi đèn chiếu). Cảnh cần chứng minh thật (giao diện app, độ nét, cổng sạc, bộ phận tháo rời) thì đánh dấu quay thật, và shot đó không có nhân vật AI để chèn cảnh thật vào không bị lệch người.
- **Không cho Veo nói tiếng Việt**, không có chữ trong hình: lời đọc và chữ chèn làm lúc dựng.
- **Bảng ý bán hàng**: ý nào bị bỏ phải ghi ra, không lặng lẽ mất.

## 5. Bước 3: kiểm tra JSON bằng code trước khi gửi Veo

Gửi lại cho LLM sửa nếu có bất kỳ lỗi nào sau (file `lint.py` làm sẵn những việc này, chạy: `python3 lint.py shotlist.json`):
- `duration_seconds` không phải 4, 6, 8 (1080p thì phải 8); đoạn cắt không nằm trọn trong clip; tổng `use_seconds` lệch thời lượng quá 1 giây.
- Shot `continuous` không chép nguyên trạng thái cuối của shot trước; shot đứng trước nó không cắt đến hết clip.
- Trạng thái khác shot trước mà note không có dòng "Ngoài hình: ...".
- `veo_prompt` ngoài khoảng 100–300 từ; có chữ số (trừ "9:16"); có câu bắt đầu bằng "It"; có "or", "no", "not", "without", "again", "previous"...
- `negative_prompt` không bắt đầu bằng danh sách chuẩn, thêm quá 4 thứ, hoặc có từ trùng với từ trong `veo_prompt` (prompt có "ice maker" mà negative có "ice" thì Veo bị rối).
- Thiếu 3 câu pha, hoặc 3 pha cộng lại không bằng độ dài clip.
- `action` có "then", "while", "until", "after".
- Mục setting, style, ambience, lighting của bible không nằm nguyên văn trong `veo_prompt`.
- `voiceover_vi` quá 3 âm tiết × `use_seconds` (tiếng Việt: đếm số chữ cách nhau bằng dấu cách).

Cách gửi lại: "JSON của bạn có các lỗi sau: [danh sách]. Sửa đúng các lỗi này, giữ nguyên phần còn lại, trả lại toàn bộ JSON."

## 6. Bước 4: gửi cho model ảnh và Veo

**Ảnh nhân vật** (làm một lần cho cả chiến dịch): dùng model ảnh tạo một ảnh chân dung từ câu `bible.character`, nền trơn, đứng thẳng. Dùng lại ảnh này cho mọi shot. Không dùng ảnh người thật khi chưa có đồng ý bằng văn bản.

**Ảnh bối cảnh** (làm một lần cho mỗi bối cảnh): một ảnh căn phòng trống theo câu `bible.setting`. Đính kèm khi `images_to_attach` có "setting", để các shot không ra mỗi shot một căn bếp. Kịch bản có cảnh đêm thì làm thêm "setting_night": sửa ảnh setting thành cùng chỗ đó lúc đêm.

**Ảnh khung đầu** cho mỗi shot có `transition: "cut"`: gửi model ảnh (Nano Banana) `keyframe_prompt` + đúng các ảnh ghi trong `images_to_attach` ("product" = ảnh sản phẩm thật, "product_open" = ảnh thật lúc mở ở mục 2a, "character", "setting", "keyframe:N" = ảnh khung đầu của shot N, "last_frame:N" = khung cuối clip shot N), khung dọc 9:16.
- Xem nhanh ảnh này trước khi tạo video (sửa ảnh rẻ hơn nhiều so với sửa video).
- Model ảnh cũng có thể vẽ lại nhãn và chữ trên bao bì. Shot nào cần nhãn đúng thì so vùng nhãn trong ảnh với ảnh sản phẩm thật, hoặc dán ảnh sản phẩm thật đè lên.

**Xem nháp trước khi tốn tiền Veo (nên làm với kịch bản mới):** ghép các ảnh khung đầu + giọng đọc TTS + chữ chèn thành một video trình chiếu (slideshow) bằng FFmpeg. Nhìn là biết ngay câu chuyện có logic không. Bước này gần như miễn phí, và bắt lỗi "không logic" ở chỗ rẻ nhất.

**Shot `continuous`**: lấy khung cuối của clip trước làm ảnh khung đầu:
`ffmpeg -sseof -0.1 -i clip_truoc.mp4 -frames:v 1 khung_cuoi.png`
Chỉ nối kiểu này tối đa 1–2 lần liên tiếp. Nối nhiều hơn thì hình và mặt người trôi dần; lúc đó tạo keyframe mới từ ảnh gốc.

**Gọi Veo** cho mỗi shot:
- prompt = `veo_prompt`
- ảnh khung đầu (image-to-video) = ảnh ở trên
- `negativePrompt` = `negative_prompt`
- `aspectRatio` = "9:16" (**phải đặt bằng tham số**, ghi trong câu chữ là không đủ)
- `durationSeconds` = `duration_seconds`
- `personGeneration` = "allow_adult" khi dùng ảnh khung đầu có người. Qua Gemini API: image-to-video chỉ nhận "allow_adult", text-to-video chỉ nhận "allow_all"; đặt sai sẽ bị lỗi 400. Trẻ em luôn bị chặn.

Lưu ý:
- Không dùng "reference images" (ảnh tham chiếu) cùng lúc với ảnh khung đầu: API không cho kết hợp. Ảnh tham chiếu bắt buộc clip 8 giây và không có ở bản Lite.
- Qua Gemini API, muốn 1080p thì clip gần như chắc chắn phải dài 8 giây. Clip 4 hoặc 6 giây nên để 720p.
- Qua Gemini API, mỗi lệnh gọi chỉ trả 1 video, nên "tạo 2 bản" là 2 lệnh gọi. Vertex AI trả được 1–2 bản mỗi lệnh.
- Kiểm tra lệnh lỗi trước: nếu kết quả không có video, xem đó là lỗi hạn mức (429), lỗi tham số (400), hay bị bộ lọc an toàn chặn (`rai_media_filtered_reasons`). Chỉ trường hợp bị lọc mới nên thử lại hoặc viết lại prompt.
- Ghép clip theo mã shot (`shot_number`), không theo thứ tự kết quả trả về, vì các lệnh chạy song song xong không theo thứ tự.
- Tiếng Veo bỏ đi khi dựng; lồng TTS tiếng Việt một giọng cố định cho cả video. Giọng miền Nam hoặc miền Bắc có ở FPT.AI, Viettel AI, Vbee; ElevenLabs v3 cũng đọc được tiếng Việt. Trước khi đưa vào TTS, viết số và giá thành chữ ("199k" → "một trăm chín mươi chín nghìn").
- Chữ chèn tiếng Việt: dùng font có đủ dấu (ví dụ Be Vietnam Pro), chuẩn hóa chữ về dạng NFC để dấu không bị tách, và chừa lề trên cho dấu của chữ hoa (Ấ, Ổ).
- Video kiểu UGC có người nói vào máy: Veo không nói tiếng Việt ổn định. Shot đó được đánh dấu `needs_real_footage`. Cách hợp nhất: dùng công cụ avatar lip-sync tiếng Việt (ví dụ HeyGen nhận file giọng TTS của bạn) tạo từ đúng ảnh nhân vật, rồi ghi nhãn AI. Nếu quay người thật thì ảnh nhân vật của CẢ video phải là ảnh người đó, không thì mặt người sẽ đổi giữa các shot.
- Shot có dòng "Quay thật: ..." trong note: quay đúng như mô tả (nền, hướng sáng, cỡ cảnh, thời lượng), rồi thay vào chỗ clip tạm của Veo.
- Cảnh cuối chỉ có sản phẩm (packshot, end card): dùng ảnh sản phẩm thật và hiệu ứng zoom chậm của FFmpeg, không cần Veo. Rẻ hơn và nhãn không bị méo.
- Hạn mức (quota): 500 video/ngày × 5 shot × 2 bản ≈ 5.000 lệnh gọi Veo mỗi ngày. Kiểm tra hạn mức trong Google Cloud console trước; ở quy mô này nên chạy qua Vertex AI.

## 7. Bước 5: cho Gemini chấm từng clip

Gửi Gemini (model đọc được video) clip + JSON của shot + ảnh sản phẩm thật + ảnh khung đầu.

**Quan trọng:** khi gửi video cho Gemini, đặt tốc độ lấy mẫu `fps` = 5–10 (trong `videoMetadata`). Mặc định Gemini chỉ xem 1 khung hình mỗi giây, tức là 8 khung cho clip 8 giây, nên sẽ bỏ sót tay méo, chữ lóe lên hay cú cắt ngắn mà vẫn báo PASS.

Lời dặn:

```
Bạn là người kiểm tra chất lượng clip quảng cáo do AI tạo. Kèm theo: (1) clip video, (2) JSON mô tả shot, (3) ảnh sản phẩm thật, (4) ảnh khung đầu đã dùng.
Xem kỹ từng giây. Chỉ đánh giá những gì thật sự thấy, không đoán. Trả về đúng JSON:
{
  "start_matches": true/false,
  "action_matches": true/false,
  "end_matches": true/false,
  "extra_actions": ["động tác thừa không có trong action"],
  "product_matches_photo": true/false,
  "person_consistent": true/false,
  "extra_people_or_objects": ["..."],
  "onscreen_text": true/false,
  "talking": true/false,
  "physics_errors": [{"time": "00:03", "problem": "tay méo / vật xuyên nhau / vật tự xuất hiện"}],
  "verdict": "PASS hoặc FAIL",
  "fix_hint": "nếu FAIL: nên sửa gì trong veo_prompt hoặc start_state"
}
FAIL nếu có bất kỳ mục true/false nào sai (talking và onscreen_text phải là false), có extra_actions, hoặc có physics_errors nhìn thấy rõ.
```

Cách chấm chắc hơn (nên dùng khi AI chấm hay cho PASS nhầm): chia làm 2 lần gọi.
1. Lần 1 gửi **chỉ video**, không gửi JSON: "Mô tả từng giây chuyện gì xảy ra, có bao nhiêu người, tay cầm gì, có chữ nào xuất hiện, có lỗi hình nào không."
2. Lần 2 gửi mô tả đó cùng JSON của shot để so sánh và cho PASS/FAIL.

Khi được đưa JSON ngay từ đầu, AI chấm hay "thấy" đúng thứ kịch bản viết dù video không có.

Quy tắc tạo lại:
1. Mỗi shot tạo 2 bản, lấy bản PASS.
2. Cả 2 FAIL: tạo lại tối đa 2 lần nữa.
3. Vẫn FAIL: gửi `fix_hint` về AI đạo diễn để viết lại riêng shot đó trong JSON, rồi dựng lại prompt từ JSON. Đừng chắp thêm câu sửa vào cuối prompt cũ, vì prompt sẽ dài ra và tự mâu thuẫn. Hoặc đưa người duyệt.
4. Mỗi ngày xem tay ngẫu nhiên khoảng 5–10% video đã PASS để biết AI chấm có đáng tin không.

## 8. Chi phí cần biết

- Veo tính tiền theo giây **tạo ra**, không phải giây dùng. Video 18 giây ở ví dụ mẫu tạo 30 giây clip; tạo 2 bản mỗi shot là 60 giây (khoảng $6 với bản Fast 720p, $3 với bản Lite).
- Giá Veo 3.1 theo trang giá Google Cloud (xem ngày 25/9/2026), có tiếng / không tiếng, mỗi giây:
  - Lite: $0,05 / $0,03 (720p); $0,08 / $0,05 (1080p)
  - Fast: $0,10 / $0,08 (720p); $0,12 / $0,10 (1080p)
  - Standard: $0,40 / $0,20
- Lite và Fast đều nhận ảnh khung đầu, nên thử chúng trước. Thử trên đúng bản bạn sẽ dùng khi sản xuất, vì tỷ lệ đạt không giống nhau giữa các bản.
- Qua Gemini API, Veo luôn tạo và tính tiền phần tiếng. Qua Vertex AI tắt được tiếng (`generateAudio` = false), rẻ hơn khoảng 17–50% tùy bản. Vì đằng nào bạn cũng bỏ tiếng Veo để lồng TTS, đây là khoản tiết kiệm đáng kể.
- Ở 50–500 video/ngày: giữ lại các clip đã PASS (cảnh sản phẩm, cảnh cơ chế, cảnh CTA) làm **thư viện** dùng lại cho nhiều biến thể. Mỗi video mới chỉ tạo thêm 1–2 clip (thường là hook). Vừa rẻ vừa ít chỗ hỏng.

## 9. Pháp lý cần biết (nên hỏi luật sư trước khi chạy lớn)

- **Luật Trí tuệ nhân tạo 134/2025/QH15** (hiệu lực 01/3/2026), Điều 11: video, hình, tiếng do AI tạo phải có đánh dấu máy đọc được. Nội dung mô phỏng hình ảnh hoặc giọng nói của người thật phải có nhãn dễ nhận biết. Nội dung có thể gây hiểu nhầm về tính xác thực phải thông báo rõ. Khi dựng lại bằng FFmpeg, phần đánh dấu kiểu C2PA bị mất, nên hãy thêm nhãn "Video tạo bằng AI" nhìn thấy được và bật nhãn nội dung AI trên TikTok/Facebook.
- **Nghị định 142/2026/NĐ-CP** (hiệu lực 01/5/2026) hướng dẫn cách đánh dấu: nhúng vào cấu trúc file, metadata, chữ ký số... (C2PA là một cách hợp lệ).
- **Luật Quảng cáo sửa đổi 75/2025/QH15** (hiệu lực 01/01/2026):
  - Quảng cáo trên mạng phải có dấu hiệu nhận biết là quảng cáo rõ ràng (ví dụ chữ "Quảng cáo" hoặc #quảngcáo).
  - Người giới thiệu sản phẩm phải đã dùng hoặc hiểu sản phẩm. Vì vậy video avatar AI nói ngôi thứ nhất kiểu "mình dùng 1 tuần rồi" có rủi ro bị coi là đánh giá giả. Theo Nghị định 87/2026, người có ảnh hưởng quảng cáo sản phẩm chưa dùng có thể bị phạt 80–100 triệu đồng. Nên để lời đọc ở dạng giới thiệu sản phẩm, không giả làm khách hàng đã dùng.
  - Cấm "nhất", "số 1", "duy nhất", "tốt nhất" khi không có giấy tờ chứng minh.
- Mỹ phẩm, thực phẩm chức năng, sức khỏe: có danh sách câu chữ bị cấm và có loại cần duyệt nội dung trước. Đưa danh sách từ cấm vào bước kiểm tra JSON.
- Không dùng mặt hoặc giọng người thật (kể cả người nổi tiếng) khi chưa có đồng ý bằng văn bản.

## 10. Những điều đừng làm

- Đừng gửi thẳng kịch bản cho Veo.
- Đừng dùng chữ "or / hoặc" trong mô tả cảnh.
- Đừng để một clip có nhiều việc nối tiếp.
- Đừng bắt Veo nói tiếng Việt hay viết chữ trên hình.
- Đừng chạy text-to-video (không có ảnh) cho cảnh có sản phẩm của bạn.
- Đừng đưa video ra ngoài khi chưa qua bước chấm.
