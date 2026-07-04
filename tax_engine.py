# tax_engine.py
"""
Engine คำนวณภาษีเงินได้บุคคลธรรมดา รองรับปีภาษี 2568 และ 2569
ครอบคลุม: การหักค่าใช้จ่ายตามเงินได้ 40(1)-40(8), ค่าลดหย่อนแบบเต็มรูปแบบ,
และฟังก์ชันวางแผนภาษี (หา 'ช่องว่าง' ที่ยังลดหย่อนเพิ่มได้ พร้อมประเมินภาษีที่ประหยัดได้จริง)

โครงสร้างค่าลดหย่อน/ขั้นภาษีเป็น "กฎถาวร" เหมือนกันทุกปี ส่วนมาตรการกระตุ้นเศรษฐกิจที่มีกำหนดเวลา
(Easy E-Receipt, โซลาร์เซลล์ ฯลฯ) ควบคุมการเปิด/ปิดต่อปีผ่าน YEAR_RULES ด้านล่าง

หมายเหตุ: เครื่องมือนี้เป็นการประมาณการเพื่อวางแผนเบื้องต้นเท่านั้น
ไม่ใช่คำแนะนำทางภาษีอย่างเป็นทางการ ควรตรวจสอบกับผู้เชี่ยวชาญ/สรรพากรก่อนตัดสินใจจริง
"""

import copy

# ==========================================
# ค่าคงที่
# ==========================================
TAX_BRACKETS = [
    (0, 150000, 0.0),
    (150000, 300000, 0.05),
    (300000, 500000, 0.10),
    (500000, 750000, 0.15),
    (750000, 1000000, 0.20),
    (1000000, 2000000, 0.25),
    (2000000, 5000000, 0.30),
    (5000000, float('inf'), 0.35),
]

RETIREMENT_POOL_CAP = 500000      # PVD/กบข + RMF + SSF + ประกันบำนาญ รวมกันไม่เกิน
THAI_ESG_CAP = 300000
LIFE_HEALTH_CAP = 100000
ANNUITY_BASE_CAP = 200000
ANNUITY_MAX_WITH_CARRYOVER = 300000   # 200,000 + ส่วนที่เหลือจากวงเงินประกันชีวิต/สุขภาพ 100,000 ที่ใช้ไม่เต็ม (สัดส่วน)
HEALTH_SUBCAP = 25000
PARENT_HEALTH_CAP = 15000
SPOUSE_LIFE_CAP = 10000
HOME_LOAN_CAP = 100000
SOCIAL_SEC_CAP = 9000
NSF_CAP = 30000   # กองทุนการออมแห่งชาติ (กอช.) ลดหย่อนตามจริง
DONATION_RATE_CAP = 0.10

EASY_RECEIPT_GENERAL_CAP = 30000
EASY_RECEIPT_OTOP_CAP = 20000
EASY_RECEIPT_TOTAL_CAP = 50000
SOLAR_INSTALL_CAP = 200000

DEFAULT_YEAR = '2568'

# กฎถาวร (โครงสร้างค่าลดหย่อน/ขั้นภาษี) เหมือนกันทุกปีที่รองรับ ต่างกันเฉพาะ
# "มาตรการกระตุ้นเศรษฐกิจ" ที่มีกำหนดเวลา/ยังไม่มีประกาศอย่างเป็นทางการ
# - Easy E-Receipt 2568: ยืนยันแล้ว ใช้ได้เฉพาะของที่ซื้อ 16 ม.ค. - 28 ก.พ. 2568
# - Easy E-Receipt 2569: ยังไม่มีมติ ครม./ประกาศกรมสรรพากร ณ ปัจจุบัน (TBD) จึงปิดไว้ก่อน
# - โซลาร์เซลล์: มติ ครม. 24 มิ.ย. 2568 ให้ใช้สิทธิ์ได้ปีภาษี 2568-2570 จึงเปิดทั้งสองปี
YEAR_RULES = {
    '2568': {'easy_receipt_enabled': True, 'solar_enabled': True},
    '2569': {'easy_receipt_enabled': False, 'solar_enabled': True},
}


def get_year_rules(year):
    return YEAR_RULES.get(year, YEAR_RULES[DEFAULT_YEAR])


