#!/usr/bin/env python3
"""
pdf_merge_and_split.py

1. Take an input PDF.
2. Merge all pages vertically into one long image.
3. Split that image into multiple standard-height pages (like A4).
4. Save the result as a multi-page PDF in ./converted/<same-name>.pdf

Dependencies:
    pip install pymupdf Pillow
"""

import os
import sys
import argparse
from io import BytesIO

from PIL import Image
import fitz  # from PyMuPDF


def merge_pages_to_image(input_pdf_path: str, zoom: float = 3.0):
    """Render all pages and merge vertically into one large Pillow image."""
    doc = fitz.open(input_pdf_path)
    pil_images = []

    for i in range(doc.page_count):
        page = doc.load_page(i)
        mat = fitz.Matrix(zoom, zoom)
        pix = page.get_pixmap(matrix=mat, alpha=False)
        pil = Image.open(BytesIO(pix.tobytes("png"))).convert("RGB")
        pil_images.append(pil)
        print(f"Rendered page {i + 1}/{doc.page_count}")

    max_width = max(img.width for img in pil_images)
    total_height = sum(img.height for img in pil_images)
    combined = Image.new("RGB", (max_width, total_height), (255, 255, 255))

    y = 0
    for img in pil_images:
        x = (max_width - img.width) // 2
        combined.paste(img, (x, y))
        y += img.height

    print(f"Combined image size: {max_width}x{total_height}")
    return combined


def split_long_image_to_pages(long_image: Image.Image, page_height: int):
    """Slice a long image into a list of standard-height pages."""
    width, height = long_image.size
    pages = []
    for top in range(0, height, page_height):
        bottom = min(top + page_height, height)
        crop = long_image.crop((0, top, width, bottom))
        pages.append(crop)
    print(f"Sliced into {len(pages)} standard pages.")
    return pages


def merge_and_split_pdf(input_pdf_path: str, output_dir: str = "converted", zoom: float = 3.0):
    """Main workflow."""
    if not os.path.isfile(input_pdf_path):
        raise FileNotFoundError(f"Input file not found: {input_pdf_path}")

    basename = os.path.basename(input_pdf_path)
    name, _ = os.path.splitext(basename)
    os.makedirs(output_dir, exist_ok=True)
    output_path = os.path.join(output_dir, f"{name}.pdf")

    # Step 1: Merge all pages vertically into one big image
    combined_image = merge_pages_to_image(input_pdf_path, zoom=zoom)

    # Step 2: Define "standard page" height
    # For A4 at 300 DPI, page height ≈ 3508 px, but adjust to your rendering DPI (zoom=3 ~ 216 DPI)
    # You can tweak this to match your preference
    standard_page_height =  2500 # scale height with zoom

    # Step 3: Split into slices
    page_slices = split_long_image_to_pages(combined_image, standard_page_height)

    # Step 4: Save all slices as a multi-page PDF
    page_slices[0].save(
        output_path,
        "PDF",
        save_all=True,
        append_images=page_slices[1:],
        resolution=72.0,
    )

    print(f"✅ Saved paginated merged PDF: {output_path}")
    return output_path



def process_folder(folder_path: str, output_dir: str, zoom: float, recursive: bool = False):
    """Process all PDFs in a folder."""
    pdf_files = []
    if recursive:
        for root, _, files in os.walk(folder_path):
            for f in files:
                if f.lower().endswith(".pdf"):
                    pdf_files.append(os.path.join(root, f))
    else:
        pdf_files = [
            os.path.join(folder_path, f)
            for f in os.listdir(folder_path)
            if f.lower().endswith(".pdf")
        ]

    if not pdf_files:
        print(f"No PDFs found in folder: {folder_path}")
        return

    print(f"Found {len(pdf_files)} PDF(s) in '{folder_path}'")

    for pdf_path in pdf_files:
        try:
            print(f"\n--- Processing: {pdf_path} ---")
            merge_and_split_pdf(pdf_path, output_dir=output_dir, zoom=zoom)
        except Exception as e:
            print(f"❌ Error processing {pdf_path}: {e}")


def main():
    parser = argparse.ArgumentParser(description="Merge PDF pages into a long image, then split into standard-sized pages.")
    parser.add_argument("input_path", help="Path to input PDF file or folder")
    parser.add_argument("--outdir", "-o", default="converted", help="Output folder (default: converted)")
    parser.add_argument("--zoom", "-z", type=float, default=3.0, help="Render zoom factor (default 3.0)")
    parser.add_argument("--recursive", "-r", action="store_true", help="Search subfolders for PDFs")
    args = parser.parse_args()

    try:
        if os.path.isdir(args.input_path):
            process_folder(args.input_path, args.outdir, args.zoom, recursive=args.recursive)
        else:
            merge_and_split_pdf(args.input_path, output_dir=args.outdir, zoom=args.zoom)
    except Exception as e:
        print("❌ Error:", e)
        sys.exit(1)


if __name__ == "__main__":
    main()