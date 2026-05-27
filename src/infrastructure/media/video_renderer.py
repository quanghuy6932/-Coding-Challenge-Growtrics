import os
import textwrap
import tempfile
from dataclasses import dataclass
from typing import List, Tuple
 
import numpy as np
from PIL import Image, ImageDraw, ImageFont
 
# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
 
VIDEO_WIDTH = 1280
VIDEO_HEIGHT = 720
FPS = 24
 
# Color palette — chemistry/science theme
COLOR_BG_TOP    = (15, 32, 65)      # Deep navy blue
COLOR_BG_BOTTOM = (26, 58, 108)     # Slightly lighter navy
COLOR_ACCENT    = (64, 196, 255)    # Bright cyan
COLOR_ACCENT2   = (100, 230, 180)   # Mint green
COLOR_WHITE     = (255, 255, 255)
COLOR_LIGHT     = (200, 220, 255)
COLOR_DIM       = (140, 165, 210)
COLOR_CARD_BG   = (255, 255, 255, 28)  # Semi-transparent white overlay
 
FONT_BOLD   = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
FONT_NORMAL = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
 
 
# ---------------------------------------------------------------------------
# Data types (mirrors core models without importing them — keeps renderer independent)
# ---------------------------------------------------------------------------
 
@dataclass
class SegmentData:
    timestamp_start: float
    timestamp_end: float
    title: str
    voiceover_script: str
    visual_elements: List[str]
 
 
@dataclass
class ManifestData:
    concept_query: str
    total_duration_secs: float
    timeline: List[SegmentData]
 
 
# ---------------------------------------------------------------------------
# Gradient background helper
# ---------------------------------------------------------------------------
 
def _make_gradient_background() -> Image.Image:
    """Creates a vertical linear gradient background (numpy → PIL)."""
    img_array = np.zeros((VIDEO_HEIGHT, VIDEO_WIDTH, 3), dtype=np.uint8)
    for y in range(VIDEO_HEIGHT):
        t = y / VIDEO_HEIGHT
        r = int(COLOR_BG_TOP[0] + t * (COLOR_BG_BOTTOM[0] - COLOR_BG_TOP[0]))
        g = int(COLOR_BG_TOP[1] + t * (COLOR_BG_BOTTOM[1] - COLOR_BG_TOP[1]))
        b = int(COLOR_BG_TOP[2] + t * (COLOR_BG_BOTTOM[2] - COLOR_BG_TOP[2]))
        img_array[y, :] = [r, g, b]
    return Image.fromarray(img_array, "RGB")
 
 
# ---------------------------------------------------------------------------
# Rounded rectangle helper
# ---------------------------------------------------------------------------
 
def _draw_rounded_rect(draw: ImageDraw.ImageDraw, xy: Tuple, radius: int, fill: Tuple):
    x0, y0, x1, y1 = xy
    draw.rectangle([x0 + radius, y0, x1 - radius, y1], fill=fill)
    draw.rectangle([x0, y0 + radius, x1, y1 - radius], fill=fill)
    draw.ellipse([x0, y0, x0 + 2*radius, y0 + 2*radius], fill=fill)
    draw.ellipse([x1 - 2*radius, y0, x1, y0 + 2*radius], fill=fill)
    draw.ellipse([x0, y1 - 2*radius, x0 + 2*radius, y1], fill=fill)
    draw.ellipse([x1 - 2*radius, y1 - 2*radius, x1, y1], fill=fill)
 
 
# ---------------------------------------------------------------------------
# Slide renderer — one PNG per segment
# ---------------------------------------------------------------------------
 