# ==========================================
# 1) ค่าใช้จ่าย (หักจากเงินได้แต่ละประเภท)
# ==========================================
def calculate_expenses(data):
    """คำนวณการหักค่าใช้จ่ายตามประเภทเงินได้พึงประเมิน 40(1) - 40(8)"""

    # มาตรา 40(1) และ 40(2) หักรวมกัน 50% สูงสุดไม่เกิน 100,000 บาท
    inc_1_2 = data.get('inc_40_1', 0) + data.get('inc_40_2', 0)
    exp_1_2 = min(inc_1_2 * 0.5, 100000)

    # มาตรา 40(3) ค่าลิขสิทธิ์ หัก 50% สูงสุดไม่เกิน 100,000 บาท
    exp_3 = min(data.get('inc_40_3', 0) * 0.5, 100000)

    # มาตรา 40(4) ดอกเบี้ย/เงินปันผล ไม่สามารถหักค่าใช้จ่ายได้
    exp_4 = 0

    # มาตรา 40(5) - 40(7) หักค่าใช้จ่ายแบบเหมาตามอัตรามาตรฐาน
    exp_5 = data.get('inc_40_5', 0) * 0.30
    exp_6 = data.get('inc_40_6', 0) * 0.30
    exp_7 = data.get('inc_40_7', 0) * 0.60

    # มาตรา 40(8) ธุรกิจอื่นๆ (รองรับการหักแบบเหมา และ หักตามจริง)
    exp_8_mode = data.get('mode_40_8', 'หักเหมา 60%')
    if exp_8_mode == 'หักตามจริง (ต้องมีเอกสารประกอบ)':
        exp_8 = min(data.get('actual_exp_40_8', 0), data.get('inc_40_8', 0))
    else:
        exp_8 = data.get('inc_40_8', 0) * 0.60

    return exp_1_2 + exp_3 + exp_4 + exp_5 + exp_6 + exp_7 + exp_8


