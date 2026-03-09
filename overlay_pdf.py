#!/usr/bin/env python3
"""
Composite an overlay PDF on top of a source PDF, page by page.

The overlay PDF contains envelope clear zones (white/opaque areas that mask
source content) and window knockouts (transparent areas that reveal source
content). The source page is rendered first; the overlay is stamped on top.
"""

import argparse
import sys
from pathlib import Path

import fitz  # PyMuPDF


def get_page_count(path):
    """Return the number of pages in a PDF, or None if it cannot be opened."""
    try:
        doc = fitz.open(str(path))
        n = len(doc)
        doc.close()
        return n
    except Exception:
        return None


def validate_inputs(args):
    """Fail-fast validation: file existence, extensions, overlay-page range."""
    if not args.source_pdf.exists():
        print(f"Error: Source file not found: {args.source_pdf}", file=sys.stderr)
        sys.exit(1)

    if not args.overlays_pdf.exists():
        print(f"Error: Overlays file not found: {args.overlays_pdf}", file=sys.stderr)
        sys.exit(1)

    if args.source_pdf.suffix.lower() != '.pdf':
        print(f"Warning: Source file does not have .pdf extension: {args.source_pdf}",
              file=sys.stderr)

    if args.overlays_pdf.suffix.lower() != '.pdf':
        print(f"Warning: Overlays file does not have .pdf extension: {args.overlays_pdf}",
              file=sys.stderr)

    if args.overlay_page < 0:
        print(f"Error: --overlay-page must be non-negative, got {args.overlay_page}",
              file=sys.stderr)
        sys.exit(1)

    overlay_count = get_page_count(args.overlays_pdf)
    if overlay_count is None:
        print(f"Error: Could not open overlays PDF: {args.overlays_pdf}", file=sys.stderr)
        sys.exit(1)

    if args.overlay_page >= overlay_count:
        print(
            f"Error: --overlay-page {args.overlay_page} is out of range; "
            f"overlays PDF has {overlay_count} page(s) (0-indexed max: {overlay_count - 1})",
            file=sys.stderr,
        )
        sys.exit(1)


def determine_output_path(source_path, output_arg):
    """Return output Path: explicit arg or <source_stem>_overlaid.pdf alongside source."""
    if output_arg is not None:
        return output_arg
    return source_path.parent / f"{source_path.stem}_overlaid.pdf"


def overlay_pdfs(source_path, overlays_path, output_path, overlay_page_num, verbose):
    """Composite overlay onto each source page. Returns exit code (0 = success)."""
    src_doc = None
    overlay_doc = None
    out_doc = None

    try:
        src_doc = fitz.open(str(source_path))
        overlay_doc = fitz.open(str(overlays_path))
        out_doc = fitz.open()  # new empty in-memory PDF

        overlay_rect = overlay_doc[overlay_page_num].rect
        total_pages = len(src_doc)

        for page_num in range(total_pages):
            src_page = src_doc[page_num]
            src_rect = src_page.rect
            out_page = out_doc.new_page(width=src_rect.width, height=src_rect.height)

            if verbose:
                if src_rect.width != overlay_rect.width or src_rect.height != overlay_rect.height:
                    print(
                        f"  Warning: page {page_num} size {src_rect.width:.1f}x{src_rect.height:.1f} "
                        f"differs from overlay {overlay_rect.width:.1f}x{overlay_rect.height:.1f}; "
                        f"overlay will be scaled to fit",
                        file=sys.stderr,
                    )
                print(f"  Processing page {page_num + 1}/{total_pages}...")

            # Layer 1: source content (base)
            out_page.show_pdf_page(src_rect, src_doc, page_num)

            # Layer 2: overlay on top (white areas mask source; transparent areas reveal it)
            out_page.show_pdf_page(src_rect, overlay_doc, overlay_page_num)

        out_doc.save(str(output_path))

        if verbose:
            print(f"Saved {total_pages} page(s) to: {output_path}")

        return 0

    except Exception as e:
        print(f"Error during compositing: {e}", file=sys.stderr)
        return 1

    finally:
        for doc in (src_doc, overlay_doc, out_doc):
            if doc is not None:
                try:
                    doc.close()
                except Exception:
                    pass


def main():
    parser = argparse.ArgumentParser(
        description="Composite an overlay PDF on top of a source PDF, page by page.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s source.pdf envelope.pdf
  %(prog)s source.pdf envelope.pdf -o output.pdf -v
  %(prog)s source.pdf envelope.pdf -p 1 -v
        """,
    )

    parser.add_argument('source_pdf', type=Path,
                        help='Source PDF with content to overlay')
    parser.add_argument('overlays_pdf', type=Path,
                        help='Overlays PDF (envelope template with clear zones/knockouts)')
    parser.add_argument('-o', '--output', type=Path, default=None, dest='output',
                        metavar='OUTPUT',
                        help='Output PDF path (default: <source>_overlaid.pdf)')
    parser.add_argument('-p', '--overlay-page', type=int, default=0,
                        metavar='N',
                        help='0-indexed page from overlays PDF to use (default: 0)')
    parser.add_argument('-v', '--verbose', action='store_true',
                        help='Print per-page progress and size-mismatch warnings')

    args = parser.parse_args()

    validate_inputs(args)

    output_path = determine_output_path(args.source_pdf, args.output)

    # Guard against overwriting source
    if output_path.resolve() == args.source_pdf.resolve():
        print(
            "Error: Output path resolves to the same file as source PDF",
            file=sys.stderr,
        )
        sys.exit(1)

    if args.verbose:
        print(f"Source:   {args.source_pdf}")
        print(f"Overlays: {args.overlays_pdf} (page {args.overlay_page})")
        print(f"Output:   {output_path}")

    return overlay_pdfs(
        args.source_pdf,
        args.overlays_pdf,
        output_path,
        args.overlay_page,
        args.verbose,
    )


if __name__ == '__main__':
    sys.exit(main())