def render_slide(
    segment: SegmentData,
    segment_index: int,
    total_segments: int,
    concept_query: str,
    output_path: str,
):
    """
    Renders a single educational slide as a PNG image.
 
    Layout:
    ┌─────────────────────────────────────────┐
    │  [Topic tag]          [Segment N / N]   │  ← header bar
    │                                          │
    │         SEGMENT TITLE (large)            │  ← title zone
    │  ──────────────────────────────────────  │
    │  Voiceover narration text (wrapped)      │  ← narration card
    │                                          │
    │  ◆ Visual element 1                      │  ← visual elements
    │  ◆ Visual element 2                      │
    │                                          │
    │  ━━━━━━━━━━━━━━━━━━━━░░░░░░░░            │  ← progress bar
    └─────────────────────────────────────────┘
    """
    img = _make_gradient_background()
    draw = ImageDraw.Draw(img, "RGBA")
 
    # --- Fonts ---
    try:
        font_title     = ImageFont.truetype(FONT_BOLD,   48)
        font_subtitle  = ImageFont.truetype(FONT_BOLD,   22)
        font_body      = ImageFont.truetype(FONT_NORMAL, 22)
        font_small     = ImageFont.truetype(FONT_NORMAL, 18)
        font_tag       = ImageFont.truetype(FONT_BOLD,   17)
        font_visual    = ImageFont.truetype(FONT_NORMAL, 20)
    except IOError:
        font_title = font_subtitle = font_body = font_small = font_tag = font_visual = ImageFont.load_default()
 
    PAD = 60
    y = 0
 
    # --- Top header bar ---
    draw.rectangle([0, 0, VIDEO_WIDTH, 60], fill=(10, 22, 50))
    # Left: topic label
    topic_label = "🧪  GROWTRICS · AI CHEMISTRY"
    draw.text((PAD, 18), topic_label, font=font_tag, fill=COLOR_ACCENT)
    # Right: segment counter
    counter_text = f"SECTION  {segment_index + 1} / {total_segments}"
    ct_bbox = draw.textbbox((0, 0), counter_text, font=font_tag)
    ct_w = ct_bbox[2] - ct_bbox[0]
    draw.text((VIDEO_WIDTH - PAD - ct_w, 18), counter_text, font=font_tag, fill=COLOR_DIM)
 
    y = 80
 
    # --- Concept query (small subtitle above title) ---
    query_short = concept_query if len(concept_query) <= 70 else concept_query[:67] + "..."
    draw.text((PAD, y), query_short, font=font_small, fill=COLOR_DIM)
    y += 32
 
    # --- Accent line ---
    draw.rectangle([PAD, y, PAD + 60, y + 3], fill=COLOR_ACCENT)
    y += 18
 
    # --- Segment Title ---
    draw.text((PAD, y), segment.title.upper(), font=font_title, fill=COLOR_WHITE)
    y += 70
 
    # --- Narration card ---
    CARD_X0, CARD_X1 = PAD, VIDEO_WIDTH - PAD
    CARD_Y0 = y
    # Wrap narration text
    wrapped = textwrap.wrap(segment.voiceover_script, width=76)
    line_h = 30
    CARD_H = 28 + len(wrapped) * line_h + 20
    _draw_rounded_rect(draw, (CARD_X0, CARD_Y0, CARD_X1, CARD_Y0 + CARD_H), radius=12, fill=(255, 255, 255, 22))
    draw.text((CARD_X0 + 20, CARD_Y0 + 14), "NARRATION", font=font_tag, fill=COLOR_ACCENT2)
    ty = CARD_Y0 + 38
    for line in wrapped:
        draw.text((CARD_X0 + 20, ty), line, font=font_body, fill=COLOR_LIGHT)
        ty += line_h
    y = CARD_Y0 + CARD_H + 28
 
    # --- Visual elements ---
    if segment.visual_elements:
        draw.text((PAD, y), "ON SCREEN", font=font_tag, fill=COLOR_ACCENT2)
        y += 26
        for elem in segment.visual_elements[:4]:  # cap at 4 to avoid overflow
            elem_short = elem if len(elem) <= 72 else elem[:69] + "..."
            # Diamond bullet
            draw.polygon([
                (PAD + 8, y + 10),
                (PAD + 16, y + 4),
                (PAD + 24, y + 10),
                (PAD + 16, y + 16),
            ], fill=COLOR_ACCENT)
            draw.text((PAD + 34, y), elem_short, font=font_visual, fill=COLOR_LIGHT)
            y += 30
 
    # --- Progress bar (bottom) ---
    BAR_Y = VIDEO_HEIGHT - 40
    BAR_X0 = PAD
    BAR_X1 = VIDEO_WIDTH - PAD
    BAR_W = BAR_X1 - BAR_X0
    progress = (segment_index + 1) / total_segments
 
    # Track
    draw.rectangle([BAR_X0, BAR_Y, BAR_X1, BAR_Y + 6], fill=(255, 255, 255, 40))
    # Fill
    fill_w = int(BAR_W * progress)
    # Gradient fill: cyan → mint
    for px in range(fill_w):
        t = px / max(fill_w, 1)
        r = int(COLOR_ACCENT[0] + t * (COLOR_ACCENT2[0] - COLOR_ACCENT[0]))
        g = int(COLOR_ACCENT[1] + t * (COLOR_ACCENT2[1] - COLOR_ACCENT[1]))
        b = int(COLOR_ACCENT[2] + t * (COLOR_ACCENT2[2] - COLOR_ACCENT[2]))
        draw.rectangle([BAR_X0 + px, BAR_Y, BAR_X0 + px + 1, BAR_Y + 6], fill=(r, g, b))
 
    # Bottom label
    pct_text = f"{int(progress * 100)}%  COMPLETE"
    draw.text((PAD, BAR_Y + 12), pct_text, font=font_small, fill=COLOR_DIM)
 
    img.save(output_path, "PNG")
 
 
