"""Prepare audited chart inputs and self-contained slide-generation jobs."""
from pathlib import Path
import hashlib
import json
import re
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
ASSETS = HERE / 'assets'
REPORT = json.loads((ROOT / 'tradeoff/results/report.json').read_text())
INSITU = json.loads((ROOT / 'tradeoff/results/insitu_report.json').read_text())
plt.rcParams.update({'font.family': 'DejaVu Sans', 'font.size': 20,
                     'axes.spines.top': False, 'axes.spines.right': False,
                     'axes.spines.left': False, 'axes.spines.bottom': False,
                     'figure.facecolor': 'white', 'axes.facecolor': 'white',
                     'savefig.facecolor': 'white'})

def match(rows, policy, horizon=None):
    return next(r for r in rows if r['policy'] == policy and
                (horizon is None or r['horizon'] == horizon))

chart_data = {}

def bars(number, labels, values, units, limit, fmt, baseline=None):
    fig, ax = plt.subplots(figsize=(12, 3.8))
    colors = ['#aaaaaa'] * len(values)
    colors[-1] = '#202020'
    positions = list(range(len(values)))
    ax.barh(positions, values, height=.40, color=colors)
    ax.set_yticks(positions, labels)
    ax.tick_params(axis='both', length=0, pad=12)
    ax.invert_yaxis()
    ax.set_xlim(0, limit)
    ax.set_xticks([])
    ax.set_xlabel(units, labelpad=15, color='#444444')
    if baseline is not None:
        ax.axvline(baseline, color='#777777', linestyle='--', linewidth=1.2)
    for i, v in enumerate(values):
        ax.text(v + limit * .025, i, fmt.format(v), va='center', fontsize=23)
    fig.subplots_adjust(left=.22, right=.87, top=.93, bottom=.23)
    path = ASSETS / f'chart_{number:02d}.png'
    fig.savefig(path, dpi=180, bbox_inches='tight', pad_inches=.12)
    plt.close(fig)
    chart_data[str(number)] = {'labels': labels, 'values': values, 'units': units,
                               'figure': str(path.relative_to(HERE))}

