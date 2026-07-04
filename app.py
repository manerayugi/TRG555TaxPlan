# app.py
import streamlit as st

from tabs import income, deductions, insurance, investments, stimulus, donations, summary, planning

# ==========================================
# ตั้งค่าระบบและ UI
# ==========================================
st.set_page_config(page_title="TRG555 Tax Plan", layout="wide")

st.sidebar.title("TRG555 Tax Plan")
selected_year = st.sidebar.selectbox("เลือกปีภาษีสำหรับการประเมิน", ["2568", "2569"])
st.sidebar.markdown("---")
st.sidebar.info("ระบบจำลองการประเมินภาษีเงินได้บุคคลธรรมดา เพื่อประโยชน์ในการวางแผนการเงินและการลงทุน")
st.sidebar.caption("⚠️ เครื่องมือนี้เป็นการประมาณการเบื้องต้นเพื่อการวางแผน มิใช่คำแนะนำทางภาษีอย่างเป็นทางการ")

# กำหนดค่าเริ่มต้นตัวแปร (Session State Initialization)
DEFAULTS = {
    'inc_40_1': 0, 'inc_40_2': 0, 'inc_40_3': 0, 'inc_40_4': 0, 'inc_40_5': 0,
    'inc_40_6': 0, 'inc_40_7': 0, 'inc_40_8': 0,
    'mode_40_8': 'หักเหมา 60%', 'actual_exp_40_8': 0, 'wht': 0,

    'has_spouse_no_income': False, 'child_regular': 0, 'child_2018': 0,
    'parent_count': 0, 'disabled_count': 0,

    'social_sec': 0, 'home_loan': 0,

    'life_ins': 0, 'health_ins': 0, 'annuity_ins': 0,
    'parent_health_ins': 0, 'spouse_life_ins': 0,

    'pvd': 0, 'ssf': 0, 'rmf': 0, 'nsf': 0, 'thai_esg': 0,

    'easy_receipt_general': 0, 'easy_receipt_otop': 0, 'solar_install': 0,

    'donate_education': 0, 'donate_other': 0,
}
for k, v in DEFAULTS.items():
    if k not in st.session_state:
        st.session_state[k] = v

st.title(f"แบบจำลองการประเมินภาษี ปีภาษี {selected_year}")

# ==========================================
# โครงสร้างแบบฟอร์ม (Tabs)
# ==========================================
tab1, tab2, tab3, tab4, tab5, tab6, tab7, tab8 = st.tabs([
    "1. ข้อมูลรายได้",
    "2. ลดหย่อนส่วนตัว/ครอบครัว",
    "3. ประกันภัย",
    "4. กองทุน/การลงทุน",
    "5. มาตรการกระตุ้นเศรษฐกิจ",
    "6. เงินบริจาค",
    "7. รายงานสรุปผล",
    "8. วางแผนลดหย่อนภาษี",
])

with tab1:
    income.render()

with tab2:
    deductions.render()

with tab3:
    insurance.render()

with tab4:
    investments.render()

with tab5:
    stimulus.render(selected_year)

with tab6:
    donations.render()

with tab7:
    summary.render(selected_year)

with tab8:
    planning.render(selected_year)
