import streamlit as st
import pandas as pd
from fuzzywuzzy import fuzz
import re
from io import BytesIO
# ==========================
st.set_page_config(page_title="Reconciliation Tool", layout="wide")

# ==========================
# ✅ CSS Fixes
# ==========================
st.markdown("""
<style>

/* Remove the large default Streamlit top margin */
main > div {
    padding-top: 5px !important;
    margin-top: 10px !important;
}
.block-container {
    padding-top: 5px !important;
    margin-top: 0px !important;
}


html, body, [class*="css"] {
    font-size: 18px !important;
}

            
/* Slider shorten fix (targeting correct internal div) */
.short-slider div[data-baseweb="slider"] {
    width: 45% !important;
    margin-left: auto !important;
    margin-right: auto !important;
}

</style>
""", unsafe_allow_html=True)

# ==========================
# ✅ Header
# ==========================

col_logo, col_title = st.columns([1, 6])

with col_logo:
    st.markdown(
        """
        <div style="margin-top: 50px; margin-bottom: 0px;">
        """,
        unsafe_allow_html=True
    )

    st.image("apex-group-logo.png", width=200)

    st.markdown("</div>", unsafe_allow_html=True)


with col_title:
    st.markdown("""
            <h1 style="
                color:#004B8D;
                margin-top:50px;
                margin-bottom:0px;
            ">
                Reconciliation Tool
            </h1>
        """, unsafe_allow_html=True)

st.markdown("<hr>", unsafe_allow_html=True)






# ==========================
# ✅ Upload Boxes (Corrected)
# ==========================
st.markdown("### 📂 Upload Files")

col1, col2 = st.columns(2)

with col1:
    # st.markdown('<div class="upload-container">', unsafe_allow_html=True)
    base_file = st.file_uploader("📘 Upload Base File", type=["xlsx"])
    st.markdown('</div>', unsafe_allow_html=True)

