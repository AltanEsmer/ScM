"""Render verified publisher pages and assemble the citation appendix."""
import hashlib
import json
from pathlib import Path
from textwrap import wrap

import pymupdf
import requests
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas

ROOT = Path(__file__).resolve().parents[1]
CACHE = ROOT / 'work/paper-sources'
EVIDENCE = ROOT / 'paper/evidence'
SOURCES = json.loads((EVIDENCE / 'sources.json').read_text())
OUTPUT = ROOT / 'paper/output/citation-appendix.pdf'
OUTPUT.parent.mkdir(parents=True, exist_ok=True)
CACHE.mkdir(parents=True, exist_ok=True)
PDF = canvas.Canvas(str(OUTPUT), pagesize=A4)
PDF.setTitle('Publisher evidence for preliminary prompt sensitivity paper')
PDF.setAuthor('ScM research project')
records = []
for source in SOURCES:
    sid = source['source_id']
    path = CACHE / f'{sid}.pdf'
    if not path.exists():
        response = requests.get(source['publisher_pdf_url'], timeout=90)
        response.raise_for_status()
        path.write_bytes(response.content)
    assert hashlib.sha256(path.read_bytes()).hexdigest() == source['source_pdf_sha256'], sid
    document = pymupdf.open(path)
    page = document[source['pdf_page'] - 1]
    quads = []
    for excerpt in source['highlight_excerpts']:
        matches = page.search_for(excerpt, quads=True)
        assert matches, f'No literal passage match for {sid}: {excerpt}'
        quads.extend(matches)
    assert quads, f'No literal passage match for {sid}'
    annotation = page.add_highlight_annot(quads)
    annotation.set_colors(stroke=(1, 0.88, 0))
    annotation.set_opacity(0.4)
    annotation.update()
    screenshot = EVIDENCE / f'{source["occurrence_id"]}-{sid}-p{source["pdf_page"]}-highlight.png'
    page.get_pixmap(matrix=pymupdf.Matrix(2, 2), alpha=False).save(screenshot)
    width, height = A4
    PDF.setFont('Helvetica-Bold', 12)
    PDF.drawString(28, height - 28, f'[{source["planned_reference_number"]}] {source["occurrence_id"]} / {sid} - publisher passage')
    PDF.setFont('Helvetica', 8)
    y = height - 43
    lines = wrap(source['title'], 115) + [f'Abstract. PDF page {source["pdf_page"]}. Printed page {source["printed_page"]}.'] + wrap(source['publisher_pdf_url'], 110) + wrap('Supports: ' + source['supported_claim'], 110)
    for line in lines:
        PDF.drawString(28, y, line)
        y -= 10
    available_height = y - 30
    scale = min((width - 56) / page.rect.width, available_height / page.rect.height)
    image_width, image_height = page.rect.width * scale, page.rect.height * scale
    PDF.drawImage(str(screenshot), (width - image_width) / 2, 20, width=image_width, height=image_height)
    PDF.showPage()
    records.append({'source_id': sid, 'occurrence_id': source['occurrence_id'], 'screenshot': str(screenshot.relative_to(ROOT / 'paper')), 'screenshot_sha256': hashlib.sha256(screenshot.read_bytes()).hexdigest(), 'highlight_quads': [list(q) for q in (tuple(float(v) for p in quad for v in p) for quad in quads)]})
PDF.save()
(EVIDENCE / 'render-manifest.json').write_text(json.dumps({'renderer': f'PyMuPDF {pymupdf.VersionBind}', 'sources': records, 'appendix_sha256': hashlib.sha256(OUTPUT.read_bytes()).hexdigest()}, indent=2) + '\n')
print(f'{len(records)} highlighted publisher screenshots; {OUTPUT}')
