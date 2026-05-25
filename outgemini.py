import io
import folium
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
from streamlit_folium import st_folium

# =====================================================================
# 🎨 UI/UX 骨架與基本設定 (必須放在整個程式的第一行)
# =====================================================================
st.set_page_config(
    page_title="德國城市搬遷與生活綜合評估系統", layout="wide"
)

st.markdown(
    """
    <style>
    .main .block-container {
        padding-top: 1.5rem;
        padding-bottom: 1.5rem;
    }
    h1 {
        color: #1E3A8A;
        font-weight: 700;
    }
    </style>
""",
    unsafe_allow_html=True,
)

# =====================================================================
# 💾 核心數據處理區 (已精確微調所有欄位的逗號數量，保證 12 個欄位完美對齊)
# =====================================================================
city_metrics_data = """city_name,chin_name,climate_score,living_cost,ef_epi,safety_index,traffic_accessibility,avg_rent,restuarant_price,local_purchase,lat,lon
Berlin,柏林,83.35,105.5,624.2,55.4,1.6,34.5,69.5,136.4,52.5200,13.4050
Leipzig,萊比錫,82.33,96.4,590.9,54.96,2.22,20.9,61.0,139.1,51.3397,12.3731
Frankfurt an der Oder,奧德河畔法蘭克福,83.95,94.3,587.1,61.67,3.6,27.0,70.0,140.0,52.3412,14.5494
Erfurt,埃爾福特,79.05,98.1,566.4,68.71,2.63,17.6,62.9,140.6,50.9781,11.0292
Göttingen,哥廷根,83.15,98.3,627.9,59.02,4.38,27.0,70.0,140.0,51.5413,9.9158
Kiel,基爾,89.35,97.9,602.0,67.86,2.25,27.0,70.0,140.0,54.3233,10.1228
Köln,科隆,84.85,109.4,623.1,54.96,2.26,27.2,70.1,158.3,50.9375,6.9603
Duisburg/Essen,杜伊斯堡 / 埃森,89.61,96.0,586.9,46.04,2.35,16.0,64.6,139.1,51.4556,7.0116
Trier,特里爾,82.04,104.3,597.9,69.47,2.6,27.0,70.0,140.0,49.7499,6.6371
Heidelberg,海德堡,82.49,111.5,659.3,76.77,1.93,33.1,66.6,120.3,49.3988,8.6724
Mannheim,曼海姆,81.74,104.7,634.4,58.56,2.26,21.1,99.5,56.4,49.4875,8.4660
Konstanz,康斯坦茲,77.96,105.0,646.9,74.19,3.53,27.0,70.0,140.0,47.6779,9.1732
Friedrichshafen,腓特烈港,77.96,104.2,628.2,72.06,3.12,27.0,70.0,140.0,47.6542,9.4794
Karlsruhe,卡爾斯魯厄,81.28,106.0,640.7,63.13,1.74,39.4,68.5,135.6,49.0069,8.4037
Frankfurt,法蘭克福,84.72,115.9,655.1,54.54,3.6,30.1,74.5,175.8,50.1109,8.6821
Würzburg,維爾茨堡,80.62,104.9,627.3,80.98,2.29,27.0,70.0,140.0,49.7913,9.9534
Augsburg,奧格斯堡,75.93,105.2,615.0,70.11,4.48,25.0,70.0,140.3,48.3705,10.8978
Neu-Ulm,新烏爾姆,77.83,102.7,621.1,70.3,4.08,27.0,70.0,140.0,48.3946,10.0033"""


def normalize_column(series, higher_is_better=True):
    min_val = series.min()
    max_val = series.max()
    if max_val == min_val:
        return series.apply(lambda x: 100.0)
    if higher_is_better:
        return ((series - min_val) / (max_val - min_val)) * 100
    else:
        return ((max_val - series) / (max_val - min_val)) * 100


def load_and_process_data():
    df = pd.read_csv(io.StringIO(city_metrics_data.strip()))
    df.columns = df.columns.str.strip()

    column_directions = {
        "climate_score": True,
        "living_cost": False,
        "ef_epi": True,
        "safety_index": True,
        "traffic_accessibility": False,
        "avg_rent": False,
        "restuarant_price": False,
        "local_purchase": True,
    }

    for col, direction in column_directions.items():
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")
            df[col] = df[col].fillna(df[col].mean())
            df[f"{col}_score"] = normalize_column(
                df[col], higher_is_better=direction
            )
    return df


base_df = load_and_process_data().copy()

# =====================================================================
# ⚙️ 側邊欄加權調整區
# =====================================================================
st.sidebar.header("⚙️ 指標權重比例配置 (%)")
st.sidebar.write("拖動滑桿可即時動態觀察右側圖表與排名的變化：")

w_living = st.sidebar.slider("🪙 生活成本權重", 0, 100, 15)
w_rent = st.sidebar.slider("🏠 平均租金權重", 0, 100, 15)
w_climate = st.sidebar.slider("☀️ 氣候舒適權重", 0, 100, 10)
w_english = st.sidebar.slider("🗣️ 英語能力權重", 0, 100, 20)
w_safety = st.sidebar.slider("🛡️ 治安安全權重", 0, 100, 20)
w_traffic = st.sidebar.slider("🚇 交通便利權重", 0, 100, 20)

total_w = w_living + w_rent + w_climate + w_english + w_safety + w_traffic

