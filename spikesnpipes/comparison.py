"""Comparison tools for A/B evaluation of model outputs.

Image comparison uses a custom HTML/JS component for instant
hold-to-overlay, zoom buttons, and synchronised pan — all running
client-side in the browser for zero latency.
"""

from __future__ import annotations

import base64
import difflib
from pathlib import Path

import numpy as np
import streamlit as st
import streamlit.components.v1 as components


# ---------------------------------------------------------------------------
# Image comparison — client-side HTML/JS
# ---------------------------------------------------------------------------


def _img_to_b64(path: Path | str) -> str:
    data = Path(path).read_bytes()
    ext = Path(path).suffix.lstrip(".").lower()
    if ext == "jpg":
        ext = "jpeg"
    return f"data:image/{ext};base64,{base64.b64encode(data).decode()}"


def _estimate_height(path: Path | str) -> int:
    try:
        from PIL import Image as PILImage

        with PILImage.open(str(path)) as img:
            w, h = img.size
        aspect = h / max(w, 1)
        return max(int(400 * aspect), 200)
    except Exception:
        return 400


def render_image_compare(
    img_a_path: Path | str,
    img_b_path: Path | str,
    label_a: str,
    label_b: str,
    key: str,
) -> None:
    mode = st.radio(
        "Compare mode",
        ["Side-by-side", "Pixel diff"],
        horizontal=True,
        key=f"icmp_mode_{key}",
    )

    if mode == "Pixel diff":
        _render_pixel_diff(img_a_path, img_b_path, label_a, label_b, key)
        return

    b64_a = _img_to_b64(img_a_path)
    b64_b = _img_to_b64(img_b_path)
    img_h = _estimate_height(img_a_path)
    k = key.replace(" ", "_").replace("/", "_")

    html = f"""
<style>
  @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600&display=swap');
  * {{ box-sizing: border-box; margin: 0; padding: 0; }}
  body {{ background: transparent; font-family: 'Inter', sans-serif; color: #E5E5E5; }}
  .cmp-row {{ display: flex; gap: 10px; }}
  .cmp-panel {{
    flex: 1; position: relative; overflow: hidden;
    border-radius: 8px; background: #1A1A1A;
    max-height: {img_h + 20}px;
  }}
  .cmp-panel.zoomed {{ overflow: auto; cursor: grab; }}
  .cmp-panel.dragging {{ cursor: grabbing !important; }}
  .cmp-panel img {{ pointer-events: none; width: 100%; display: block; }}
  .cmp-panel img.cmp-overlay {{ position: absolute; top: 0; left: 0; width: 100%; display: none; }}
  .cmp-label {{
    position: absolute; top: 6px; left: 8px; z-index: 2;
    background: rgba(0,0,0,0.65); color: #fff;
    padding: 2px 10px; border-radius: 4px; font-size: 12px;
  }}
  .cmp-controls {{ display: flex; gap: 6px; margin-top: 10px; flex-wrap: wrap; align-items: center; }}
  .cmp-btn {{
    background: #252525; border: 1px solid #3a3a3a; color: #ccc;
    padding: 5px 14px; border-radius: 6px; cursor: pointer;
    font-size: 13px; font-family: 'Inter', sans-serif;
    user-select: none; -webkit-user-select: none;
    transition: background 0.1s;
  }}
  .cmp-btn:hover {{ background: #3a3a3a; }}
  .cmp-btn.active {{ background: #FFF844; color: #0C0C0C; border-color: #FFF844; font-weight: 600; }}
  .cmp-btn-overlay {{
    background: #1a2e1a; border-color: #3CD077; color: #3CD077;
    margin-left: auto;
  }}
  .cmp-btn-overlay:active {{ background: #3CD077; color: #0C0C0C; }}
  .cmp-sep {{ color: #444; margin: 0 2px; }}
</style>

<div id="cmp_{k}">
  <div class="cmp-row">
    <div class="cmp-panel" id="left_{k}">
      <span class="cmp-label" id="lbl_left_{k}">{label_a}</span>
      <img id="imgA_{k}" class="cmp-img" src="{b64_a}">
      <img id="ovB_{k}" class="cmp-img cmp-overlay" src="{b64_b}">
    </div>
    <div class="cmp-panel" id="right_{k}">
      <span class="cmp-label">{label_b}</span>
      <img id="imgB_{k}" class="cmp-img" src="{b64_b}">
    </div>
  </div>
  <div class="cmp-controls">
    <span class="cmp-btn active" data-z="fit" onclick="zoom_{k}('fit')">Fit</span>
    <span class="cmp-btn" data-z="1" onclick="zoom_{k}(1)">100%</span>
    <span class="cmp-btn" data-z="2" onclick="zoom_{k}(2)">200%</span>
    <span class="cmp-btn" data-z="4" onclick="zoom_{k}(4)">400%</span>
    <span class="cmp-sep">|</span>
    <span class="cmp-btn cmp-btn-overlay"
          onmousedown="ovOn_{k}()" onmouseup="ovOff_{k}()"
          onmouseleave="ovOff_{k}()"
          ontouchstart="ovOn_{k}()" ontouchend="ovOff_{k}()">
      ⇄ Hold to overlay
    </span>
  </div>
</div>

<script>
(function() {{
  const L = document.getElementById('left_{k}');
  const R = document.getElementById('right_{k}');
  const imgA = document.getElementById('imgA_{k}');
  const ovB  = document.getElementById('ovB_{k}');
  const lblL = document.getElementById('lbl_left_{k}');

  // --- overlay (hold to peek) ---
  window.ovOn_{k} = function() {{
    imgA.style.display = 'none';
    ovB.style.display = 'block';
    lblL.textContent = '{label_b}';
  }};
  window.ovOff_{k} = function() {{
    imgA.style.display = 'block';
    ovB.style.display = 'none';
    lblL.textContent = '{label_a}';
  }};

  // --- zoom ---
  window.zoom_{k} = function(level) {{
    const imgs = document.querySelectorAll('#cmp_{k} .cmp-img');
    if (level === 'fit') {{
      imgs.forEach(i => i.style.width = '100%');
      L.classList.remove('zoomed');
      R.classList.remove('zoomed');
    }} else {{
      imgs.forEach(i => i.style.width = (level * 100) + '%');
      L.classList.add('zoomed');
      R.classList.add('zoomed');
    }}
    document.querySelectorAll('#cmp_{k} [data-z]').forEach(b => {{
      b.classList.toggle('active', String(b.dataset.z) === String(level));
    }});
  }};

  // --- synchronised scroll ---
  let syncing = false;
  L.addEventListener('scroll', function() {{
    if (syncing) return;
    syncing = true;
    R.scrollTop = L.scrollTop;
    R.scrollLeft = L.scrollLeft;
    syncing = false;
  }});
  R.addEventListener('scroll', function() {{
    if (syncing) return;
    syncing = true;
    L.scrollTop = R.scrollTop;
    L.scrollLeft = R.scrollLeft;
    syncing = false;
  }});

  // --- drag-to-pan (click-and-drag moves both panels) ---
  let dragging = false, dx0 = 0, dy0 = 0, sx0 = 0, sy0 = 0, dp = null;

  function dragStart(e, panel) {{
    if (!panel.classList.contains('zoomed')) return;
    dragging = true;
    dp = panel;
    const ev = e.touches ? e.touches[0] : e;
    dx0 = ev.clientX; dy0 = ev.clientY;
    sx0 = panel.scrollLeft; sy0 = panel.scrollTop;
    panel.classList.add('dragging');
    e.preventDefault();
  }}
  function dragMove(e) {{
    if (!dragging) return;
    const ev = e.touches ? e.touches[0] : e;
    dp.scrollLeft = sx0 - (ev.clientX - dx0);
    dp.scrollTop  = sy0 - (ev.clientY - dy0);
    e.preventDefault();
  }}
  function dragEnd() {{
    if (!dragging) return;
    dragging = false;
    if (dp) dp.classList.remove('dragging');
    dp = null;
  }}

  L.addEventListener('mousedown',  function(e) {{ dragStart(e, L); }});
  R.addEventListener('mousedown',  function(e) {{ dragStart(e, R); }});
  L.addEventListener('touchstart', function(e) {{ dragStart(e, L); }}, {{passive:false}});
  R.addEventListener('touchstart', function(e) {{ dragStart(e, R); }}, {{passive:false}});
  document.addEventListener('mousemove', dragMove);
  document.addEventListener('touchmove', dragMove, {{passive:false}});
  document.addEventListener('mouseup', dragEnd);
  document.addEventListener('touchend', dragEnd);
}})();
</script>
"""
    total_h = img_h + 70
    components.html(html, height=total_h, scrolling=False)