def main():
    ASSETS.mkdir(exist_ok=True)
    selection = match(REPORT['selection'], 'budget4')
    quality = match(REPORT['quality'], 'budget4')
    bars(7, ['Full 12', 'Guided 4'], [36, 12], 'Test executions', 42, '{:.0f}')
    bars(15, ['Within 5%', 'Within 10%'],
         [100 * quality['within5'], 100 * quality['within10']],
         'Share of runs near the independent reference', 82, '{:.1f}%')
    bars(16, ['Elapsed time saved', 'CPU time saved'],
         [selection['wall_saved_pct'], selection['cpu_saved_pct']],
         'Saving during scheduler selection', 83, '{:.1f}%')
    ratio50 = match(REPORT['deployment'], 'budget4', 50)['wall_speedup']
    bars(17, ['Full 12', 'Guided 4'], [100, 100 / ratio50],
         'Relative complete cost (Full 12 = 100)', 120, '{:.1f}')
    horizons = [10, 50, 100, 500]
    savings = [100 * (1 - 1 / match(REPORT['deployment'], 'budget4', h)['wall_speedup'])
               for h in horizons]
    fig, ax = plt.subplots(figsize=(12, 3.8))
    ax.plot(range(4), savings, '-o', color='#202020', linewidth=2.5, markersize=8)
    ax.set_xticks(range(4), [str(h) for h in horizons])
    ax.set_ylim(0, 65)
    ax.set_yticks([0, 20, 40, 60], ['0%', '20%', '40%', '60%'])
    ax.set_xlabel('Useful executions after extra testing', labelpad=10)
    ax.tick_params(length=0, pad=8)
    for i, v in enumerate(savings):
        ax.text(i, v + 4, f'{v:.1f}%', ha='center', fontsize=21)
    ax.grid(axis='y', color='#eeeeee')
    fig.subplots_adjust(left=.10, right=.93, bottom=.25, top=.90)
    fig.savefig(ASSETS / 'chart_18.png', dpi=180)
    plt.close(fig)
    chart_data['18'] = {'useful_executions': horizons, 'elapsed_saving_pct': savings,
                        'figure': 'assets/chart_18.png'}
    # Read the secondary report's own values rather than reconstructing its results.
    candidates = INSITU.get('comparisons', INSITU.get('results', []))
    if not candidates:
        candidates = next(v for v in INSITU.values() if isinstance(v, list)
                          and v and isinstance(v[0], dict) and 'policy' in v[0])
    secondary = [match(candidates, 'budget4', h) for h in [50, 500]]
    key = next(k for k in ['wall_speedup', 'wall_ratio'] if k in secondary[0])
    vals = [r[key] for r in secondary]
    fig, ax = plt.subplots(figsize=(12, 3.8))
    ax.axhline(1, color='#999999', linestyle='--', linewidth=1.5)
    ax.plot([0, 1], vals, 'o', color='#202020', markersize=11)
    ax.set_xticks([0, 1], ['50 useful runs', '500 useful runs'])
    ax.set_xlim(-.4, 1.4)
    ax.set_ylim(.93, 1.045)
    ax.set_yticks([.95, 1, 1.04], ['0.95', '1.00', '1.04'])
    ax.tick_params(length=0, pad=10)
    ax.set_xlabel('Full 12 cost / Guided 4 cost; above 1 favors Guided 4', labelpad=12)
    for i, v in enumerate(vals):
        ax.text(i, v + .007, f'{v:.3f}', ha='center', fontsize=24)
    fig.subplots_adjust(left=.10, right=.95, top=.92, bottom=.25)
    fig.savefig(ASSETS / 'chart_21.png', dpi=180)
    plt.close(fig)
    chart_data['21'] = {'useful_executions': [50, 500], 'wall_ratio': vals,
                        'figure': 'assets/chart_21.png'}
    policies = ['budget4', 'random4', 'bestfixed']
    ratios = [match(REPORT['deployment'], p, 50)['wall_speedup'] for p in policies]
    bars(22, ['Guided 4', 'Random 4', 'Best fixed'], ratios,
         'Full 12 cost / method cost; above 1 favors the method', 2.05, '{:.3f}', baseline=1)
    sources = {str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest()
               for p in [ROOT/'tradeoff/results/report.json',
                         ROOT/'tradeoff/results/insitu_report.json']}
    (ASSETS / 'chart_data.json').write_text(json.dumps({'sources': sources, 'charts': chart_data}, indent=2)+'\n')

    outline = (HERE / 'outline.md').read_text()
    parts = re.findall(r'^## Slide (\d+) — ([^\n]+)\n(.*?)(?=^## Slide |^## Production requirements)',
                       outline, re.M | re.S)
    assert len(parts) == 24
    slides = []
    for number, title, content in parts:
        number = int(number)
        bullets_text = content.split('Visible bullets:\n', 1)[1].split('\n\n', 1)[0]
        bullets = [s[2:] for s in bullets_text.splitlines() if s.startswith('- ')]
        assert len(bullets) == 3
        slide = {
            'number': number, 'title': title.strip(), 'role': 'technical explainer',
            'intent': 'One simple understandable claim; retain the approved research facts.',
            'key_points': bullets,
            'local_context': {'approved_content_and_visual_instructions': content.strip()},
            'layout': {'composition': 'One bold top-left heading, three left-aligned bullets; center the equation, diagram or chart below; one small pale reminder box near the bottom when requested.',
                       'spacing': 'Keep each bullet to one or two lines; heading 42–46pt, body 25–28pt at widescreen slide scale. No upper label or footer.'},
            'visual_elements': {'main_visual': content.split('\n\n', 2)[-1].strip()},
            'constraints': ['English only. Do not display the slide number or any meta instructions.',
                            'White background, black sans-serif type, no decorative imagery or logos.',
                            'Use the title and three bullets exactly as provided; do not add facts.',
                            'The notes in local_context are explanatory instructions, not additional slide text.',
                            'Render centered equations carefully, with true fractions and subscripts.',
                            'Do not show outline labels such as Role, Reminder box, Source, or Visible bullets.'],
        }
        if number in [7, 15, 16, 17, 18, 21, 22]:
            slide['required_images'] = [{'path': str(ASSETS / f'chart_{number:02d}.png'),
                                          'role': 'strict input asset; audited chart, use as centered main figure',
                                          'fidelity': 'Preserve all data, labels, bar lengths, directions, axis scales and numeric values. Embed this supplied chart; do not synthesize a replacement.'}]
        if number == 13:
            slide['sample_approved'] = True
            slide['use_approved_style_reference'] = False
        slides.append(slide)
    sample = str(HERE / 'origin_image/slide_13.png')
    spec = {
        'deck_name': HERE.name, 'language': 'English', 'goal': 'Explain this OpenMP scheduling paper to undergraduates and an unfamiliar professor, with minimal slides and patient notes.',
        'selected_image_backend': 'built-in image tool', 'max_concurrent_slides': 3,
        'approval': {'outline_approved': True, 'remaining_confirmation_steps_waived': True,
                     'evidence': 'User replied go ahead to approval of the outline and skipping further confirmation steps.'},
        'template_reference': str(ASSETS / 'reference.pptx'),
        'deck_context': {'source_summary': 'We compare 12-candidate scheduling search with a training-guided four-candidate shortlist on one four-core WSL2 machine. Guided 4 saves 65.0% tuning wall time and 65.9% tuning CPU time. At 50 useful loops after EXTRA calibration and with a CACHED model, total elapsed saving is about 27.5%. No clear benefit when exploratory executions already perform useful work.',
                         'core_claim': 'Count both choosing cost and useful execution cost, including a share of training. Benefits are conditional; model ranking is not proven necessary.',
                         'canonical_terms': ['scheduler = rule distributing loop iterations to threads', 'arm = scheduler option', 'prior = previously trained model', 'payload = useful execution after commitment', 'Full 12 is a finite noisy search, not a true optimum']},
        'style': {'name': 'Simple Light Mode — minimal professional adaptation',
                  'visual_direction': 'Import the clean white Helvetica Neue visual identity of the retained reference. Match the accepted sample. The user explicitly removes supertitles, numbers, decoration and elaborate frames.',
                  'color_palette': 'Pure white background; black text; restrained gray chart bars and occasional pale gray reminder box.',
                  'typography': 'Large bold Helvetica Neue-style sans-serif title at the same top-left position; left-aligned professional sans-serif body. Center only equations and charts.',
                  'texture_and_finish': 'Flat plain professional presentation; no shadows, illustrations, gradients, ornamental lines, logos, slide numbers, page borders or footer.'},
        'approved_style_reference': {'path': sample, 'role': 'Accepted sample slide style reference', 'fidelity': 'Use only the typography, palette, spacing and visual identity, not its title or content.'},
        'sample_generation_method': {'backend_used': 'built-in image tool', 'tool_name': 'image_gen__imagegen',
                                     'mode': 'edit', 'model/config': 'built-in default; exact model not exposed',
                                     'prompt_source': 'Cost-equation sample prompt in the parent conversation',
                                     'approved_sample_path': sample,
                                     'input_context_preparation': 'Inspect every local reference image with view_image, then pass referenced_image_paths to the same built-in tool.',
                                     'handoff_rule': 'Use this exact backend and edit mode. Return a blocker if unavailable. Save the original tool-generated bytes, without drawing or overlays.'},
        'slides': slides,
    }
    (HERE / 'deck_spec.json').write_text(json.dumps(spec, ensure_ascii=False, indent=2)+'\n')
    print('Prepared eight audited chart inputs and the 24-slide specification.')

if __name__ == '__main__':
    main()