# ==========================================
# 2) ค่าลดหย่อน (แบบละเอียด พร้อมรายละเอียดแต่ละหมวด)
# ==========================================
def calculate_deductions(data, total_income, year=DEFAULT_YEAR):
    """
    คำนวณค่าลดหย่อนทุกหมวด คืนค่าเป็น (total_deductions, breakdown_dict)
    breakdown_dict เก็บทั้งยอดที่ใช้สิทธิ์แล้ว และ 'ช่องว่าง' (room) ที่ยังลดหย่อนเพิ่มได้
    """
    year_rules = get_year_rules(year)
    salary_income = data.get('inc_40_1', 0) + data.get('inc_40_2', 0)

    # ---------- หมวดส่วนตัวและครอบครัว ----------
    personal = 60000
    spouse = 60000 if data.get('has_spouse_no_income', False) else 0
    child_regular = min(data.get('child_regular', 0), 20) * 30000
    child_2018 = min(data.get('child_2018', 0), 20) * 60000
    parent = min(data.get('parent_count', 0), 8) * 30000
    disabled = min(data.get('disabled_count', 0), 20) * 60000
    family_total = personal + spouse + child_regular + child_2018 + parent + disabled

    # ---------- หมวดประกัน ----------
    health_used = min(data.get('health_ins', 0), HEALTH_SUBCAP)
    life_health_total = min(data.get('life_ins', 0) + health_used, LIFE_HEALTH_CAP)
    parent_health = min(data.get('parent_health_ins', 0), PARENT_HEALTH_CAP)
    spouse_life = min(data.get('spouse_life_ins', 0), SPOUSE_LIFE_CAP) if data.get('has_spouse_no_income', False) else 0

    # ---------- หมวดกองทุนเกษียณ (พูลรวมไม่เกิน 500,000) ----------
    pvd_cap_individual = min(data.get('pvd', 0), salary_income * 0.15)
    # ส่วนของวงเงินประกันชีวิต/สุขภาพ (100,000) ที่ใช้ไม่เต็ม โอนมาเพิ่มเพดานบำนาญได้ตามสัดส่วน
    unused_life_health_room = max(0, LIFE_HEALTH_CAP - life_health_total)
    annuity_cap = min(ANNUITY_BASE_CAP + unused_life_health_room, ANNUITY_MAX_WITH_CARRYOVER)
    annuity_cap_individual = min(data.get('annuity_ins', 0), total_income * 0.15, annuity_cap)
    rmf_cap_individual = min(data.get('rmf', 0), total_income * 0.30, 500000)
    ssf_cap_individual = min(data.get('ssf', 0), total_income * 0.30, 200000)
    nsf_cap_individual = min(data.get('nsf', 0), NSF_CAP)

    pool_sum = pvd_cap_individual + annuity_cap_individual + rmf_cap_individual + ssf_cap_individual + nsf_cap_individual
    pool_scale = 1.0
    if pool_sum > RETIREMENT_POOL_CAP and pool_sum > 0:
        pool_scale = RETIREMENT_POOL_CAP / pool_sum
    pvd_final = pvd_cap_individual * pool_scale
    annuity_final = annuity_cap_individual * pool_scale
    rmf_final = rmf_cap_individual * pool_scale
    ssf_final = ssf_cap_individual * pool_scale
    nsf_final = nsf_cap_individual * pool_scale
    pool_used = pvd_final + annuity_final + rmf_final + ssf_final + nsf_final

    # ---------- Thai ESG (พูลแยกต่างหาก) ----------
    thai_esg_final = min(data.get('thai_esg', 0), total_income * 0.30, THAI_ESG_CAP)

    # ---------- อื่นๆ ----------
    social_sec_final = min(data.get('social_sec', 0), SOCIAL_SEC_CAP)
    home_loan_final = min(data.get('home_loan', 0), HOME_LOAN_CAP)

    # ---------- มาตรการกระตุ้นเศรษฐกิจ (มีกำหนดเวลา/เงื่อนไขต่อปี ดู YEAR_RULES) ----------
    if year_rules['easy_receipt_enabled']:
        easy_receipt_general_final = min(data.get('easy_receipt_general', 0), EASY_RECEIPT_GENERAL_CAP)
        easy_receipt_otop_final = min(data.get('easy_receipt_otop', 0), EASY_RECEIPT_OTOP_CAP)
        easy_receipt_final = min(easy_receipt_general_final + easy_receipt_otop_final, EASY_RECEIPT_TOTAL_CAP)
    else:
        easy_receipt_final = 0

    if year_rules['solar_enabled']:
        solar_final = min(data.get('solar_install', 0), SOLAR_INSTALL_CAP)
    else:
        solar_final = 0

    other_total = social_sec_final + home_loan_final + easy_receipt_final + solar_final

    subtotal_before_donation = (
        family_total + life_health_total + parent_health + spouse_life +
        pool_used + thai_esg_final + other_total
    )

    # ---------- เงินบริจาค (คำนวณจากเงินได้สุทธิก่อนหักบริจาค) ----------
    expenses = calculate_expenses(data)
    net_before_donation = max(0, total_income - expenses - subtotal_before_donation)
    donation_cap = net_before_donation * DONATION_RATE_CAP

    donate_edu_raw = data.get('donate_education', 0) * 2  # บริจาคการศึกษา/กีฬา ลดหย่อนได้ 2 เท่า
    donate_edu_final = min(donate_edu_raw, donation_cap)
    remaining_donation_cap = max(0, donation_cap - donate_edu_final)
    donate_other_final = min(data.get('donate_other', 0), remaining_donation_cap)
    donation_total = donate_edu_final + donate_other_final

    total_deductions = subtotal_before_donation + donation_total

    breakdown = {
        'personal': personal,
        'spouse': spouse,
        'child_regular': child_regular,
        'child_2018': child_2018,
        'parent': parent,
        'disabled': disabled,
        'family_total': family_total,

        'life_health_total': life_health_total,
        'health_used': health_used,
        'parent_health': parent_health,
        'spouse_life': spouse_life,

        'pvd_final': pvd_final,
        'annuity_final': annuity_final,
        'rmf_final': rmf_final,
        'ssf_final': ssf_final,
        'nsf_final': nsf_final,
        'pool_used': pool_used,
        'pool_room': max(0, RETIREMENT_POOL_CAP - pool_used),

        'thai_esg_final': thai_esg_final,
        'thai_esg_room': max(0, min(total_income * 0.30, THAI_ESG_CAP) - thai_esg_final),

        'social_sec_final': social_sec_final,
        'home_loan_final': home_loan_final,
        'easy_receipt_final': easy_receipt_final,
        'solar_final': solar_final,

        'donate_edu_final': donate_edu_final,
        'donate_other_final': donate_other_final,
        'donation_total': donation_total,
        'donation_cap': donation_cap,

        'net_before_donation': net_before_donation,
    }
    return total_deductions, breakdown


# ==========================================
# 3) คำนวณภาษีจากขั้นบันได
# ==========================================
def calculate_tax_from_net_income(net_income):
    tax = 0
    for lower, upper, rate in TAX_BRACKETS:
        if net_income > lower:
            taxable_amount = min(net_income, upper) - lower
            tax += taxable_amount * rate
        else:
            break
    return tax


def get_marginal_rate(net_income):
    """อัตราภาษีส่วนเพิ่ม (marginal rate) ณ ระดับเงินได้สุทธิปัจจุบัน"""
    rate = 0.0
    for lower, upper, r in TAX_BRACKETS:
        if net_income > lower:
            rate = r
        else:
            break
    return rate


