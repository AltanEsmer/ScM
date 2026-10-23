"""Annotate the captured first-party dataset record for citation C11."""
import pathlib,json,hashlib
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from textwrap import wrap
from PIL import Image
root=pathlib.Path(__file__).resolve().parents[1]
source=root/'paper/evidence/C11-S11-dataset-card.png'
out=root/'paper/evidence/dataset-evidence.pdf'
im=Image.open(source);w,h=im.size
c=canvas.Canvas(str(out),pagesize=A4);pw,ph=A4
c.setTitle('Dataset record evidence, C11 / S11')
lines=['[11] C11 / S11 - official dataset record','BAAI/TACO, pinned Hugging Face dataset card','Not a peer-reviewed paper; additional dataset attribution.','Accessed 23 October 2026. Browser screenshot, highlighted description.']
url='https://huggingface.co/datasets/BAAI/TACO/blob/d593ed0a2becbbc952230bb89be09189bf1056dc/README.md'
lines+=wrap(url,105)+wrap('Supports: The official dataset record describes code generation from natural-language specifications.',105)
y=ph-28
for i,line in enumerate(lines):
 c.setFont('Helvetica-Bold' if i==0 else 'Helvetica',11 if i==0 else 8);c.drawString(28,y,line);y-=13
scale=min((pw-56)/w,(y-35)/h);iw,ih=w*scale,h*scale;ix=(pw-iw)/2;iy=20
c.drawImage(str(source),ix,iy,width=iw,height=ih)
c.saveState();c.setFillColorRGB(1,0.88,0);c.setFillAlpha(0.20)
c.rect(ix+30*scale,iy+(h-480)*scale,390*scale,112*scale,fill=1,stroke=0);c.restoreState();c.save()
record=dict(source_id='S11',occurrence_id='C11',reference_number=11,bibkey='taco-dataset',source_type='first-party dataset record, not peer-reviewed',publisher_url=url,accessed_utc='2026-10-23',screenshot_sha256=hashlib.sha256(source.read_bytes()).hexdigest(),evidence_pdf_sha256=hashlib.sha256(out.read_bytes()).hexdigest(),highlight_pixel_rectangle=[30,368,420,480],supported_claim='The official dataset record describes code generation from natural-language specifications.')
(root/'paper/evidence/dataset-record.json').write_text(json.dumps(record,indent=2)+'\n')
