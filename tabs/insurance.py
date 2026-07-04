# tabs/insurance.py
import streamlit as st

from tax_engine import RETIREMENT_POOL_CAP


def render():
    st.header("หมวดสิทธิประโยชน์ทางภาษี (ประกันและการลงทุนเพื่อการเกษียณ)")
    col_ins, col_fund = st.columns(2)
    with col_ins:
        st.subheader("กลุ่มผลิตภัณฑ์ประกันภัย")
        st.number_input(
            "เบี้ยประกันชีวิตแบบทั่วไป / สะสมทรัพย์", min_value=0, step=1000,
            help="รวมกับประกันสุขภาพ สูงสุด 100,000 บาท", key='life_ins'
        )
        st.number_input(
            "เบี้ยประกันสุขภาพ", min_value=0, step=1000,
            help="สูงสุด 25,000 บาท (รวมกับประกันชีวิตต้องไม่เกิน 100,000 บาท)",
            key='health_ins'
        )
        st.number_input(
            "เบี้ยประกันสุขภาพบิดามารดา (ของตนเอง/คู่สมรส)", min_value=0, step=1000,
            help="สูงสุด 15,000 บาท", key='parent_health_ins'
        )
        st.number_input(
            "เบี้ยประกันชีวิตคู่สมรสที่ไม่มีเงินได้", min_value=0, step=1000,
            help="สูงสุด 10,000 บาท (ใช้สิทธิ์ได้เมื่อระบุว่ามีคู่สมรสไม่มีเงินได้ในแท็บที่ 2)",
            disabled=not st.session_state.has_spouse_no_income,
            key='spouse_life_ins'
        )
        st.number_input(
            "เบี้ยประกันชีวิตแบบบำนาญ", min_value=0, step=1000,
            help=(
                "สูงสุด 15% ของรายได้ และไม่เกิน 200,000 บาท "
                "(หากไม่ใช้สิทธิ์ประกันชีวิต/สุขภาพทั่วไปเลย (=0 บาท) "
                "จะได้เพดานเพิ่มเป็น 300,000 บาทแทน — เป็นแบบ all-or-nothing "
                "ใช้แม้เพียงบาทเดียวจะไม่ได้รับการโอนสิทธิ์นี้ "
                "และยังนับรวมในพูลเกษียณ 500,000 บาท)"
            ),
            key='annuity_ins'
        )
    with col_fund:
        st.subheader("กลุ่มกองทุนเพื่อการเกษียณและการลงทุน")
        st.number_input(
            "กองทุนสำรองเลี้ยงชีพ (PVD) / กบข.", min_value=0, step=1000,
            help="สูงสุด 15% ของเงินเดือน (นับรวมในพูลเกษียณ 500,000)", key='pvd'
        )
        st.number_input(
            "กองทุนเพื่อการออม (SSF)", min_value=0, step=1000,
            help="สูงสุด 30% ของเงินได้ และไม่เกิน 200,000 บาท (นับรวมในพูลเกษียณ 500,000)",
            key='ssf'
        )
        st.number_input(
            "กองทุนเพื่อการเลี้ยงชีพ (RMF)", min_value=0, step=1000,
            help="สูงสุด 30% ของเงินได้ และไม่เกิน 500,000 บาท (นับรวมในพูลเกษียณ 500,000)",
            key='rmf'
        )
        st.number_input(
            "กองทุน Thai ESG", min_value=0, step=1000,
            help="สูงสุด 30% ของเงินได้ และไม่เกิน 300,000 บาท (พูลแยกต่างหาก ไม่รวมกับพูลเกษียณ)",
            key='thai_esg'
        )

        pool_used_preview = (
            min(st.session_state.pvd, 999999999) + st.session_state.ssf +
            st.session_state.rmf + st.session_state.annuity_ins
        )
        st.progress(min(1.0, pool_used_preview / RETIREMENT_POOL_CAP))
        st.caption(f"ใช้ไปแล้วโดยประมาณ {pool_used_preview:,.0f} / {RETIREMENT_POOL_CAP:,.0f} บาท ในพูลเกษียณ (PVD+RMF+SSF+ประกันบำนาญ) — ระบบจะคำนวณเพดานที่แท้จริงให้อัตโนมัติในหน้าสรุปผล")
