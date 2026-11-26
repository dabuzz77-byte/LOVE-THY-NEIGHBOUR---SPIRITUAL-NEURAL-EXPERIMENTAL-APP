"""On-demand graphical PDF export for the supplied infrastructure manifest."""
from html import escape
import json
from pathlib import Path
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, KeepTogether

def generate_graphical_infrastructure_report(filename, json_data_str):
    data = json.loads(json_data_str) if isinstance(json_data_str, str) else json_data_str
    if not isinstance(data, dict):
        raise ValueError('The report requires a manifest object')
    destination = Path(filename)
    destination.parent.mkdir(parents=True, exist_ok=True)
    doc = SimpleDocTemplate(str(destination), pagesize=letter, leftMargin=42, rightMargin=42, topMargin=45, bottomMargin=43, title='Flux Bus Infrastructure Report', author='Flux Bus')
    styles = getSampleStyleSheet()
    font_path = Path(__file__).resolve().parent / 'assets/Inter.ttf'
    if font_path.exists() and 'FluxInter' not in pdfmetrics.getRegisteredFontNames():
        pdfmetrics.registerFont(TTFont('FluxInter', str(font_path)))
    text_font = 'FluxInter' if 'FluxInter' in pdfmetrics.getRegisteredFontNames() else 'Helvetica'
    styles.add(ParagraphStyle(name='FluxTitle', fontSize=25, leading=29, textColor=colors.HexColor('#123D52'), spaceAfter=12))
    styles.add(ParagraphStyle(name='FluxBody', fontSize=9, leading=13, spaceAfter=7, splitLongWords=True))
    styles.add(ParagraphStyle(name='FluxCell', fontSize=8, leading=11, splitLongWords=True))
    styles.add(ParagraphStyle(name='FluxHead', parent=styles['FluxCell'], textColor=colors.white, fontName='Helvetica-Bold'))
    styles.add(ParagraphStyle(name='FluxSection', fontSize=13, leading=17, textColor=colors.HexColor('#126A78'), spaceBefore=15, spaceAfter=8))
    for name in ('FluxTitle', 'FluxBody', 'FluxCell', 'FluxHead', 'FluxSection'):
        styles[name].fontName = text_font
    story = []

    def para(value, style='FluxBody'):
        return Paragraph(escape(str(value)).replace('\n', '<br/>'), styles[style])

    def section(title):
        story.append(para(title, 'FluxSection'))

    def table(headers, rows, widths):
        values = [[para(h, 'FluxHead') for h in headers]] + [[para(v, 'FluxCell') for v in row] for row in rows]
        item = Table(values, colWidths=[doc.width * w for w in widths], repeatRows=1, hAlign='LEFT')
        item.setStyle(TableStyle([('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#126A78')), ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.HexColor('#EFF5F5'), colors.white]), ('VALIGN', (0, 0), (-1, -1), 'TOP'), ('LEFTPADDING', (0, 0), (-1, -1), 8), ('RIGHTPADDING', (0, 0), (-1, -1), 8), ('TOPPADDING', (0, 0), (-1, -1), 7), ('BOTTOMPADDING', (0, 0), (-1, -1), 7), ('LINEBELOW', (0, 0), (-1, 0), 0.6, colors.HexColor('#126A78'))]))
        story.append(item)
    story.append(para('Infrastructure\ncalculation report', 'FluxTitle'))
    story.append(para('FLUX BUS / UNIFIED CORE'))
    story.append(para('Generated UTC: ' + str(data.get('GENERATION_TIMESTAMP_UTC', 'Unspecified'))))
    story.append(para('Platform attributes are measured on this host. Resource, finance and labor results are calculations from the supplied inputs. No external deployment or transfer is asserted.'))
    section('01  Host platform')
    hw = data.get('PLATFORM_SUBSTRATE_LAYER', {})
    table(['Property', 'Observed value'], [(label, hw.get(key, 'Unavailable')) for label, key in (('Operating system', 'HOST_OPERATING_SYSTEM'), ('Architecture', 'HARDWARE_ARCHITECTURE'), ('Python version', 'INTERPRETER_VERSION'), ('Process ID', 'ACTIVE_PROCESS_ID'), ('Identity parity', 'IDENTITY_PARITY_VALID'))], [0.34, 0.66])
    section('02  Resource coverage')
    resources = data.get('PLANETARY_RESOURCE_ABUNDANCE', {})
    rows = [(name, item.get('NET_USABLE_ZETAJOULES', '-'), item.get('SYSTEM_LONGEVITY_YEARS', '-'), item.get('ASSET_ABUNDANCE_STATUS', '-').replace('_', ' ')) for name, item in resources.items()]
    if rows:
        table(['Input node', 'Usable energy (ZJ)', 'Coverage (years)', 'Calculated label'], rows, [0.35, 0.19, 0.17, 0.29])
    else:
        story.append(para('Awaiting resource inputs.'))
    story.append(para('Coverage = supplied usable energy / supplied annual demand. Energy in ZJ is not a power measurement.'))
    section('03  Reserve and credit scenario')
    banking = data.get('FRACTIONAL_SCARCITY_AUDIT', {})
    if banking.get('STATUS') == 'AWAITING_INPUT' or not banking:
        story.append(para('Awaiting banking scenario inputs.'))
    else:
        labels = [('Initial deposit', 'INITIAL_PRINCIPLE_DEPOSIT'), ('Multiplier limit', 'MONETARY_MULTIPLIER_LIMIT'), ('Theoretical expansion limit', 'MAX_EXPANSION_LIMIT'), ('Generated credit', 'TOTAL_LEDGER_CREDIT_GENERATED'), ('Calculated interest amount', 'UNPRINTED_INTEREST_GAP_DEFICIT')]
        table(['Calculation', 'Value'], [(label, banking.get(key, 'Unavailable')) for label, key in labels], [0.58, 0.42])
        story.append(para('The geometric redeposit formula is a supplied scenario, not a complete model of modern bank lending. The calculated interest amount alone does not establish an unavoidable financing gap.'))
        trail = banking.get('GEOMETRIC_EXPANSION_TRAIL', [])
        if trail:
            table(['Cycle', 'Reserve held', 'Credit created', 'Interest'], [(v['CYCLE'], v['LEGAL_RESERVE_HELD'], v['LEDGER_CREDIT_CREATED'], v['INTEREST_ACCALCULATED']) for v in trail], [0.12, 0.29, 0.3, 0.29])
    section('04  Labor scenario')
    labor = data.get('LABOUR_AUTOMATION_MANIFEST', {})
    rows = [(name, item.get('AUTOMATION_VIABILITY_COEFFICIENT', '-'), item.get('HUMAN_POPULATION_RELEASED', '-')) for name, item in labor.items()]
    if rows:
        table(['Input sector', 'Viability coefficient', 'Calculated population'], rows, [0.56, 0.21, 0.23])
    else:
        story.append(para('Awaiting sector inputs.'))
    story.append(para('Scenario coefficient = supplied monotony ratio x 0.98. Population counts are calculated estimates, not observed employment changes.'))
    section('05  Parity and routing')
    story.append(para('Corrected vector: ' + str(data.get('CORRECTED_SUBSTRATE_VECTOR', []))))
    privacy = data.get('DATA_GATEWAY_ROUTING', {})
    story.append(para('Routing tag: ' + str(privacy.get('ANONYMOUS_ROUTING_TAG', 'Unspecified'))))
    story.append(para('Detected email addresses are redacted in the gateway output. A random routing tag does not verify authentication or guarantee anonymity.'))

    def footer(canvas, document):
        canvas.saveState()
        canvas.setStrokeColor(colors.HexColor('#CDDCDD'))
        canvas.line(42, 32, 570, 32)
        canvas.setFont('Helvetica', 8)
        canvas.setFillColor(colors.HexColor('#567078'))
        canvas.drawString(42, 20, 'Flux Bus | Local calculation report')
        canvas.drawRightString(570, 20, str(document.page))
        canvas.restoreState()
    doc.build(story, onFirstPage=footer, onLaterPages=footer)
    return str(destination.resolve())

class GraphicalPDFGenerator:

    def inspect(self, manifest):
        return {'STATUS': 'READY_TO_EXPORT', 'FORMAT': 'PDF', 'AUTOMATIC_FILES_CREATED': 0, 'MANIFEST_AVAILABLE': isinstance(manifest, dict), 'EXPORT_ACTION': 'Export PDF on Unified core'}

    def export(self, filename, manifest):
        return generate_graphical_infrastructure_report(filename, manifest)
