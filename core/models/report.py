import os
from datetime import date, timedelta

from fpdf import FPDF

from core.database import get_conn

FONT_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'fonts')
EN_REG = os.path.join(FONT_DIR, 'NotoSans-Regular.ttf')
EN_BOLD = os.path.join(FONT_DIR, 'NotoSans-Bold.ttf')

EN_MONTHS = ['January', 'February', 'March', 'April', 'May', 'June', 'July',
             'August', 'September', 'October', 'November', 'December']

APP_NAME_EN = 'Sri Lakshmi Venkateshwara Finance'

ORANGE = (234, 88, 12)
DARK = (30, 27, 46)
GRAY = (100, 108, 128)
LIGHT_ROW = (255, 244, 230)


def inr(amount):
    try:
        amount = float(amount or 0)
    except (TypeError, ValueError):
        amount = 0.0
    amount = round(amount, 2)
    sign = '-'
    if amount < 0:
        amount = -amount
    else:
        sign = ''
    whole = int(amount)
    frac = f'{amount:.2f}'.split('.')[1]
    s = str(whole)
    if len(s) > 3:
        head, tail = s[:-3], s[-3:]
        groups = []
        while head:
            groups.insert(0, head[-2:])
            head = head[:-2]
        s = ','.join(groups) + ',' + tail
    return f'{sign}₹{s}.{frac}'


def fmt_date(d):
    if not d:
        return ''
    try:
        dt = date.fromisoformat(str(d)[:10])
    except ValueError:
        return str(d)[:10]
    return f'{dt.day:02d} {EN_MONTHS[dt.month - 1]} {dt.year}'


def get_report_data(from_date: str, to_date: str) -> dict:
    f, t = from_date, to_date
    conn = get_conn()
    cur = conn.cursor()

    cur.execute('''SELECT m.member_id, m.name,
        COALESCE(SUM(p.share_amount),0) s, COALESCE(SUM(p.loan_principal),0) pr,
        COALESCE(SUM(p.loan_interest),0) i, COALESCE(SUM(p.fine),0) fn
        FROM member_ledger p JOIN members m ON m.member_id=p.member_id
        WHERE substr(p.pay_date,1,10)>=? AND substr(p.pay_date,1,10)<=?
        GROUP BY m.member_id ORDER BY m.name''', (f, t))
    contrib_rows = [dict(r) for r in cur.fetchall()]
    contributions = [r for r in contrib_rows if (r['s'] or r['pr'] or r['i'] or r['fn']) > 0]
    contrib_total = {
        's': sum(r['s'] for r in contributions),
        'pr': sum(r['pr'] for r in contributions),
        'i': sum(r['i'] for r in contributions),
        'fn': sum(r['fn'] for r in contributions),
        'total': sum(r['s'] + r['pr'] + r['i'] + r['fn'] for r in contributions),
    }

    cur.execute('SELECT COUNT(*) c FROM members')
    member_count = cur.fetchone()['c']

    cur.execute('''SELECT m.name FROM loans l JOIN members m ON m.member_id=l.member_id
        WHERE l.disbursed_date IS NOT NULL AND substr(l.disbursed_date,1,10)>=? AND substr(l.disbursed_date,1,10)<=?
        ORDER BY l.disbursed_date''', (f, t))
    new_loans = [dict(r) for r in cur.fetchall()]

    cur.execute('''SELECT substr(timestamp,1,10) d, description, amount
        FROM group_ledger WHERE member_id IS NULL AND debit_credit='credit'
        AND substr(timestamp,1,10)>=? AND substr(timestamp,1,10)<=?
        ORDER BY timestamp''', (f, t))
    income = [dict(r) for r in cur.fetchall()]

    cur.execute('''SELECT notes, amount FROM fixed_deposits
        WHERE status='active' AND investment_type!='monthly'
        AND start_date IS NOT NULL AND substr(start_date,1,10)<=?
        ORDER BY start_date''', (t,))
    hardlock_active = [dict(r) for r in cur.fetchall()]
    conn.close()

    try:
        last_day = (date(int(f[:4]), int(f[5:7]) + 1, 1) - timedelta(days=1)).day
    except ValueError:
        last_day = 31
    is_monthly = f == f'{f[:4]}-{f[5:7]}-01' and t == f'{f[:4]}-{f[5:7]}-{last_day:02d}'

    return {
        'from': f,
        'to': t,
        'is_monthly': is_monthly,
        'period_label': f'{fmt_date(f)} - {fmt_date(t)}',
        'generated_on': fmt_date(date.today().isoformat()),
        'monthly_title': EN_MONTHS[int(f[5:7]) - 1] + ' ' + f[:4],
        'contributions': {'rows': contributions, 'totals': contrib_total, 'count': len(contributions), 'member_count': member_count},
        'new_loans': {'rows': new_loans},
        'income': {'rows': income},
        'hardlock_active': hardlock_active,
    }


class _ReportPDF(FPDF):
    def footer(self):
        self.set_y(-12)
        self.set_font('EN', '', 8)
        self.set_text_color(*GRAY)
        self.cell(0, 8, f'Page {self.page_no()}', align='C')


def _load_fonts(pdf):
    pdf.add_font('EN', '', EN_REG)
    pdf.add_font('EN', 'B', EN_BOLD)