# ==========================================
# 4) ฟังก์ชันหลัก: คำนวณภาษี (ใช้ในหน้าแอปหลัก, รองรับหลายปีภาษี)
# ==========================================
def calculate_tax_2568(data):
    """คงชื่อ/สัญญาณ (signature) เดิมไว้เพื่อความเข้ากันได้กับโค้ดเดิม"""
    result = calculate_tax_full(data, year='2568')
    return (
        result['net_income'], result['tax'], result['tax_payable'],
        result['tax_refund'], result['total_income'], result['total_expenses'],
        result['total_deductions'],
    )


def calculate_tax_full(data, year=DEFAULT_YEAR):
    """เวอร์ชันเต็ม คืนค่าเป็น dict รายละเอียดครบถ้วน สำหรับหน้าสรุปผล/วางแผนภาษี"""
    total_income = sum([data.get(f'inc_40_{i}', 0) for i in range(1, 9)])
    total_expenses = calculate_expenses(data)
    total_deductions, breakdown = calculate_deductions(data, total_income, year)

    net_income = max(0, total_income - total_expenses - total_deductions)
    tax = calculate_tax_from_net_income(net_income)

    wht = data.get('wht', 0)
    final_tax = tax - wht
    tax_payable = max(0, final_tax)
    tax_refund = max(0, -final_tax)

    return {
        'total_income': total_income,
        'total_expenses': total_expenses,
        'total_deductions': total_deductions,
        'net_income': net_income,
        'tax': tax,
        'wht': wht,
        'tax_payable': tax_payable,
        'tax_refund': tax_refund,
        'marginal_rate': get_marginal_rate(net_income),
        'breakdown': breakdown,
    }


# ==========================================
# 5) เครื่องมือวางแผนภาษี (Tax Planning / Optimizer)
# ==========================================
PLANNING_ITEMS = [
    # key ใน session_state, ป้ายชื่อ, คำอธิบายเพดาน
    ('rmf', 'RMF (กองทุนเพื่อการเลี้ยงชีพ)', 'ไม่เกิน 30% ของเงินได้ และไม่เกิน 500,000 (รวมพูลเกษียณ)'),
    ('ssf', 'SSF (กองทุนเพื่อการออม)', 'ไม่เกิน 30% ของเงินได้ และไม่เกิน 200,000 (รวมพูลเกษียณ)'),
    ('pvd', 'PVD / กบข.', 'ไม่เกิน 15% ของเงินเดือน (รวมพูลเกษียณ)'),
    ('nsf', 'กองทุนการออมแห่งชาติ (กอช.)', 'ตามที่จ่ายจริง ไม่เกิน 30,000 (รวมพูลเกษียณ)'),
    ('annuity_ins', 'ประกันชีวิตแบบบำนาญ', 'ไม่เกิน 15% ของเงินได้ และไม่เกิน 200,000 (รวมพูลเกษียณ)'),
    ('thai_esg', 'กองทุน Thai ESG', 'ไม่เกิน 30% ของเงินได้ และไม่เกิน 300,000'),
    ('life_ins', 'เบี้ยประกันชีวิต/สุขภาพ', 'รวมกันไม่เกิน 100,000'),
    ('donate_education', 'เงินบริจาคการศึกษา (ลดหย่อนได้ 2 เท่า)', 'ไม่เกิน 10% ของเงินได้หลังหักลดหย่อน'),
    ('donate_other', 'เงินบริจาคทั่วไป', 'ไม่เกิน 10% ของเงินได้หลังหักลดหย่อน'),
    ('solar_install', 'ค่าติดตั้งโซลาร์เซลล์', 'ตามที่จ่ายจริง ไม่เกิน 200,000 (ปีภาษี 2568-2570, ขนาดไม่เกิน 10kW)'),
    ('easy_receipt_general', 'Easy E-Receipt (ร้านทั่วไป)', 'ไม่เกิน 30,000 (ซื้อช่วง 16 ม.ค. - 28 ก.พ. 2568 เท่านั้น)'),
    ('easy_receipt_otop', 'Easy E-Receipt (OTOP/วิสาหกิจชุมชน)', 'ไม่เกิน 20,000 (ซื้อช่วง 16 ม.ค. - 28 ก.พ. 2568 เท่านั้น)'),
]


