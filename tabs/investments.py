# tabs/investments.py
import streamlit as st

from tax_engine import RETIREMENT_POOL_CAP


def render():
    st.header("หมวดกองทุนเพื่อการเกษียณและการลงทุน")
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
        "กองทุนการออมแห่งชาติ (กอช.)", min_value=0, step=500,
        help="ลดหย่อนตามที่จ่ายจริง สูงสุด 30,000 บาท (นับรวมในพูลเกษียณ 500,000) — เหมาะสำหรับฟรีแลนซ์/ผู้ประกอบอาชีพอิสระที่ไม่มีกองทุนอื่นรองรับ",
        key='nsf'
    )
    st.number_input(
        "กองทุน Thai ESG", min_value=0, step=1000,
        help="สูงสุด 30% ของเงินได้ และไม่เกิน 300,000 บาท (พูลแยกต่างหาก ไม่รวมกับพูลเกษียณ)",
        key='thai_esg'
    )

    pool_used_preview = (
        min(st.session_state.pvd, 999999999) + st.session_state.ssf +
        st.session_state.rmf + st.session_state.nsf + st.session_state.annuity_ins
    )
    st.progress(min(1.0, pool_used_preview / RETIREMENT_POOL_CAP))
    st.caption(f"ใช้ไปแล้วโดยประมาณ {pool_used_preview:,.0f} / {RETIREMENT_POOL_CAP:,.0f} บาท ในพูลเกษียณ (PVD+RMF+SSF+กอช.+ประกันบำนาญ) — ระบบจะคำนวณเพดานที่แท้จริงให้อัตโนมัติในหน้าสรุปผล")
