"""Assemble generated slides with the installed skill, retaining the named template."""
from pathlib import Path
import hashlib
import json
import shutil
import subprocess
import sys
import zipfile

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
SKILL = Path('/home/shaan/.codex/skills/codex-ppt')
sys.path.insert(0, str(SKILL / 'scripts'))
import assemble_ppt
import pptx
from lxml import etree
from pptx.enum.shapes import MSO_SHAPE_TYPE

def digest(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()

def main():
    jobs = json.loads((HERE / 'slide_jobs.json').read_text())
    assert len(jobs['slides']) == 24
    assert all(s['status'] in ['recorded', 'accepted'] for s in jobs['slides'])
    assert all(s['status'] == 'accepted' or
               s['result']['backend_used'] == 'built-in image tool' for s in jobs['slides'])
    reference = HERE / 'assets/reference.pptx'
    retained = Path('/home/shaan/.codex/plugins/cache/openai-curated-remote/openai-templates/0.1.1/skills/artifact-template-simple-light-mode/assets/reference.pptx')
    assert digest(reference) == digest(retained)
    original_presentation = pptx.Presentation
    template = original_presentation(reference)
    original_width, original_height = template.slide_width, template.slide_height

    def load_template(*args, **kwargs):
        # Import the retained template; remove only its example slide contents.
        # Masters, layouts, theme and font definitions stay in the package.
        imported = original_presentation(reference)
        for slide_id in list(imported.slides._sldIdLst):
            imported.part.drop_rel(slide_id.rId)
            imported.slides._sldIdLst.remove(slide_id)
        imported.core_properties.title = 'Budgeted OpenMP Scheduling Selection — Group 3'
        imported.core_properties.author = 'Shaan Chopra; Mrinal Dhami; Aniket Verma'
        imported.core_properties.subject = 'Plain-language explanation of time, CPU and scheduling-quality trade-offs'
        return imported

    images = assemble_ppt.get_slide_images(str(HERE))
    assert len(images) == 24
    notes = assemble_ppt.load_speaker_notes(str(HERE))
    assert set(notes) == set(range(1, 25))
    output = HERE / 'PCAP_PRESENTATION_G3.pptx'
    # Keep the tool-generated images lossless instead of the optional JPEG compression.
    assemble_ppt.compress_image_if_needed = lambda *args, **kwargs: None
    pptx.Presentation = load_template
    try:
        assert assemble_ppt.create_presentation(images, str(output), '16:9', notes)
    finally:
        pptx.Presentation = original_presentation

    # Restore the reference's exact canvas dimensions and clear unused placeholders.
    final = original_presentation(output)
    final.slide_width, final.slide_height = original_width, original_height
    spec = json.loads((HERE / 'deck_spec.json').read_text())
    for slide, content in zip(final.slides, spec['slides']):
        for shape in list(slide.shapes):
            if shape.shape_type != MSO_SHAPE_TYPE.PICTURE:
                element = shape._element
                element.getparent().remove(element)
            else:
                shape.left = shape.top = 0
                shape.width, shape.height = original_width, original_height
                shape.name = content['title']
                shape._element.nvPicPr.cNvPr.set('descr', content['title']+'\n'+'\n'.join(content['key_points']))
    final.save(output)
    with zipfile.ZipFile(reference) as source, zipfile.ZipFile(output) as bundle:
        unchanged = [n for n in source.namelist() if
                     n.startswith(('ppt/theme/', 'ppt/slideMasters/', 'ppt/slideLayouts/'))
                     and n.endswith('.xml')]
        # XML declaration quote style can change during packaging; compare contents.
        canonical = lambda data: etree.tostring(etree.fromstring(data), method='c14n')
        assert all(canonical(source.read(n)) == canonical(bundle.read(n)) for n in unchanged)
        assert bundle.testzip() is None
    reopened = original_presentation(output)
    for i, (slide, image) in enumerate(zip(reopened.slides, images), 1):
        assert len(slide.shapes) == 1
        assert hashlib.sha256(slide.shapes[0].image.blob).hexdigest() == digest(image)
        assert slide.notes_slide.notes_text_frame.text.strip() == notes[i].strip()
    assert len(reopened.slides) == 24

    # Plain pdfTeX embeds the original slide images at exact 16:9 page size.
    build = ROOT / 'build/presentation'
    build.mkdir(parents=True, exist_ok=True)
    tex = build / 'PCAP_PRESENTATION_G3.tex'
    lines = [r'\pdfpagewidth=13.333333in', r'\pdfpageheight=7.5in',
             r'\pdfhorigin=0pt', r'\pdfvorigin=0pt', r'\nopagenumbers',
             r'\pdfinfo{/Title (Budgeted OpenMP Scheduling Selection - Group 3)}']
    for image in images:
        lines += [r'\pdfximage width\pdfpagewidth height\pdfpageheight {'+str(Path(image).resolve())+'}',
                  r'\shipout\hbox{\pdfrefximage\pdflastximage}']
    lines.append(r'\end')
    tex.write_text('\n'.join(lines)+'\n')
    run = subprocess.run(['pdftex', '-interaction=nonstopmode', '-halt-on-error',
                          '-output-directory='+str(build), str(tex)],
                         cwd=ROOT, capture_output=True, text=True)
    (build / 'compile.txt').write_text(run.stdout+run.stderr)
    assert run.returncode == 0, run.stdout[-2000:]
    pdf = build / 'PCAP_PRESENTATION_G3.pdf'
    shutil.copy2(pdf, HERE / pdf.name)
    deliverables = ROOT / 'deliverables/current'
    shutil.copy2(output, deliverables / output.name)
    shutil.copy2(pdf, deliverables / pdf.name)
    shutil.copy2(HERE / 'speech.md', deliverables / 'PCAP_PRESENTATION_NOTES_G3.md')

    report = {'slides': 24, 'speaker_notes_verified': 24,
              'images_generated_with': 'built-in image tool',
              'all_non_sample_results_recorded': True,
              'template_reference_unchanged': True,
              'template_theme_master_layout_xml_preserved': len(unchanged),
              'slide_geometry_matches_template': [original_width, original_height],
              'embedded_images_match_original_backend_bytes': True,
              'pptx_zip_integrity_passed': True,
              'pptx_sha256': digest(output), 'pdf_sha256': digest(pdf),
              'reference_sha256': digest(reference),
              'notes_sha256': digest(HERE/'speech.md'),
              'image_hashes': {Path(p).name: digest(p) for p in images}}
    (HERE / 'qa_report.json').write_text(json.dumps(report, indent=2)+'\n')
    print(json.dumps(report, indent=2))

if __name__ == '__main__':
    main()