def _room_for_item(key, data, total_income, breakdown, year=DEFAULT_YEAR):
    year_rules = get_year_rules(year)
    salary_income = data.get('inc_40_1', 0) + data.get('inc_40_2', 0)
    pool_room = breakdown['pool_room']

    if key == 'rmf':
        cap = min(total_income * 0.30, 500000)
        indiv_room = max(0, cap - data.get('rmf', 0))
        return min(indiv_room, pool_room)
    if key == 'ssf':
        cap = min(total_income * 0.30, 200000)
        indiv_room = max(0, cap - data.get('ssf', 0))
        return min(indiv_room, pool_room)
    if key == 'pvd':
        cap = salary_income * 0.15
        indiv_room = max(0, cap - data.get('pvd', 0))
        return min(indiv_room, pool_room)
    if key == 'nsf':
        indiv_room = max(0, NSF_CAP - data.get('nsf', 0))
        return min(indiv_room, pool_room)
    if key == 'annuity_ins':
        unused_life_health_room = max(0, LIFE_HEALTH_CAP - breakdown['life_health_total'])
        annuity_cap = min(ANNUITY_BASE_CAP + unused_life_health_room, ANNUITY_MAX_WITH_CARRYOVER)
        cap = min(total_income * 0.15, annuity_cap)
        indiv_room = max(0, cap - data.get('annuity_ins', 0))
        return min(indiv_room, pool_room)
    if key == 'thai_esg':
        return breakdown['thai_esg_room']
    if key == 'life_ins':
        return max(0, LIFE_HEALTH_CAP - breakdown['life_health_total'])
    if key == 'donate_education':
        return max(0, (breakdown['donation_cap'] - breakdown['donation_total']))
    if key == 'donate_other':
        return max(0, (breakdown['donation_cap'] - breakdown['donation_total']))
    if key == 'solar_install':
        if not year_rules['solar_enabled']:
            return 0
        return max(0, SOLAR_INSTALL_CAP - data.get('solar_install', 0))
    if key == 'easy_receipt_general':
        if not year_rules['easy_receipt_enabled']:
            return 0
        return max(0, EASY_RECEIPT_GENERAL_CAP - data.get('easy_receipt_general', 0))
    if key == 'easy_receipt_otop':
        if not year_rules['easy_receipt_enabled']:
            return 0
        return max(0, EASY_RECEIPT_OTOP_CAP - data.get('easy_receipt_otop', 0))
    return 0


def suggest_tax_planning(data, year=DEFAULT_YEAR):
    """
    วิเคราะห์ 'ช่องว่าง' ของแต่ละหมวดลดหย่อนที่ยังใช้สิทธิ์ได้ไม่เต็ม
    และประเมินภาษีที่จะประหยัดได้จริง หากลงทุน/ซื้อเพิ่มจนเต็มสิทธิ์ในหมวดนั้นๆ เพียงหมวดเดียว
    คืนค่าเป็น list of dict เรียงจากประหยัดภาษีได้มากไปน้อย
    """
    base_result = calculate_tax_full(data, year)
    total_income = base_result['total_income']
    breakdown = base_result['breakdown']
    base_tax = base_result['tax']

    suggestions = []
    for key, label, cap_desc in PLANNING_ITEMS:
        room = _room_for_item(key, data, total_income, breakdown, year)
        room = round(room, 2)
        if room <= 1:
            continue

        # คำนวณภาษีใหม่จริง หากใช้สิทธิ์เต็มในหมวดนี้ (คำนวณซ้ำทั้งระบบเพื่อความแม่นยำ)
        sim_data = copy.deepcopy(data)
        sim_data[key] = sim_data.get(key, 0) + room
        sim_result = calculate_tax_full(sim_data, year)
        tax_saved = max(0, base_tax - sim_result['tax'])

        suggestions.append({
            'key': key,
            'label': label,
            'cap_desc': cap_desc,
            'room': room,
            'tax_saved': round(tax_saved, 2),
        })

    suggestions.sort(key=lambda x: x['tax_saved'], reverse=True)
    return suggestions


def simulate_plan(data, overrides, year=DEFAULT_YEAR):
    """
    จำลอง 'แผนใหม่' โดยรับ dict ของค่าที่ต้องการเพิ่ม (overrides: key -> จำนวนเงินที่เพิ่ม)
    แล้วคืนผลลัพธ์ calculate_tax_full ของแผนใหม่ เทียบกับแผนปัจจุบัน
    """
    sim_data = copy.deepcopy(data)
    for k, v in overrides.items():
        sim_data[k] = sim_data.get(k, 0) + v

    base_result = calculate_tax_full(data, year)
    sim_result = calculate_tax_full(sim_data, year)
    tax_saved = base_result['tax'] - sim_result['tax']

    return {
        'base': base_result,
        'plan': sim_result,
        'tax_saved': tax_saved,
    }
