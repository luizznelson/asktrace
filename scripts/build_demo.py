"""Build an edited walkthrough video from real browser captures.

Inputs : docs/assets/demo/source/*.jpg (+ captures.json), docs/media/storyboard.json
Outputs: docs/assets/demo/asktrace-demo.mp4 (pt) and asktrace-demo-en.mp4 (en)

The video is an edited sequence of real screenshots, not a continuous screen
recording, and it does not measure response time.
"""

import argparse
import json
import shutil
import subprocess
import tempfile
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont, ImageOps

WIDTH, HEIGHT = 1920, 1080
NAVY, TEAL, WHITE, MUTED = "#102138", "#61d5cb", "#f5f8fc", "#b3c2d5"


def font(size, bold=False):
    candidates = (
        Path("C:/Windows/Fonts") / ("seguisb.ttf" if bold else "segoeui.ttf"),
        Path("/usr/share/fonts/truetype/dejavu")
        / ("DejaVuSans-Bold.ttf" if bold else "DejaVuSans.ttf"),
    )
    for path in candidates:
        if path.is_file():
            return ImageFont.truetype(str(path), size)
    raise RuntimeError("Install Segoe UI or DejaVu Sans to reproduce the media layout")


def paragraph(draw, value, position, face, fill, width, spacing=12):
    x, y = position
    line = ""
    for word in value.split():
        trial = (line + " " + word).strip()
        if line and draw.textlength(trial, font=face) > width:
            draw.text((x, y), line, font=face, fill=fill)
            y += face.size + spacing
            line = word
        else:
            line = trial
    if line:
        draw.text((x, y), line, font=face, fill=fill)
        y += face.size + spacing
    return y


def render(scene, index, total, source, language):
    canvas = Image.new("RGB", (WIDTH, HEIGHT), NAVY)
    draw = ImageDraw.Draw(canvas)
    draw.text((65, 32), "asktrace", font=font(48, True), fill=WHITE)
    label = "DEMONSTRAÇÃO GUIADA" if language == "pt" else "GUIDED WALKTHROUGH"
    draw.text((335, 55), label, font=font(22), fill=TEAL)
    draw.text((1260, 55), "asktrace-pyop.onrender.com", font=font(25), fill=MUTED)
    draw.line((65, 112, 1855, 112), fill="#29425d", width=2)
    if scene.get("source"):
        shot = Image.open(source / (scene["source"] + ".jpg")).convert("RGB")
        fitted = ImageOps.contain(shot, (1130, 820), Image.Resampling.LANCZOS)
        x, y = 70 + (1130 - fitted.width) // 2, 152 + (820 - fitted.height) // 2
        draw.rounded_rectangle(
            (x - 9, y - 9, x + fitted.width + 9, y + fitted.height + 9),
            radius=18,
            fill="#dae7f1",
        )
        canvas.paste(fitted, (x, y))
    else:
        draw.rounded_rectangle((100, 190, 1145, 915), radius=28, fill="#19314b")
        draw.text((155, 255), "asktrace", font=font(86, True), fill=TEAL)
        steps = (
            ["Escolha o recorte", "Faça uma pergunta", "Confira as fontes"]
            if language == "pt"
            else ["Choose the dataset", "Ask a question", "Check the sources"]
        )
        for number, line in enumerate(steps, 1):
            y = 430 + (number - 1) * 110
            draw.text((160, y), str(number).zfill(2), font=font(40, True), fill=TEAL)
            draw.text((260, y), line, font=font(45), fill=WHITE)
    text = scene[language]
    draw.text((1260, 190), f"{index + 1:02d} / {total:02d}", font=font(26, True), fill=TEAL)
    end = paragraph(draw, text["title"], (1260, 260), font(53, True), WHITE, 575, 15)
    paragraph(draw, text["body"], (1260, end + 35), font(32), MUTED, 560, 16)
    note = (
        "Capturas reais. Sequência editada.\nO vídeo não mede tempo de resposta."
        if language == "pt"
        else "Real captures. Edited sequence.\nThis video does not measure response time."
    )
    draw.multiline_text((1260, 830), note, font=font(21), fill=MUTED, spacing=9)
    step = 1130 // total
    for n in range(total):
        x = 70 + n * step
        draw.rounded_rectangle(
            (x, 1010, x + step - 10, 1016),
            radius=3,
            fill=TEAL if n <= index else "#29425d",
        )
    footer = (
        "Base histórica do PNCP · Publicação não comprova pagamento"
        if language == "pt"
        else "Historical PNCP dataset · Publication does not establish payment"
    )
    draw.text((70, 1030), footer, font=font(20), fill=MUTED)
    return canvas


def ffmpeg_path():
    found = shutil.which("ffmpeg")
    if found:
        return found
    import imageio_ffmpeg  # optional fallback

    return imageio_ffmpeg.get_ffmpeg_exe()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--language", choices=("pt", "en"), default="pt")
    parser.add_argument("--font-check", action="store_true")
    args = parser.parse_args()
    if args.font_check:
        font(20)
        return
    root = Path(__file__).resolve().parents[1]
    media = root / "docs/assets/demo"
    source = media / "source"
    scenes = json.loads((root / "docs/media/storyboard.json").read_bytes())
    output = media / ("asktrace-demo" + ("-en" if args.language == "en" else "") + ".mp4")
    if output.exists():
        raise FileExistsError("Move the existing video before rebuilding")
    with tempfile.TemporaryDirectory(prefix="asktrace-media-") as temporary:
        folder = Path(temporary)
        listing = []
        for index, scene in enumerate(scenes):
            frame = render(scene, index, len(scenes), source, args.language)
            path = folder / f"{index:02d}.png"
            frame.save(path)
            if index in (0, 4, 6):
                frame.save(media / f"preview-{index:02d}-{args.language}.jpg", quality=90)
            listing.append(f"file '{path.as_posix()}'\nduration {scene['seconds']}")
        listing.append(f"file '{(folder / f'{len(scenes) - 1:02d}.png').as_posix()}'")
        concat = folder / "frames.txt"
        concat.write_text("\n".join(listing) + "\n", encoding="utf-8")
        subprocess.run(
            [
                ffmpeg_path(),
                "-y",
                "-loglevel",
                "error",
                "-f",
                "concat",
                "-safe",
                "0",
                "-i",
                str(concat),
                "-vf",
                "fps=30,format=yuv420p",
                "-c:v",
                "libx264",
                "-preset",
                "veryfast",
                "-crf",
                "23",
                "-movflags",
                "+faststart",
                str(output),
            ],
            check=True,
        )
    print(f"Wrote {output}")


if __name__ == "__main__":
    main()
