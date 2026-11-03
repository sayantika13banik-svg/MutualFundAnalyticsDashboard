
import streamlit as st
import pandas as pd
import numpy as np
import sqlite3
import plotly.express as px
import plotly.graph_objects as go

st.set_page_config(
    page_title="MF Analytics Platform",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded"
)

DB = "mf_analytics.db"

@st.cache_data
def load_data():
    con = sqlite3.connect(DB)
    tables = {
        "funds": "SELECT * FROM dim_fund",
        "perf": "SELECT * FROM fact_performance",
        "aum": "SELECT * FROM fact_aum",
        "sip": "SELECT * FROM fact_sip",
        "tx": "SELECT * FROM fact_transactions",
        "hold": "SELECT * FROM fact_holdings",
    }
    out = {}
    for k, q in tables.items():
        try:
            out[k] = pd.read_sql_query(q, con)
        except Exception:
            out[k] = pd.DataFrame()
    con.close()
    return out

D = load_data()
funds, perf, aum, sip, tx, hold = [D[k] for k in ["funds","perf","aum","sip","tx","hold"]]

# ----------------- Helpers -----------------
def money_cr(x):
    return f"₹{x:,.0f} Cr"

def pct(x):
    return f"{x:.2f}%"

def safe_num(df, col):
    if col not in df.columns:
        return pd.Series(dtype=float)
    return pd.to_numeric(df[col], errors="coerce")

def style_fig(fig, height=400):
    fig.update_layout(
        height=height,
        margin=dict(l=10,r=10,t=45,b=10),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(color="#D9E2F2"),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="left", x=0)
    )
    fig.update_xaxes(showgrid=False)
    fig.update_yaxes(gridcolor="rgba(255,255,255,0.08)")
    return fig

# ----------------- CSS -----------------
st.markdown("""
<style>
.stApp { background: #07111f; color: #e8eef8; }
[data-testid="stSidebar"] { background: #0a1628; }
.block-container { padding-top: 1.2rem; max-width: 1500px; }
.hero {
    padding: 28px 30px; border-radius: 20px; margin-bottom: 20px;
    background: linear-gradient(135deg,#111f38 0%,#1c1b4b 52%,#30206b 100%);
    border: 1px solid rgba(255,255,255,.08);
}
.hero h1 { margin: 0; font-size: 2.35rem; color: white; }
.hero p { margin: 8px 0 0; color: #b8c6dc; font-size: 1rem; }
.section { margin: 18px 0 10px; font-size: 1.15rem; font-weight: 700; color: #f4f7fb; }
.kpi {
    padding: 18px; border-radius: 16px; background: #0e1c30;
    border: 1px solid rgba(255,255,255,.07); min-height: 112px;
}
.kpi .label { color:#8fa4c1; font-size:.82rem; }
.kpi .value { color:#fff; font-size:1.55rem; font-weight:750; margin-top:7px; }
.kpi .sub { color:#7187a6; font-size:.74rem; margin-top:4px; }
.badge { padding:5px 10px; border-radius:999px; background:#172a46; color:#b9d0ef; font-size:.75rem; }
.small { color:#8fa4c1; font-size:.82rem; }
</style>
""", unsafe_allow_html=True)

# ----------------- Sidebar -----------------
st.sidebar.markdown("## 📈 MF Analytics")
st.sidebar.caption("FinTech Data Analytics & Decision Support Platform")
page = st.sidebar.radio(
    "Navigate",
    ["Executive Overview","Fund Screener","Performance & Risk","Investor Analytics","Portfolio & Holdings","Benchmark & Correlation"]
)

st.sidebar.divider()

amcs = ["All"] + sorted(funds["fund_house"].dropna().unique().tolist()) if "fund_house" in funds else ["All"]
cats = ["All"] + sorted(funds["category"].dropna().unique().tolist()) if "category" in funds else ["All"]

sel_amc = st.sidebar.selectbox("AMC", amcs)
sel_cat = st.sidebar.selectbox("Category", cats)

st.sidebar.caption("")

def filtered_perf():
    x = perf.copy()
    if sel_amc != "All" and "fund_house" in x:
        x = x[x["fund_house"] == sel_amc]
    if sel_cat != "All" and "category" in x:
        x = x[x["category"] == sel_cat]
    return x

# ----------------- Header -----------------
st.markdown("""
<div class="hero">
<h1>Mutual Fund Analytics Platform</h1>
<p>End-to-end analytics layer for fund performance, risk, investor behaviour and portfolio intelligence.</p>
</div>
""", unsafe_allow_html=True)