def _table(pdf, widths, headers, rows, fonts, aligns, size=9, bold_rows=(), header_font=None, page_break=True):
    total = sum(widths)
    x0 = (210 - total) / 2
    row_h = 6.2
    header_h = 7
    margin_bottom = 14

    def draw_header():
        if not headers:
            return
        pdf.set_font(header_font or fonts[0], 'B', size)
        pdf.set_fill_color(*ORANGE)
        pdf.set_text_color(255, 255, 255)
        x = x0
        for i, h in enumerate(headers):
            pdf.set_xy(x, pdf.get_y())
            pdf.cell(widths[i], header_h, h, border=0, align='C', fill=True)
            x += widths[i]
        pdf.ln(header_h)
        pdf.set_text_color(*DARK)

    draw_header()
    for ri, row in enumerate(rows):
        if page_break and pdf.get_y() + row_h > 297 - margin_bottom:
            pdf.add_page()
            draw_header()
        pdf.set_x(x0)
        bold = ri in bold_rows
        fill = LIGHT_ROW if ri % 2 == 1 else False
        x = x0
        for ci, val in enumerate(row):
            font = fonts[ci]
            style = 'B' if bold else ''
            pdf.set_font(font, style, size)
            if fill:
                pdf.set_fill_color(*LIGHT_ROW)
                pdf.cell(widths[ci], row_h, str(val), border=0, align=aligns[ci], fill=True)
            else:
                pdf.cell(widths[ci], row_h, str(val), border=0, align=aligns[ci])
            x += widths[ci]
        pdf.ln(row_h)


def _heading(pdf, num, text):
    pdf.ln(2)
    if pdf.get_y() > 250:
        pdf.add_page()
    pdf.set_font('EN', 'B', 11.5)
    pdf.set_text_color(*ORANGE)
    pdf.cell(0, 7, f'{num}. {text}')
    pdf.ln(8)


def _empty(pdf, text):
    pdf.set_font('EN', '', 9)
    pdf.set_text_color(*GRAY)
    pdf.cell(0, 6, text)
    pdf.ln(7)


def _draw_page(pdf, data):
    if data['is_monthly']:
        title = f'{data["monthly_title"]} - Monthly Summary'
    else:
        title = 'Summary Report'
    title_sub = f'Period: {data["period_label"]}'

    pdf.add_page()
    pdf.set_font('EN', 'B', 16)
    pdf.set_text_color(*ORANGE)
    pdf.cell(0, 9, APP_NAME_EN, align='C')
    pdf.ln(10)
    pdf.set_draw_color(*ORANGE)
    pdf.set_line_width(0.5)
    pdf.line(14, pdf.get_y(), 196, pdf.get_y())
    pdf.ln(6)
    pdf.set_font('EN', 'B', 12.5)
    pdf.set_text_color(*DARK)
    pdf.cell(0, 7, title, align='C')
    pdf.ln(8)
    pdf.set_font('EN', '', 9)
    pdf.set_text_color(*GRAY)
    pdf.cell(0, 5, title_sub, align='C')
    pdf.ln(8)

    # 1. Member Collections
    _heading(pdf, 1, 'Member Collections')
    contrib = data['contributions']
    note = f'{contrib["count"]} of {contrib["member_count"]} members contributed'
    pdf.set_font('EN', '', 8.5)
    pdf.set_text_color(*GRAY)
    pdf.cell(0, 5, note)
    pdf.ln(6.5)

    if contrib['rows']:
        headers = ['#', 'Member', 'Share', 'Loan Principal', 'Loan Interest', 'Fine', 'Total']
        widths = [8, 66, 22, 25, 22, 24, 25]
        rows = []
        for idx, r in enumerate(contrib['rows'], 1):
            rows.append([idx, r['name'], inr(r['s']), inr(r['pr']), inr(r['i']), inr(r['fn']), inr(r['s'] + r['pr'] + r['i'] + r['fn'])])
        t = contrib['totals']
        rows.append(['', 'Total', inr(t['s']), inr(t['pr']), inr(t['i']), inr(t['fn']), inr(t['total'])])
        fonts = ['EN'] * 7
        aligns = ['C', 'L', 'R', 'R', 'R', 'R', 'R']
        _table(pdf, widths, headers, rows, fonts, aligns, bold_rows=(len(rows) - 1,))
    else:
        _empty(pdf, 'No entries')

    # 2. Summary
    _heading(pdf, 2, 'Summary')
    hardlock = '; '.join(f'{(r["notes"] or "-")} - {inr(r["amount"])}' for r in data['hardlock_active']) or 'NA'
    loan_names = []
    for r in data['new_loans']['rows']:
        if r['name'] not in loan_names:
            loan_names.append(r['name'])
    loans_val = '; '.join(loan_names) or 'NA'
    income_val = '; '.join(f'{r["description"]} ({inr(r["amount"])})' for r in data['income']['rows']) or 'NA'
    kv_rows = [
        ['Hardlock (Investments)', hardlock],
        ['New Loans', loans_val],
        ['Income', income_val],
    ]
    _table(pdf, [70, 116], ['Item', 'Details'], kv_rows, ['EN', 'EN'], ['L', 'L'])

    pdf.ln(3)
    pdf.set_font('EN', '', 8)
    pdf.set_text_color(*GRAY)
    pdf.cell(0, 5, f'Generated by {APP_NAME_EN} on {data["generated_on"]}')
    pdf.ln(5)


def build_report_pdf(data: dict) -> bytes:
    pdf = _ReportPDF('P', 'mm', 'A4')
    pdf.set_margins(14, 14, 14)
    pdf.set_auto_page_break(True, 14)
    _load_fonts(pdf)
    _draw_page(pdf, data)
    return bytes(pdf.output())
