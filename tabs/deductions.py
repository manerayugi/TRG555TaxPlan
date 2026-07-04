# tabs/deductions.py
import streamlit as st


def render():
    st.header("หมวดค่าลดหย่อนส่วนบุคคลและครอบครัว")

    st.info("ค่าลดหย่อนผู้มีเงินได้ 60,000 บาท ถูกนำไปคำนวณให้อัตโนมัติ")

    c1, c2 = st.columns(2)
    with c1:
        st.checkbox(
            "มีคู่สมรสที่ไม่มีเงินได้ (ลดหย่อนเพิ่ม 60,000 บาท)",
            key='has_spouse_no_income'
        )
        st.number_input(
            "จำนวนบุตร (คนที่ 1 หรือเกิดก่อนปี พ.ศ. 2561) — คนละ 30,000",
            min_value=0, max_value=20, step=1, key='child_regular'
        )
        st.number_input(
            "จำนวนบุตร (คนที่ 2 เป็นต้นไป ที่เกิดปี พ.ศ. 2561 เป็นต้นไป) — คนละ 60,000",
            min_value=0, max_value=20, step=1, key='child_2018'
        )
    with c2:
        st.number_input(
            "จำนวนบิดามารดาที่อุปการะเลี้ยงดู (ท่าน) — คนละ 30,000",
            min_value=0, max_value=8, step=1,
            help="อายุ 60 ปีขึ้นไป มีรายได้ไม่เกิน 30,000 บาท/ปี (รวมบิดามารดาของคู่สมรส กรณีคู่สมรสไม่มีเงินได้ ได้สูงสุด 8 ท่าน)",
            key='parent_count'
        )
        st.number_input(
            "จำนวนผู้พิการ/ทุพพลภาพที่อุปการะ (ท่าน) — คนละ 60,000",
            min_value=0, max_value=20, step=1, key='disabled_count'
        )

    st.divider()
    st.subheader("ค่าลดหย่อนอื่นๆ")
    c3, c4 = st.columns(2)
    with c3:
        st.number_input(
            "เงินสมทบกองทุนประกันสังคม", min_value=0, max_value=9000, step=100,
            key='social_sec'
        )
    with c4:
        st.number_input(
            "ดอกเบี้ยเงินกู้ยืมเพื่อที่อยู่อาศัย", min_value=0, step=1000,
            help="ตามที่จ่ายจริง สูงสุดไม่เกิน 100,000 บาท",
            key='home_loan'
        )