# ---------------------------------------------------------------------------
# Video assembler — slides → MP4
# ---------------------------------------------------------------------------
 
def assemble_video(manifest: ManifestData, output_path: str) -> str:
    """
    Assembles multiple slide images into a single MP4 video.
 
    Each segment becomes a still image held for (timestamp_end - timestamp_start) seconds.
    moviepy concatenates them into a single video stream.
 
    Returns the output_path on success.
    """
    from moviepy import ImageClip, concatenate_videoclips
 
    clips = []
    total_segments = len(manifest.timeline)
 
    with tempfile.TemporaryDirectory() as tmpdir:
        for idx, segment in enumerate(manifest.timeline):
            slide_path = os.path.join(tmpdir, f"slide_{idx:03d}.png")
            duration = segment.timestamp_end - segment.timestamp_start
 
            render_slide(
                segment=segment,
                segment_index=idx,
                total_segments=total_segments,
                concept_query=manifest.concept_query,
                output_path=slide_path,
            )
 
            clip = ImageClip(slide_path).with_duration(duration)
            clips.append(clip)
 
        final = concatenate_videoclips(clips, method="compose")
        final.write_videofile(
            output_path,
            fps=FPS,
            codec="libx264",
            audio=False,
            logger=None,          # suppress moviepy verbose logs
            preset="ultrafast",   # fast encoding for prototyping
        )
        final.close()
 
    return output_path
 
 
# ---------------------------------------------------------------------------
# Public entry point
# ---------------------------------------------------------------------------
 
def render_manifest_to_video(manifest_data: dict, output_path: str) -> str:
    """
    Converts a VideoArtifactManifest dict into an MP4 file.
    This is the single public interface used by StructuredMediaEngine.
 
    Args:
        manifest_data: dict with keys matching VideoArtifactManifest fields
        output_path: absolute path for the output .mp4 file
 
    Returns:
        output_path on success
    """
    segments = [
        SegmentData(
            timestamp_start=seg["timestamp_start"],
            timestamp_end=seg["timestamp_end"],
            title=seg["title"],
            voiceover_script=seg["voiceover_script"],
            visual_elements=seg.get("visual_elements", []),
        )
        for seg in manifest_data["timeline"]
    ]
 
    manifest = ManifestData(
        concept_query=manifest_data["concept_query"],
        total_duration_secs=manifest_data["total_duration_secs"],
        timeline=segments,
    )
 
    return assemble_video(manifest, output_path)