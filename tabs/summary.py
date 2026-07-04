# tabs/summary.py
import pandas as pd
import streamlit as st

from tax_engine import calculate_tax_full


def render(selected_year):
    st.header("รายงานสรุปการประเมินภาษี")

    result = calculate_tax_full(dict(st.session_state), year=selected_year)
    b = result['breakdown']

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("รายได้พึงประเมินรวม", f"{result['total_income']:,.0f} ฿")
    c2.metric("หักค่าใช้จ่ายรวม", f"{result['total_expenses']:,.0f} ฿")
    c3.metric("หักค่าลดหย่อนรวม", f"{result['total_deductions']:,.0f} ฿")
    c4.metric("เงินได้สุทธิ", f"{result['net_income']:,.0f} ฿")

    st.divider()
    col_left, col_right = st.columns([1.3, 1])
    with col_left:
        st.subheader("สรุปภาระภาษีประจำปี")
        st.write(f"อัตราภาษีส่วนเพิ่ม (Marginal Rate) ปัจจุบัน: **{result['marginal_rate']*100:.0f}%**")
        st.write(f"ภาษีที่คำนวณได้ทั้งหมด: **{result['tax']:,.2f} บาท**")
        st.write(f"ภาษีหัก ณ ที่จ่ายสะสม: **{result['wht']:,.2f} บาท**")

        if result['tax_payable'] > 0:
            st.error(f"ยอดภาษีที่ต้องชำระเพิ่มเติม: **{result['tax_payable']:,.2f} บาท**")
        elif result['tax_refund'] > 0:
            st.success(f"ยอดภาษีที่ขอคืนได้: **{result['tax_refund']:,.2f} บาท**")
        else:
            st.info("ภาระภาษีสมดุล (ไม่ต้องชำระเพิ่มเติมและไม่มีสิทธิขอคืน)")

    with col_right:
        st.subheader("โครงสร้างเงินได้")
        chart_df = pd.DataFrame({
            'รายการ': ['ค่าใช้จ่าย', 'ค่าลดหย่อน', 'เงินได้สุทธิ'],
            'บาท': [result['total_expenses'], result['total_deductions'], result['net_income']],
        }).set_index('รายการ')
        st.bar_chart(chart_df)

    st.divider()
    st.subheader("รายละเอียดค่าลดหย่อนที่ใช้สิทธิ์แล้ว")
    detail_rows = [
        ("ผู้มีเงินได้ + ครอบครัว", b['family_total']),
        ("ประกันชีวิต/สุขภาพ", b['life_health_total']),
        ("ประกันสุขภาพบิดามารดา", b['parent_health']),
        ("ประกันชีวิตคู่สมรส", b['spouse_life']),
        ("พูลเกษียณ (PVD+RMF+SSF+กอช.+บำนาญ)", b['pool_used']),
        ("Thai ESG", b['thai_esg_final']),
        ("ประกันสังคม", b['social_sec_final']),
        ("ดอกเบี้ยบ้าน", b['home_loan_final']),
        ("Easy E-Receipt", b['easy_receipt_final']),
        ("ติดตั้งโซลาร์เซลล์", b['solar_final']),
        ("เงินบริจาค", b['donation_total']),
    ]
    detail_df = pd.DataFrame(detail_rows, columns=['หมวด', 'จำนวนเงิน (บาท)'])
    st.dataframe(detail_df.style.format({'จำนวนเงิน (บาท)': '{:,.0f}'}), width='stretch', hide_index=True)