# ----------------- Executive Overview -----------------
if page == "Executive Overview":
    latest_sip = safe_num(sip,"sip_inflow_crore").iloc[-1] if len(sip) else np.nan
    latest_folios = safe_num(sip,"active_sip_accounts_crore").iloc[-1] if len(sip) else np.nan
    tracked_aum = safe_num(aum,"aum_crore").iloc[-1] if len(aum) else np.nan

    cols = st.columns(4)
    vals = [
        ("Schemes Tracked", f"{len(funds):,}", "Fund master"),
        ("Latest SIP Inflow", money_cr(latest_sip) if pd.notna(latest_sip) else "—", "Latest observation"),
        ("Investor Transactions", f"{len(tx):,}", f"{tx['investor_id'].nunique():,} investors" if 'investor_id' in tx else "Project dataset"),
        ("Tracked AUM", money_cr(tracked_aum) if pd.notna(tracked_aum) else "—", "Latest AUM observation"),
    ]
    for c,(l,v,s) in zip(cols, vals):
        c.markdown(f'<div class="kpi"><div class="label">{l}</div><div class="value">{v}</div><div class="sub">{s}</div></div>', unsafe_allow_html=True)

    st.markdown('<div class="section">Market Pulse</div>', unsafe_allow_html=True)
    c1,c2 = st.columns(2)
    with c1:
        if len(sip):
            q = sip.copy()
            q["month"] = pd.to_datetime(q["month"], errors="coerce")
            q["sip_inflow_crore"] = safe_num(q,"sip_inflow_crore")
            fig = px.area(q, x="month", y="sip_inflow_crore", title="Monthly SIP Inflow (₹ Cr)")
            st.plotly_chart(style_fig(fig,390), use_container_width=True)
    with c2:
        if len(aum):
            q = aum.copy()
            q["aum_crore"] = safe_num(q,"aum_crore")
            q = q.sort_values("aum_crore", ascending=False).head(10)
            fig = px.bar(q, x="aum_crore", y="fund_house", orientation="h", title="Largest AMC AUM Observations")
            st.plotly_chart(style_fig(fig,390), use_container_width=True)

    c1,c2 = st.columns(2)
    with c1:
        st.markdown('<div class="section">Category Inflows</div>', unsafe_allow_html=True)
        if "category" in perf.columns:
            cat = perf.groupby("category", as_index=False).agg(
                Schemes=("scheme_name","count"),
                Avg_Return_3Y=("return_3yr_pct","mean"),
                Avg_Sharpe=("sharpe_ratio","mean")
            ).sort_values("Avg_Return_3Y", ascending=False)
            st.dataframe(cat.round(2), use_container_width=True, hide_index=True)
    with c2:
        st.markdown('<div class="section">Top Risk-Adjusted Funds</div>', unsafe_allow_html=True)
        q = filtered_perf().sort_values("sharpe_ratio", ascending=False).head(5)
        show = q[["scheme_name","return_3yr_pct","sharpe_ratio","max_drawdown_pct"]].copy()
        show.columns=["Fund","3Y Return %","Sharpe","Max Drawdown %"]
        st.dataframe(show.round(2), use_container_width=True, hide_index=True)

# ----------------- Fund Screener -----------------
elif page == "Fund Screener":
    st.markdown('<div class="section">Fund Screener & Decision Support</div>', unsafe_allow_html=True)
    st.caption("Apply quantitative filters to identify funds matching a chosen return/risk profile.")

    c1,c2,c3,c4 = st.columns(4)
    min_ret = c1.slider("Minimum 3Y Return (%)", -20.0, 50.0, 10.0, 0.5)
    max_vol = c2.slider("Maximum Volatility (%)", 5.0, 60.0, 25.0, 0.5)
    min_sh = c3.slider("Minimum Sharpe", -2.0, 3.0, 0.75, 0.05)
    max_dd = c4.slider("Maximum Drawdown (%)", 0.0, 80.0, 35.0, 1.0)

    q = filtered_perf().copy()
    for col in ["return_3yr_pct","std_dev_ann_pct","sharpe_ratio","max_drawdown_pct"]:
        q[col] = safe_num(q,col)

    # drawdown is usually negative; compare absolute loss
    q["drawdown_abs"] = q["max_drawdown_pct"].abs()
    result = q[
        (q["return_3yr_pct"] >= min_ret) &
        (q["std_dev_ann_pct"] <= max_vol) &
        (q["sharpe_ratio"] >= min_sh) &
        (q["drawdown_abs"] <= max_dd)
    ].sort_values("sharpe_ratio", ascending=False)

    st.success(f"{len(result)} funds match the selected criteria.")
    cols = [c for c in ["scheme_name","fund_house","category","return_1yr_pct","return_3yr_pct","return_5yr_pct","std_dev_ann_pct","sharpe_ratio","sortino_ratio","max_drawdown_pct","risk_grade"] if c in result]
    out = result[cols].copy()
    out.columns = [c.replace("_"," ").title() for c in out.columns]
    st.dataframe(out.round(2), use_container_width=True, hide_index=True)

    if len(result):
        fig = px.scatter(result, x="std_dev_ann_pct", y="return_3yr_pct",
                         size="aum_crore" if "aum_crore" in result else None,
                         color="risk_grade" if "risk_grade" in result else None,
                         hover_name="scheme_name",
                         title="Screened Funds: Return vs Volatility")
        st.plotly_chart(style_fig(fig,450), use_container_width=True)