def _render_pixel_diff(
    img_a_path: Path | str,
    img_b_path: Path | str,
    label_a: str,
    label_b: str,
    key: str,
) -> None:
    try:
        from PIL import Image as PILImage

        img_a = np.array(
            PILImage.open(str(img_a_path)).convert("RGB"),
            dtype=np.float32,
        )
        img_b = np.array(
            PILImage.open(str(img_b_path)).convert("RGB"),
            dtype=np.float32,
        )
        if img_a.shape != img_b.shape:
            st.warning(
                "Images have different sizes — "
                "pixel diff unavailable."
            )
            return

        amplify = st.checkbox(
            "Amplify ×10", key=f"icmp_amp_{key}"
        )
        factor = 10.0 if amplify else 1.0
        diff = np.clip(
            np.abs(img_a - img_b) * factor, 0, 255
        ).astype(np.uint8)

        c1, c2, c3 = st.columns(3)
        with c1:
            st.caption(label_a)
            st.image(str(img_a_path), width="stretch")
        with c2:
            st.caption("Pixel diff")
            st.image(diff, width="stretch")
        with c3:
            st.caption(label_b)
            st.image(str(img_b_path), width="stretch")
    except ImportError:
        st.error("Pillow is required for pixel diff.")


# ---------------------------------------------------------------------------
# Text comparison (word-level diff) — renders as markdown
# ---------------------------------------------------------------------------


