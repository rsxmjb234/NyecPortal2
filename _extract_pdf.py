import os
from pypdf import PdfReader

PDF = "HEALTHeLINK-Fusion-User-Training-Guide (1).pdf"
outdir = "_guide_assets"
os.makedirs(outdir, exist_ok=True)

reader = PdfReader(PDF)
print("pages:", len(reader.pages))

# dump text
with open(os.path.join(outdir, "guide_text.txt"), "w", encoding="utf-8") as f:
    for i, pg in enumerate(reader.pages):
        f.write(f"\n===== PAGE {i+1} =====\n")
        f.write(pg.extract_text() or "")

# dump images
count = 0
for i, pg in enumerate(reader.pages):
    try:
        imgs = pg.images
    except Exception as e:
        imgs = []
    for img in imgs:
        count += 1
        name = f"p{i+1:02d}_{count:03d}_{img.name}"
        path = os.path.join(outdir, name)
        with open(path, "wb") as fh:
            fh.write(img.data)
print("images extracted:", count)