# ----------------- Performance & Risk -----------------
elif page == "Performance & Risk":
    st.markdown('<div class="section">Performance & Risk Analytics</div>', unsafe_allow_html=True)
    q = filtered_perf().copy()
    for col in ["return_1yr_pct","return_3yr_pct","return_5yr_pct","std_dev_ann_pct","sharpe_ratio","sortino_ratio","max_drawdown_pct","alpha","beta"]:
        if col in q: q[col] = safe_num(q,col)

    if len(q):
        c1,c2,c3 = st.columns(3)
        best_sh = q.loc[q["sharpe_ratio"].idxmax()]
        best_ret = q.loc[q["return_3yr_pct"].idxmax()]
        lowest_dd = q.loc[q["max_drawdown_pct"].abs().idxmin()]
        c1.metric("Top Sharpe", best_sh["scheme_name"][:28], f"{best_sh['sharpe_ratio']:.2f}")
        c2.metric("Best 3Y Return", best_ret["scheme_name"][:28], f"{best_ret['return_3yr_pct']:.2f}%")
        c3.metric("Lowest Drawdown", lowest_dd["scheme_name"][:28], f"{lowest_dd['max_drawdown_pct']:.2f}%")

        c1,c2 = st.columns(2)
        with c1:
            fig = px.scatter(q, x="std_dev_ann_pct", y="return_3yr_pct",
                             color="risk_grade" if "risk_grade" in q else None,
                             hover_name="scheme_name",
                             title="Risk–Return Map",
                             labels={"std_dev_ann_pct":"Annualized Volatility (%)","return_3yr_pct":"3Y Return (%)"})
            st.plotly_chart(style_fig(fig,430), use_container_width=True)
        with c2:
            top = q.nlargest(10,"sharpe_ratio")
            fig = px.bar(top, x="sharpe_ratio", y="scheme_name", orientation="h", title="Top 10 Risk-Adjusted Leaders")
            st.plotly_chart(style_fig(fig,430), use_container_width=True)

        st.markdown('<div class="section">Fund Risk Scorecard</div>', unsafe_allow_html=True)
        cols = [c for c in ["scheme_name","return_1yr_pct","return_3yr_pct","return_5yr_pct","std_dev_ann_pct","sharpe_ratio","sortino_ratio","max_drawdown_pct","alpha","beta","risk_grade"] if c in q]
        st.dataframe(q[cols].sort_values("sharpe_ratio",ascending=False).round(2), use_container_width=True, hide_index=True)

        if "scheme_name" in q:
            choice = st.selectbox("Inspect a fund", q["scheme_name"].tolist())
            row = q[q["scheme_name"]==choice].iloc[0]
            st.markdown(f"### {choice}")
            cc = st.columns(5)
            metrics = [
                ("1Y Return", row.get("return_1yr_pct",np.nan), "%"),
                ("3Y Return", row.get("return_3yr_pct",np.nan), "%"),
                ("Sharpe", row.get("sharpe_ratio",np.nan), ""),
                ("Sortino", row.get("sortino_ratio",np.nan), ""),
                ("Max Drawdown", row.get("max_drawdown_pct",np.nan), "%"),
            ]
            for c,(lab,val,suf) in zip(cc,metrics):
                c.metric(lab, f"{val:.2f}{suf}" if pd.notna(val) else "—")

            # automated interpretation
            sh = row.get("sharpe_ratio",np.nan)
            vol = row.get("std_dev_ann_pct",np.nan)
            dd = row.get("max_drawdown_pct",np.nan)
            if pd.notna(sh):
                strength = "strong" if sh >= 1.0 else "moderate" if sh >= 0.5 else "relatively weak"
                st.info(f"Analytical insight: this fund shows **{strength} risk-adjusted performance** on the supplied data (Sharpe {sh:.2f}). Evaluate the Sharpe result alongside volatility ({vol:.2f}%) and maximum drawdown ({dd:.2f}%) rather than using any single metric in isolation.")