def _word_diff_html(text_a: str, text_b: str) -> str:
    words_a = text_a.split()
    words_b = text_b.split()
    matcher = difflib.SequenceMatcher(None, words_a, words_b)
    parts: list[str] = []
    for op, i1, i2, j1, j2 in matcher.get_opcodes():
        if op == "equal":
            parts.append(" ".join(words_a[i1:i2]))
        elif op == "delete":
            chunk = " ".join(words_a[i1:i2])
            parts.append(
                f'<span style="background:#5c1a1a;padding:1px 3px;'
                f'border-radius:3px;text-decoration:line-through">'
                f"{chunk}</span>"
            )
        elif op == "insert":
            chunk = " ".join(words_b[j1:j2])
            parts.append(
                f'<span style="background:#1a3a1a;padding:1px 3px;'
                f'border-radius:3px">{chunk}</span>'
            )
        elif op == "replace":
            old = " ".join(words_a[i1:i2])
            new = " ".join(words_b[j1:j2])
            parts.append(
                f'<span style="background:#5c1a1a;padding:1px 3px;'
                f'border-radius:3px;text-decoration:line-through">'
                f"{old}</span>"
            )
            parts.append(
                f'<span style="background:#1a3a1a;padding:1px 3px;'
                f'border-radius:3px">{new}</span>'
            )
    return " ".join(parts)


def render_text_compare(
    text_a: str,
    text_b: str,
    label_a: str,
    label_b: str,
    key: str,
    reference: str | None = None,
) -> None:
    show_diff = st.checkbox(
        "Highlight diff", key=f"tcmp_diff_{key}"
    )

    c1, c2 = st.columns(2)
    with c1:
        st.caption(label_a)
        if show_diff and reference:
            st.markdown(
                _word_diff_html(reference, text_a),
                unsafe_allow_html=True,
            )
        else:
            st.markdown(text_a)
    with c2:
        st.caption(label_b)
        if show_diff:
            base = reference if reference else text_a
            st.markdown(
                _word_diff_html(base, text_b),
                unsafe_allow_html=True,
            )
        else:
            st.markdown(text_b)


