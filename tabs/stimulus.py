# tabs/stimulus.py
import streamlit as st

from tax_engine import (
    EASY_RECEIPT_GENERAL_CAP,
    EASY_RECEIPT_OTOP_CAP,
    SOLAR_INSTALL_CAP,
    get_year_rules,
)


def render(selected_year):
    st.header("มาตรการกระตุ้นเศรษฐกิจ")
    year_rules = get_year_rules(selected_year)

    st.subheader("Easy E-Receipt")
    if year_rules['easy_receipt_enabled']:
        st.caption("ใช้ได้เฉพาะสินค้า/บริการที่ซื้อช่วง 16 ม.ค. - 28 ก.พ. 2568 พร้อม e-Tax Invoice หรือ e-Receipt เท่านั้น "
                   "ไม่รวม: เหล้า/บุหรี่, น้ำมัน/ก๊าซ, รถยนต์/รถจักรยานยนต์, ค่าน้ำ-ไฟ-โทรศัพท์-อินเทอร์เน็ต, เบี้ยประกัน, ทัวร์/ที่พัก, ทองคำ")
        c1, c2 = st.columns(2)
        with c1:
            st.number_input(
                "ซื้อสินค้า/บริการร้านทั่วไป (บาท)", min_value=0, step=1000,
                max_value=EASY_RECEIPT_GENERAL_CAP,
                help=f"สูงสุด {EASY_RECEIPT_GENERAL_CAP:,.0f} บาท",
                key='easy_receipt_general'
            )
        with c2:
            st.number_input(
                "ซื้อสินค้า OTOP/วิสาหกิจชุมชน/วิสาหกิจเพื่อสังคม (บาท)", min_value=0, step=1000,
                max_value=EASY_RECEIPT_OTOP_CAP,
                help=f"สูงสุด {EASY_RECEIPT_OTOP_CAP:,.0f} บาท",
                key='easy_receipt_otop'
            )
    else:
        st.info(
            f"ยังไม่มีมติ ครม./ประกาศกรมสรรพากรเรื่อง Easy E-Receipt สำหรับปีภาษี {selected_year} "
            "(รายการนี้จะเปิดให้กรอกเมื่อมีประกาศอย่างเป็นทางการ)"
        )

    st.divider()
    st.subheader("ติดตั้งโซลาร์เซลล์ (Solar Rooftop)")
    if year_rules['solar_enabled']:
        st.number_input(
            "ค่าติดตั้งระบบโซลาร์เซลล์ตามจริง (บาท)", min_value=0, step=5000,
            max_value=SOLAR_INSTALL_CAP,
            help=(
                f"หักได้ตามที่จ่ายจริง สูงสุด {SOLAR_INSTALL_CAP:,.0f} บาท "
                "ขนาดติดตั้งไม่เกิน 10kW ใช้สิทธิ์ได้ 1 ระบบต่อคน "
                "(มติ ครม. 24 มิ.ย. 2568 ใช้ได้ปีภาษี 2568-2570)"
            ),
            key='solar_install'
        )
    else:
        st.info(f"มาตรการโซลาร์เซลล์ยังไม่มีผลสำหรับปีภาษี {selected_year}")
