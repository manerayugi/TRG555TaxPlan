# tabs/donations.py
import streamlit as st


def render():
    st.header("หมวดเงินบริจาค")
    c1, c2 = st.columns(2)
    with c1:
        st.number_input(
            "เงินบริจาคเพื่อการศึกษา/กีฬา/สาธารณประโยชน์ (ลดหย่อนได้ 2 เท่า)",
            min_value=0, step=1000, key='donate_education'
        )
    with c2:
        st.number_input(
            "เงินบริจาคทั่วไป (วัด มูลนิธิ องค์กรสาธารณกุศล ฯลฯ)",
            min_value=0, step=1000, key='donate_other'
        )
    st.caption("เงินบริจาคทั้งหมด (รวมส่วนที่คูณ 2 แล้ว) ลดหย่อนได้ไม่เกิน 10% ของเงินได้หลังหักค่าใช้จ่ายและค่าลดหย่อนอื่นๆ ทั้งหมด")