# ---------------------------------------------------------------------------
# Video comparison — synced playback via custom HTML/JS
# ---------------------------------------------------------------------------


def _vid_to_b64(path: Path | str) -> str:
    data = Path(path).read_bytes()
    ext = Path(path).suffix.lstrip(".").lower()
    mime = {"mp4": "video/mp4", "webm": "video/webm", "ogg": "video/ogg"}
    return (
        f"data:{mime.get(ext, 'video/mp4')};base64,"
        f"{base64.b64encode(data).decode()}"
    )


def render_video_compare(
    vid_a_path: Path | str,
    vid_b_path: Path | str,
    label_a: str,
    label_b: str,
    key: str,
) -> None:
    b64_a = _vid_to_b64(vid_a_path)
    b64_b = _vid_to_b64(vid_b_path)
    k = key.replace(" ", "_").replace("/", "_")

    html = f"""
<style>
  @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600&display=swap');
  * {{ box-sizing: border-box; margin: 0; padding: 0; }}
  body {{ background: transparent; font-family: 'Inter', sans-serif; color: #E5E5E5; }}
  .vcmp-row {{ display: flex; gap: 10px; }}
  .vcmp-panel {{
    flex: 1; position: relative; border-radius: 8px;
    background: #1A1A1A; overflow: hidden;
  }}
  .vcmp-panel video {{ width: 100%; display: block; }}
  .vcmp-label {{
    position: absolute; top: 6px; left: 8px; z-index: 2;
    background: rgba(0,0,0,0.65); color: #fff;
    padding: 2px 10px; border-radius: 4px; font-size: 12px;
  }}
  .vcmp-controls {{
    display: flex; gap: 6px; margin-bottom: 10px; flex-wrap: wrap;
    align-items: center;
  }}
  .vcmp-btn {{
    background: #252525; border: 1px solid #3a3a3a; color: #ccc;
    padding: 5px 14px; border-radius: 6px; cursor: pointer;
    font-size: 13px; font-family: 'Inter', sans-serif;
    user-select: none; -webkit-user-select: none;
    transition: background 0.1s; min-width: 32px; text-align: center;
  }}
  .vcmp-btn:hover {{ background: #3a3a3a; }}
  .vcmp-btn.active {{ background: #FFF844; color: #0C0C0C; border-color: #FFF844; font-weight: 600; }}
  .vcmp-time {{
    color: #888; font-size: 12px; font-family: 'Inter', monospace;
    margin-left: 6px;
  }}
  .vcmp-seek {{
    flex: 1; min-width: 100px; accent-color: #FFF844;
    height: 4px; cursor: pointer;
  }}
  .vcmp-sep {{ color: #444; margin: 0 2px; }}
</style>

<div id="vcmp_{k}">
  <div class="vcmp-controls">
    <span class="vcmp-btn" id="ppBtn_{k}" title="Play / Pause">&#9654;</span>
    <span class="vcmp-btn" id="prevBtn_{k}" title="Previous frame">&#9664;</span>
    <span class="vcmp-btn" id="nextBtn_{k}" title="Next frame">&#9654;</span>
    <span class="vcmp-sep">|</span>
    <input type="range" class="vcmp-seek" id="seek_{k}" min="0" max="1000" value="0">
    <span class="vcmp-time" id="time_{k}">0:00 / 0:00</span>
    <span class="vcmp-sep">|</span>
    <span class="vcmp-btn" id="spdBtn_{k}">1x</span>
  </div>
  <div class="vcmp-row">
    <div class="vcmp-panel">
      <span class="vcmp-label">{label_a}</span>
      <video id="vA_{k}" src="{b64_a}" preload="auto" muted playsinline></video>
    </div>
    <div class="vcmp-panel">
      <span class="vcmp-label">{label_b}</span>
      <video id="vB_{k}" src="{b64_b}" preload="auto" muted playsinline></video>
    </div>
  </div>
</div>

<script>
(function() {{
  var A = document.getElementById('vA_{k}');
  var B = document.getElementById('vB_{k}');
  var ppBtn = document.getElementById('ppBtn_{k}');
  var prevBtn = document.getElementById('prevBtn_{k}');
  var nextBtn = document.getElementById('nextBtn_{k}');
  var seekBar = document.getElementById('seek_{k}');
  var timeLabel = document.getElementById('time_{k}');
  var spdBtn = document.getElementById('spdBtn_{k}');

  var FRAME_DT = 1 / 30;
  var speeds = [0.25, 0.5, 1, 2];
  var spdIdx = 2;
  var playing = false;
  var rafId = null;

  function fmt(s) {{
    var m = Math.floor(s / 60);
    var sec = Math.floor(s % 60);
    return m + ':' + (sec < 10 ? '0' : '') + sec;
  }}

  function updateUI() {{
    var cur = A.currentTime || 0;
    var dur = A.duration || 0;
    timeLabel.textContent = fmt(cur) + ' / ' + fmt(dur);
    if (dur > 0) seekBar.value = Math.round((cur / dur) * 1000);
  }}

  // tight sync loop running every animation frame while playing
  function syncLoop() {{
    if (!playing) return;
    var drift = A.currentTime - B.currentTime;
    if (Math.abs(drift) > 0.05) B.currentTime = A.currentTime;
    updateUI();
    rafId = requestAnimationFrame(syncLoop);
  }}

  function doPlay() {{
    B.currentTime = A.currentTime;
    var pA = A.play();
    var pB = B.play();
    // handle autoplay promises
    if (pA && pA.catch) pA.catch(function(){{}});
    if (pB && pB.catch) pB.catch(function(){{}});
    playing = true;
    ppBtn.innerHTML = '&#9646;&#9646;';
    rafId = requestAnimationFrame(syncLoop);
  }}

  function doPause() {{
    A.pause();
    B.pause();
    if (rafId) {{ cancelAnimationFrame(rafId); rafId = null; }}
    B.currentTime = A.currentTime;
    playing = false;
    ppBtn.innerHTML = '&#9654;';
    updateUI();
  }}

  ppBtn.addEventListener('click', function() {{
    if (playing) doPause(); else doPlay();
  }});

  prevBtn.addEventListener('click', function() {{
    if (playing) doPause();
    A.currentTime = Math.max(0, A.currentTime - FRAME_DT);
    B.currentTime = A.currentTime;
    updateUI();
  }});

  nextBtn.addEventListener('click', function() {{
    if (playing) doPause();
    A.currentTime = Math.min(A.duration || 0, A.currentTime + FRAME_DT);
    B.currentTime = A.currentTime;
    updateUI();
  }});

  seekBar.addEventListener('input', function() {{
    var dur = A.duration || 0;
    var t = (seekBar.value / 1000) * dur;
    A.currentTime = t;
    B.currentTime = t;
    updateUI();
  }});

  spdBtn.addEventListener('click', function() {{
    spdIdx = (spdIdx + 1) % speeds.length;
    var s = speeds[spdIdx];
    A.playbackRate = s;
    B.playbackRate = s;
    spdBtn.textContent = s + 'x';
    spdBtn.classList.toggle('active', s !== 1);
  }});

  A.addEventListener('ended', function() {{
    doPause();
    A.currentTime = 0;
    B.currentTime = 0;
    updateUI();
  }});

  // disable native controls click-to-play on videos
  A.addEventListener('click', function(e) {{ e.preventDefault(); }});
  B.addEventListener('click', function(e) {{ e.preventDefault(); }});

  A.addEventListener('loadedmetadata', updateUI);
}})();
</script>
"""
    components.html(html, height=500, scrolling=False)


# ---------------------------------------------------------------------------
# Audio comparison
# ---------------------------------------------------------------------------


def render_audio_compare(
    audio_a_path: Path | str,
    audio_b_path: Path | str,
    label_a: str,
    label_b: str,
    key: str,
) -> None:
    c1, c2 = st.columns(2)
    with c1:
        st.caption(label_a)
        st.audio(str(audio_a_path))
    with c2:
        st.caption(label_b)
        st.audio(str(audio_b_path))