with col2:
    # st.markdown('<div class="upload-container">', unsafe_allow_html=True)
    compare_file = st.file_uploader("📗 Upload Comparison File", type=["xlsx"])
    st.markdown('</div>', unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

# ==========================
# ✅ Slider (Short + Centered)
# ==========================
# 



with st.container():
    col1, col2, col3 = st.columns([1, 2, 1])
    with col1:
        # st.write("")  # Empty to create space
        st.markdown("<div class='slider-label'>Set Matching Threshold</div>", unsafe_allow_html=True)
        THRESH = st.slider("", 50, 100, 80, 5)
        st.markdown("</div>", unsafe_allow_html=True)


st.markdown("<hr>", unsafe_allow_html=True)

##########################################################
# ✅ Logic
##########################################################

def find_column(possible, cols):
    cols_clean = [c.lower().strip() for c in cols]

    # ✅ 1. Exact match FIRST
    for p in possible:
        p_clean = p.lower().strip()
        if p_clean in cols_clean:
            return cols_clean[cols_clean.index(p_clean)]

    # ✅ 2. Partial match fallback
    for p in possible:
        p_clean = p.lower().strip()
        for c in cols_clean:
            if p_clean in c:
                return c

    return None


def combine_address(row, cols):
    parts = []

    for c in cols:
        # Skip invalid column names
        if not isinstance(c, str):
            continue

        v = row.get(c, "")

        # Skip if value is a Series (safety guard)
        if isinstance(v, pd.Series):
            continue

        # Skip nulls and empty strings
        if pd.isna(v):
            continue

        v = str(v).strip()
        if not v:
            continue

        parts.append(v)

    return " ".join(parts).upper()

def clean_text(x):
    if pd.isna(x):
        return ""
    return re.sub(r"[^A-Za-z0-9]", "", str(x)).upper()

def fuzzy_address(a, b):
    return fuzz.token_set_ratio(clean_text(a), clean_text(b))

def to_excel(df):
    output = BytesIO()
    df.to_excel(output, index=False)
    return output.getvalue()

# ==========================
# ✅ MAIN LOGIC (unchanged)
# ==========================
if base_file and compare_file:

    st.success("✅ Files uploaded successfully!")

    if st.button("🚀 Run Reconciliation"):

        base_df = pd.read_excel(base_file)
        compare_df = pd.read_excel(compare_file)

        base_df.columns = base_df.columns.str.strip().str.lower().str.replace(" ", "")
        compare_df.columns = compare_df.columns.str.strip().str.lower().str.replace(" ", "")


        print("Base Columns:")
        for c in base_df.columns:
            print(f" - {c}")

        print("Comparison Columns:")
        for c in compare_df.columns:
            print(f" - {c}")

        base_fund = find_column(["fundaccount","accountnumber"], base_df.columns)
        comp_fund = find_column(["fundaccount","accountnumber"], compare_df.columns)
        base_inv = find_column(["investor","investor/shareholder/lp"], base_df.columns)
        comp_inv = find_column(["investor","investor/shareholder/lp"], compare_df.columns)
        compare_share = find_column(["share","fundname"], compare_df.columns)

        base_addr_cols = [
            find_column(["addressline1","address"], base_df.columns),
            find_column(["addressline2","address2"], base_df.columns),
            find_column(["addressline3","address3"], base_df.columns),
            find_column(["postalcode","zipcode"], base_df.columns),
        ]

        comp_addr_cols = [
            find_column(["addressline1","address"], compare_df.columns),
            find_column(["addressline2","address2"], compare_df.columns),
            find_column(["addressline3","address3"], compare_df.columns),
            find_column(["postalcode","zipcode"], compare_df.columns),
        ]

        print(f"Identified Base Fund Account Column: {base_fund}")
        print(f"Identified Comparison Fund Account Column: {comp_fund}")

        print(f"Identified Base Investor Column: {base_inv}")
        print(f"Identified Comparison Investor Column: {comp_inv}")

        print(f"Identified Comparison Share Column: {compare_share}")

        print(f"Identified Base Address Columns: {base_addr_cols}")
        print(f"Identified Comparison Address Columns: {comp_addr_cols}")

        # comp_addr_cols = [c for c in comp_addr_cols if c is not None]
        # base_addr_cols = [c for c in base_addr_cols if c is not None]

        base_df["address_base"] = base_df.apply(lambda r: combine_address(r, base_addr_cols), axis=1)
        compare_df["address_compare"] = compare_df.apply(lambda r: combine_address(r, comp_addr_cols), axis=1)

        results = []

        for _, comp_row in compare_df.iterrows():
            comp_fa = comp_row.get(comp_fund, "")
            comp_inv_name = comp_row.get(comp_inv, "")
            comp_addr = comp_row.get("address_compare", "")
            compare_share_val = comp_row.get(compare_share, None)


            
            if isinstance(comp_fa, pd.Series):
                comp_fa = comp_fa.iloc[0]



            # print(f"Processing Fund Account: {comp_fa}")
            # print(f"Comparison Investor Name: {comp_inv_name}")
            # print(f"Comparison Address: {comp_addr}")
            # print(f"Comparison Share: {compare_share_val}")

            if pd.isna(comp_fa) or str(comp_fa).strip() == "":
                continue

            matched_base = base_df[base_df[base_fund] == comp_fa]
            if matched_base.empty:
                continue

            for _, base_row in matched_base.iterrows():
                base_inv_name = base_row.get(base_inv, "")
                base_addr = base_row.get("address_base", "")
                score = fuzzy_address(base_addr, comp_addr)

                results.append({
                    "Share": compare_share_val,
                    "FundAccount": comp_fa,
                    "Investor_Compare": comp_inv_name,
                    "Investor_Base": base_inv_name,
                    "Address_Compare": comp_addr,
                    "Address_Base": base_addr,
                    "MatchScore": score
                })

        final_results = []
        for r in results:
            if r["MatchScore"] >= THRESH:
                continue
            fa = r["FundAccount"]
            has_good = any(res["FundAccount"] == fa and res["MatchScore"] >= THRESH for res in results)
            if has_good:
                continue
            final_results.append(r)

        unique_list = []
        for item in final_results:
            if item not in unique_list:
                unique_list.append(item)

        results_df = pd.DataFrame(unique_list)

        mismatch_count = len(results_df)

        st.markdown(
            f"<h3 style='color:#b00020;'>❌ Total Mismatches / Breaks: {mismatch_count}</h3>",
            unsafe_allow_html=True
        )

        if results_df.empty:
            st.success("🎉 No mismatches found!")
        else:
            st.dataframe(results_df, use_container_width=True)
            excel_data = to_excel(results_df)

            st.download_button(
                "📥 Download Mismatch Report (Excel)",
                excel_data,
                "Address_Mismatches.xlsx",
                "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )

else:
    col1, col2, col3 = st.columns([1, 2, 1])
    with col1:
        st.info("⬆️ Please upload both Excel files to begin.")