# ----------------- Investor Analytics -----------------
elif page == "Investor Analytics":
    st.markdown('<div class="section">Investor Behaviour Analytics</div>', unsafe_allow_html=True)
    q = tx.copy()
    q["amount_inr"] = safe_num(q,"amount_inr")
    c1,c2,c3,c4 = st.columns(4)
    c1.metric("Investors", f"{q['investor_id'].nunique():,}" if "investor_id" in q else "—")
    c2.metric("Transaction Value", f"₹{q['amount_inr'].sum()/1e7:,.1f} Cr")
    c3.metric("Avg Ticket Size", f"₹{q['amount_inr'].mean():,.0f}")
    c4.metric("Verified KYC", f"{(q['kyc_status'].eq('Verified').mean()*100):.1f}%" if "kyc_status" in q else "—")

    c1,c2 = st.columns(2)
    with c1:
        mix = q.groupby("transaction_type",as_index=False)["amount_inr"].sum()
        fig=px.pie(mix,names="transaction_type",values="amount_inr",hole=.55,title="Transaction Mix")
        st.plotly_chart(style_fig(fig,380),use_container_width=True)
    with c2:
        state=q.groupby("state",as_index=False)["amount_inr"].sum().nlargest(10,"amount_inr")
        fig=px.bar(state,x="amount_inr",y="state",orientation="h",title="Top States by Transaction Value")
        st.plotly_chart(style_fig(fig,380),use_container_width=True)

    c1,c2,c3 = st.columns(3)
    for c,col,title in [(c1,"age_group","Age Group"),(c2,"city_tier","City Tier"),(c3,"gender","Gender")]:
        if col in q:
            g=q.groupby(col,as_index=False)["amount_inr"].sum()
            fig=px.bar(g,x=col,y="amount_inr",title=title)
            c.plotly_chart(style_fig(fig,320),use_container_width=True)

# ----------------- Portfolio -----------------
elif page == "Portfolio & Holdings":
    st.markdown('<div class="section">Portfolio & Holdings Intelligence</div>', unsafe_allow_html=True)
    q=hold.copy()
    q["market_value_cr"]=safe_num(q,"market_value_cr")
    q["weight_pct"]=safe_num(q,"weight_pct")
    c1,c2,c3=st.columns(3)
    c1.metric("Holding Records",f"{len(q):,}")
    c2.metric("Securities",f"{q['stock_symbol'].nunique():,}" if "stock_symbol" in q else "—")
    c3.metric("Sectors",f"{q['sector'].nunique():,}" if "sector" in q else "—")

    c1,c2=st.columns(2)
    with c1:
        top=q.groupby(["stock_symbol","stock_name"],as_index=False)["market_value_cr"].sum().nlargest(12,"market_value_cr")
        fig=px.bar(top,x="market_value_cr",y="stock_name",orientation="h",title="Largest Holdings by Market Value")
        st.plotly_chart(style_fig(fig,430),use_container_width=True)
    with c2:
        sec=q.groupby("sector",as_index=False)["market_value_cr"].sum().nlargest(10,"market_value_cr")
        fig=px.pie(sec,names="sector",values="market_value_cr",hole=.5,title="Sector Exposure")
        st.plotly_chart(style_fig(fig,430),use_container_width=True)

    st.dataframe(q.sort_values("market_value_cr",ascending=False).head(100).round(2),use_container_width=True,hide_index=True)

# ----------------- Benchmark & Correlation -----------------
else:
    st.markdown('<div class="section">Benchmark & Correlation Analytics</div>', unsafe_allow_html=True)
    st.caption("Use the supplied performance/benchmark fields to examine relationships between fund outcomes and risk measures.")

    q=filtered_perf().copy()
    numeric=[c for c in ["return_1yr_pct","return_3yr_pct","return_5yr_pct","benchmark_3yr_pct","alpha","beta","sharpe_ratio","sortino_ratio","std_dev_ann_pct","max_drawdown_pct"] if c in q]
    for c in numeric: q[c]=safe_num(q,c)

    if "return_3yr_pct" in q and "benchmark_3yr_pct" in q:
        q["fund_vs_benchmark"] = q["return_3yr_pct"] - q["benchmark_3yr_pct"]
        fig=px.histogram(q,x="fund_vs_benchmark",nbins=20,title="3Y Fund Return Minus Benchmark Return",
                         labels={"fund_vs_benchmark":"Fund − Benchmark (%)"})
        st.plotly_chart(style_fig(fig,390),use_container_width=True)

        leaders=q.sort_values("fund_vs_benchmark",ascending=False).head(10)
        fig=px.bar(leaders,x="fund_vs_benchmark",y="scheme_name",orientation="h",title="Largest Positive Benchmark Differences")
        st.plotly_chart(style_fig(fig,390),use_container_width=True)

    if len(numeric)>=3:
        corr=q[numeric].corr()
        fig=px.imshow(corr,text_auto=".2f",aspect="auto",title="Performance & Risk Correlation Matrix")
        st.plotly_chart(style_fig(fig,520),use_container_width=True)

st.divider()
st.caption("MF Analytics Platform • Semester 7 Summer Internship Project • Built with Python, Pandas, SQLite and Plotly")
