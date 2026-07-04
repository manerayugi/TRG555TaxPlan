# tabs/planning.py
import pandas as pd
import streamlit as st

from tax_engine import calculate_tax_full, suggest_tax_planning, simulate_plan

SIM_ITEMS = [
    ('rmf', 'เพิ่ม RMF (บาท)'),
    ('ssf', 'เพิ่ม SSF (บาท)'),
    ('thai_esg', 'เพิ่ม Thai ESG (บาท)'),
    ('pvd', 'เพิ่ม PVD/กบข. (บาท)'),
    ('nsf', 'เพิ่ม กอช. (บาท)'),
    ('annuity_ins', 'เพิ่มประกันบำนาญ (บาท)'),
    ('life_ins', 'เพิ่มเบี้ยประกันชีวิต/สุขภาพ (บาท)'),
    ('donate_education', 'เพิ่มเงินบริจาคการศึกษา (บาท)'),
    ('solar_install', 'เพิ่มค่าติดตั้งโซลาร์เซลล์ (บาท)'),
    ('easy_receipt_general', 'เพิ่ม Easy E-Receipt ร้านทั่วไป (บาท)'),
    ('easy_receipt_otop', 'เพิ่ม Easy E-Receipt OTOP (บาท)'),
]


def render(selected_year):
    st.header("เครื่องมือวางแผนลดหย่อนภาษี")

    base_result = calculate_tax_full(dict(st.session_state), year=selected_year)

    st.subheader("🔍 ช่องว่างที่ยังลดหย่อนได้เพิ่ม (เรียงตามภาษีที่ประหยัดได้มากสุด)")
    suggestions = suggest_tax_planning(dict(st.session_state), year=selected_year)

    if not suggestions:
        st.success("คุณใช้สิทธิ์ลดหย่อนภาษีเต็มเพดานทุกหมวดแล้ว 🎉")
    else:
        sug_df = pd.DataFrame(suggestions)[['label', 'cap_desc', 'room', 'tax_saved']]
        sug_df.columns = ['หมวดลดหย่อน', 'เงื่อนไข/เพดาน', 'ยังใช้สิทธิ์ได้อีก (บาท)', 'ประหยัดภาษีได้สูงสุด (บาท)']
        st.dataframe(
            sug_df.style.format({
                'ยังใช้สิทธิ์ได้อีก (บาท)': '{:,.0f}',
                'ประหยัดภาษีได้สูงสุด (บาท)': '{:,.0f}',
            }),
            width='stretch', hide_index=True
        )
        st.caption("ตัวเลข 'ประหยัดภาษีได้สูงสุด' คำนวณจากการใช้สิทธิ์เต็มเพดานในหมวดนั้นเพียงหมวดเดียว โดยหมวดอื่นคงเดิม")

    st.divider()
    st.subheader("🧮 จำลองแผนใหม่ (What-if Simulator)")
    st.caption("ลองปรับจำนวนเงินที่ต้องการลงทุน/ซื้อเพิ่มเติม เพื่อดูผลกระทบต่อภาษีแบบทันที เทียบกับแผนปัจจุบัน")

    room_map = {item['key']: item['room'] for item in suggestions}

    sc1, sc2 = st.columns(2)
    cols = [sc1, sc2]
    overrides = {}
    for i, (key, label) in enumerate(SIM_ITEMS):
        room = int(room_map.get(key, 0))
        with cols[i % 2]:
            if room >= 1000:
                overrides[key] = st.number_input(
                    label, min_value=0, max_value=room, value=0, step=1000,
                    help=f"ใช้สิทธิ์เพิ่มได้อีกสูงสุด {room:,.0f} บาท"
                )
            else:
                overrides[key] = 0

    overrides = {k: v for k, v in overrides.items() if v > 0}

    if not overrides:
        st.info("กรอกจำนวนเงินในช่องด้านบนเพื่อเริ่มจำลองแผนใหม่")
        return

    sim = simulate_plan(dict(st.session_state), overrides, year=selected_year)
    plan = sim['plan']

    st.divider()
    st.subheader("ผลเปรียบเทียบ: แผนปัจจุบัน vs แผนใหม่")
    pc1, pc2, pc3 = st.columns(3)
    pc1.metric("ภาษีแผนปัจจุบัน", f"{base_result['tax']:,.0f} ฿")
    pc2.metric("ภาษีแผนใหม่", f"{plan['tax']:,.0f} ฿", delta=f"-{sim['tax_saved']:,.0f} ฿" if sim['tax_saved'] > 0 else "0 ฿")
    pc3.metric("เงินลงทุนเพิ่มรวม", f"{sum(overrides.values()):,.0f} ฿")

    compare_df = pd.DataFrame({
        'แผน': ['ปัจจุบัน', 'แผนใหม่'],
        'ภาษีที่ต้องจ่าย (บาท)': [base_result['tax'], plan['tax']],
    }).set_index('แผน')
    st.bar_chart(compare_df)

    if sim['tax_saved'] > 0:
        st.success(f"หากดำเนินการตามแผนใหม่ จะช่วยประหยัดภาษีได้ประมาณ **{sim['tax_saved']:,.0f} บาท**")