if total_w == 0:
    st.warning("⚠️ 請至少將一項權重調整至 0% 以上以利計算排名。")
    st.stop()

weights = {
    "living_cost_score": w_living / total_w,
    "avg_rent_score": w_rent / total_w,
    "climate_score_score": w_climate / total_w,
    "ef_epi_score": w_english / total_w,
    "safety_index_score": w_safety / total_w,
    "traffic_accessibility_score": w_traffic / total_w,
}

base_df["total_score"] = 0.0
for score_col, w in weights.items():
    if score_col in base_df.columns:
        base_df["total_score"] += base_df[score_col] * w

df_sorted = base_df.sort_values(by="total_score", ascending=False).reset_index(
    drop=True
)

# =====================================================================
# 🏢 主網頁網格與圖表配置 (Layout & Visualization)
# =====================================================================
st.title("🇩🇪 德國留學生活綜合評估系統")
st.markdown(
    "自訂生活權重，動態演算最適合你的德國留學城市！"
)
st.markdown("---")

row1_col1, row1_col2 = st.columns([1.0, 1.2])

with row1_col1:
    st.subheader("📍 德國城市地理分佈 (點擊地標互動)")
    m = folium.Map(
        location=[51.1657, 10.4515], zoom_start=6, tiles="OpenStreetMap"
    )

    for idx, row in df_sorted.iterrows():
        folium.Marker(
            location=[row["lat"], row["lon"]],
            popup=f"<b>{row['chin_name']}</b><br>綜合總分: {round(row['total_score'], 1)}分",
            tooltip=f"{row['chin_name']} ({row['city_name']})",
        ).add_to(m)

    map_data = st_folium(m, width=500, height=450, key="germany_map_out")

    clicked_city = None
    if map_data and map_data.get("last_object_clicked"):
        c_lat = map_data["last_object_clicked"]["lat"]
        c_lon = map_data["last_object_clicked"]["lng"]
        match = df_sorted[
            (abs(df_sorted["lat"] - c_lat) < 0.01)
            & (abs(df_sorted["lon"] - c_lon) < 0.01)
        ]
        if not match.empty:
            clicked_city = match.iloc[0]

with row1_col2:
    st.subheader("📊 城市綜合得分排行")

    fig_bar = px.bar(
        df_sorted,
        x="total_score",
        y="chin_name",
        orientation="h",
        labels={"total_score": "加權綜合得分", "chin_name": "城市名稱"},
        color="total_score",
        color_continuous_scale="Viridis",
    )
    fig_bar.update_layout(
        yaxis={"categoryorder": "total ascending"},
        height=450,
        margin=dict(l=20, r=20, t=10, b=20),
        coloraxis_showscale=False,
    )
    st.plotly_chart(fig_bar, use_container_width=True)

st.markdown("---")

row2_col1, row2_col2 = st.columns([1.0, 1.2])

with row2_col1:
    st.subheader("🎯 城市核心指標強弱分析")

    if clicked_city is None:
        target_city = df_sorted.iloc[0]
        st.info(
            f"💡 提示：目前展示第 1 名【{target_city['chin_name']}】的雷達圖。點擊上方地圖藍色地標可自由切換城市！"
        )
    else:
        target_city = clicked_city
        st.success(f"🎯 已成功切換至【{target_city['chin_name']}】的詳細指標分析！")

    categories = [
        "氣候舒適度",
        "生活成本低廉度",
        "英語熟練度",
        "治安安全度",
        "交通便利度",
        "租金便宜度",
    ]
    scores = [
        target_city["climate_score_score"],
        target_city["living_cost_score"],
        target_city["ef_epi_score"],
        target_city["safety_index_score"],
        target_city["traffic_accessibility_score"],
        target_city["avg_rent_score"],
    ]

    fig_radar = go.Figure()
    fig_radar.add_trace(
        go.Scatterpolar(
            r=scores + [scores[0]],
            theta=categories + [categories[0]],
            fill="toself",
            name=target_city["chin_name"],
            fillcolor="rgba(30, 58, 138, 0.2)",
            line=dict(color="#1E3A8A", width=2.5),
        )
    )
    fig_radar.update_layout(
        polar=dict(radialaxis=dict(visible=True, range=[0, 100])),
        showlegend=False,
        height=380,
        margin=dict(l=45, r=45, t=30, b=30),
    )
    st.plotly_chart(fig_radar, use_container_width=True)

with row2_col2:
    st.subheader("📋 城市標準化綜合數據表")

    df_disp = df_sorted[
        [
            "chin_name",
            "city_name",
            "total_score",
            "climate_score_score",
            "living_cost_score",
            "ef_epi_score",
            "safety_index_score",
            "traffic_accessibility_score",
            "avg_rent_score",
        ]
    ].copy()

    df_disp.columns = [
        "中文名稱",
        "英文名稱",
        "綜合總分 🏆",
        "氣候舒適",
        "生活成本",
        "英語能力",
        "治安安全",
        "交通便利",
        "租金便宜",
    ]
    df_disp = df_disp.round(1)

    st.success(
        f"🏆 系統推薦首選城市為：**{df_disp.iloc[0]['中文名稱']}** ({df_disp.iloc[0]['綜合總分 🏆']} 分)"
    )

    st.dataframe(df_disp, use_container_width=True, hide_index=True, height=310)

st.caption(
    "註：所有單項得分均已轉化為 0 - 100 標準分數。分數越高代表在該指標表現越優秀。"
)
