"""Kiểm tra shot list JSON (bản 3) trước khi gửi Veo.
Cách dùng: python3 lint.py shotlist.json
In ra "OK" nếu đạt, hoặc danh sách lỗi để gửi lại cho AI đạo diễn sửa."""
import json, re, sys

NUM = {"one": 1, "two": 2, "three": 3, "four": 4, "five": 5, "six": 6, "seven": 7}
BANNED = r"\b(or|as appropriate|as shown|etc|various|some kind of|again|returning|same as|previous|continues|the next shot)\b"
NEGATION = r"\b(no|not|without|empty of)\b"
CONNECTORS = r"\b(then|and then|while|as|until|after|ending with)\b"
BASE_NEG = "subtitles, captions, on-screen text, watermark, talking, speech, singing, music, extra people, cuts, split screen, extra fingers, distorted hands, deformed product, duplicate product"

d = json.load(open(sys.argv[1]))
B, shots, errs = d["bible"], d["shots"], []
props = B.get("props", {}) or {}

def e(n, msg): errs.append(f"shot {n}: {msg}")

for k, lim in [("character", 30), ("hands", 15), ("product", 40), ("setting", 25), ("setting_close", 15),
               ("lighting_day", 20), ("lighting_night", 20), ("style", 15), ("ambience", 12)]:
    if len((B.get(k) or "").split()) > lim: errs.append(f"bible.{k} dài quá {lim} từ")
for k, v in props.items():
    if len(v.split()) > 15: errs.append(f"bible.props.{k} dài quá 15 từ")

total = 0
for i, s in enumerate(shots):
    n, p, dur, use, trim = s["shot_number"], s["veo_prompt"], s["duration_seconds"], s["use_seconds"], s["trim_start_seconds"]
    total += use
    if dur not in (4, 6, 8): e(n, f"duration_seconds = {dur}, chỉ được 4/6/8")
    if d.get("resolution") == "1080p" and dur != 8: e(n, "1080p thì mọi shot phải 8 giây")
    if use < 2 or trim < 0 or trim + use > dur: e(n, f"đoạn dùng [{trim}, {trim + use}] không nằm trọn trong clip {dur} giây")
    nxt = shots[i + 1] if i + 1 < len(shots) else None
    if nxt and nxt["transition"] == "continuous" and trim + use != dur:
        e(n, "shot đứng trước shot continuous phải có trim_start_seconds = duration_seconds - use_seconds")
    if s["transition"] == "continuous":
        prev = shots[i - 1] if i > 0 else None
        if not prev: e(n, "shot 1 không được là continuous")
        elif s["start_state"] != prev["end_state"]: e(n, "continuous nhưng start_state không chép nguyên end_state shot trước")
        if s["keyframe_prompt"]: e(n, "shot continuous phải để keyframe_prompt rỗng")
    elif i > 0 and s["start_state"] != shots[i - 1]["end_state"] and "Ngoài hình" not in s["note"]:
        e(n, "trạng thái khác shot trước mà note không có dòng 'Ngoài hình: ...'")
    w = len(p.split())
    if not 100 <= w <= 300: e(n, f"veo_prompt có {w} từ, cần 100-300")
    for f in ("veo_prompt", "action", "keyframe_prompt"):
        m = re.findall(BANNED, s[f], re.I)
        if m: e(n, f"từ cấm {sorted(set(m))} trong {f}")
    m = re.findall(NEGATION, p, re.I)
    if m: e(n, f"từ phủ định {sorted(set(m))} trong veo_prompt")
    if re.search(r"\d", p.replace("9:16", "")): e(n, "có chữ số trong veo_prompt")
    if re.search(r"(^|[.!?]\s+)It\b", p): e(n, "có câu bắt đầu bằng 'It'")
    m = re.findall(CONNECTORS, s["action"], re.I)
    if m: e(n, f"action có từ nối {sorted(set(m))}")
    light = B.get("lighting_night") if s.get("lighting") == "night" else B.get("lighting_day")
    for label, text in [("style", B["style"]), ("ambience", B["ambience"]), ("lighting", light)]:
        if text and text not in p: e(n, f"bible.{label} không nằm nguyên văn trong veo_prompt")
    if B["setting"] not in p and not (B.get("setting_close") and B["setting_close"] in p):
        e(n, "không có setting hoặc setting_close nguyên văn trong veo_prompt")
    a = re.search(r"Over the next (\w+) seconds?", p)
    b = re.search(r"For the final (\w+) seconds?", p)
    b_one = "For the final second" in p
    if not (a and (b or b_one) and "For the first second" in p): e(n, "thiếu câu 3 pha (For the first second / Over the next N / For the final M)")
    elif 1 + NUM.get(a.group(1).lower(), 0) + (NUM.get(b.group(1).lower(), 0) if b else 1) != dur:
        e(n, f"3 pha cộng lại không bằng {dur} giây")
    syl = len(s["voiceover_vi"].split())
    if syl > 3 * use: e(n, f"voiceover_vi {syl} âm tiết, tối đa {3 * use}")
    if re.search(r"\bno\b", s["negative_prompt"], re.I): e(n, "negative_prompt có chữ 'no'")
    if not s["negative_prompt"].startswith(BASE_NEG): e(n, "negative_prompt không bắt đầu bằng danh sách chuẩn")
    extra = [t.strip() for t in s["negative_prompt"][len(BASE_NEG):].split(",") if t.strip()]
    if len(extra) > 4: e(n, f"negative_prompt thêm {len(extra)} thứ, tối đa 4")
    pw = set(re.findall(r"[a-z]+", p.lower()))
    for t in extra:
        clash = [w for w in re.findall(r"[a-z]+", t.lower()) if w in pw]
        if clash: e(n, f"negative '{t}' trùng từ {clash} trong veo_prompt")
    print(f"shot {n}: {s['transition']:<10} {w} từ, lời đọc {syl} âm tiết, clip {dur}s, dùng [{trim}, {trim + use}]")

if abs(total - d["total_seconds"]) > 1: errs.append(f"tổng use_seconds = {total}, yêu cầu {d['total_seconds']}")
print("OK" if not errs else "LỖI:\n  " + "\n  ".join(errs))
