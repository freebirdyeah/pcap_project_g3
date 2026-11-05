# Group 3 presentation

This presentation explains the current scheduling cost–quality study in plain
language. It follows the approved 24-slide outline and Simple Light Mode
reference, with the user's requested minimal typography and no slide numbers.

- `PCAP_PRESENTATION_G3.pptx`: final PowerPoint, with speaker notes.
- `PCAP_PRESENTATION_G3.pdf`: same slides for viewing and sharing.
- `speech.md`: the full talk track, also embedded in the PowerPoint notes.
- `outline.md`: the approved slide content and order.
- `origin_image/`: final slide images, generated with the built-in image tool.
- `assets/reference.pptx`: unchanged copy of the retained template.
- `assets/chart_*.png`: charts plotted from the audited result reports.
- `assets/chart_data.json`: source hashes and plotted values.
- `deck_spec.json`, `prompts/`, `slide_jobs.json`, `slide_run_state.json`: generation
  instructions and recorded provenance.
- `qa_report.json`: final assembly and integrity checks.

The slides are full-slide images. Speaker notes and slide metadata are editable;
individual visible text, equations, and chart objects are not separately
editable. The template's masters, layouts, theme, and exact canvas geometry are
retained in the final PowerPoint. The original template file is unchanged.

`assemble_from_template.py` uses the installed Codex PPT assembler with the
retained reference, validates the generated images and notes, exports a PDF,
and copies the deliverables into the project's `deliverables/current/` folder.
It must run only after every slide has been recorded or accepted.

The user approved the outline and waived the remaining confirmation steps with
“go ahead”. The sample was checked visually before it was used for other slides.
No new research measurements were made for the presentation.
