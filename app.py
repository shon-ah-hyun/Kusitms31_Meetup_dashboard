#  Local URL: http://localhost:8518
#  Network URL: http://192.168.0.12:8518

import streamlit as st
import pandas as pd
import json

import folium
# from streamlit_folium import folium_static
from streamlit_folium import st_folium
from folium.plugins import MarkerCluster
import matplotlib.cm as cm
import matplotlib.colors as colors
from folium.features import GeoJson
from folium.features import DivIcon
from shapely.geometry import shape
from data_merge import compute_top5_table
from map_utils import generate_gu_colors_func, draw_gu_colored_map_func, add_color_legend, create_store_pop


# -----------------------------
# 📂 데이터 불러오기
# -----------------------------
MERGED_DATA_PATH = "data/merged_store_pop_data.csv"
STORE_DATA_PATH = "data/seoul_store_data.csv"
GEOJSON_PATH = "data/서울_시군구.geojson"

### (1) merged df
df = pd.read_csv(MERGED_DATA_PATH)
### (2) store df
store_df = pd.read_csv(STORE_DATA_PATH)
### (3) Geojson df
with open(GEOJSON_PATH, encoding="utf-8") as f:
    geo = json.load(f)

# # # -----------------------------
# # # 🌍 중심좌표
# # # -----------------------------
# map_center = [37.5665, 126.9780]


# -----------------------------
# 🌐 공통 UI/설정
# -----------------------------
st.set_page_config(layout="wide", page_icon='🎂', page_title='Dear.K 타겟 분석')
st.title("🎂 Dear.K")
st.title("레터링/주문제작 케이크 - 영업전략 대시보드")
st.subheader("우리 서비스가 **가장 효과적으로 작동할 수 있는 지역과 스토어들**을 확인하세요!")

with st.expander("ℹ️ 대시보드 설명", expanded=False):
    st.markdown("""
    **🎯 우리의 영업 대상이 될 스토어를 찾는 기준**
    1. **구에 스토어가 많은 경우**
        - 경쟁이 많아 사용자가 "검색/비교/탐색"에 피로를 느낌
        - 이럴수록 입점 유도는 **“차별화” + “노출 효과”** 강조
    2. **인구는 많은 경우**
        - 예약 경쟁 심해짐 → **예약 탐색 기능**에 대한 니즈 커짐
        - 생활인구수 많을수록 → 유입 사용자도 많음 → UX 서비스 가치 큼
    ⇒ **서비스 필요도 점수**가 높은 지역
        - 위 둘의 특징을 반영한 지표
        - 우리 서비스가 가장 “필요해 보이는 곳”
        > **서비스 필요도 점수 = 스토어 수 * 2030 생활인구수**
    """)


with st.container():
    st.markdown("### 📌 핵심 지표 요약")

    # 5개의 카드 레이아웃
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        # 서비스 필요도 점수 기준 Top 1 구
        top_gu = df.sort_values("서비스 필요도 점수", ascending=False)["시군구명"].iloc[0]
        st.metric(label="🎯 타겟 지역 (1위)", value=top_gu)

    with col2:
        # 등록된 스토어 수
        st.metric(label="🏪 등록 스토어 수", value=f"{len(store_df)}개")
        st.markdown("⚠️ 현재 스토어 수는 카카오 API 제한으로, 구당 최대 45개까지만 반영된 수치입니다.")

    with col3:
        # 2030 생활인구 수 총합
        total_population = df["전체_2030"].sum().round(1)
        st.metric(label="👥 2030 생활인구 수", value=f"{total_population}명")

    with col4:
        # 인구 대비 스토어 수 비율 (평균)
        ratio = df["전체_2030"] / df["매장 수"]
        st.metric(label="📊 서울 인구 대비 스토어 비율", value=f"{ratio.mean():.2f} (평균)")






map_center = [37.5665, 126.9780]
gu_names = sorted(df["시군구명"].unique())


# -----------------------------
# 📌 탭 구분 - 분석 모드 선택
# -----------------------------
st.subheader("📌 보기 설정")
tab1, tab2 = st.tabs(["📍 스토어 분석", "👥 인구 분석"])



# ----------------------------------------------------------
# 📍 스토어 분석 모드
# ----------------------------------------------------------
with tab1:
    st.subheader("📍 시군구별 스토어 분포 및 서비스 필요도 순위")
    st.markdown("⚠️ 현재 스토어 수는 카카오 API 제한으로 최대 45개까지만 반영된 수치입니다. (구당 최대 45개)")

    metric_store_option = st.radio(
        "지도에 표시할 기준을 선택하세요",
        ["서비스 필요도 점수", "스토어 수"], horizontal=True )
    st.markdown("""
        **서비스 필요도 점수**는 스토어 수와 생활인구를 곱한 지표입니다.  
        → 스토어가 많고, 인구가 많을수록 우리 서비스의 가치가 커지는 지역입니다.
        """)

    # -----------------------------------------------------
    # 📍 2열 레이아웃 (좌)
    # -----------------------------------------------------
    col_map, col_rank = st.columns([3, 2])  # 지도와 우측 순위표
    with col_map:  

        # 1️⃣ 지도 생성        
        if metric_store_option == "스토어 수":
            store_counts = store_df["시군구명"].value_counts().reindex(gu_names).fillna(0)
            values = store_counts
        else:
            values = df.set_index("시군구명")["서비스 필요도 점수"].reindex(gu_names).fillna(0)
    
        # ✅ 색상값 생성 + 지도 렌더링
        gu_colors, legend_colors = generate_gu_colors_func(values)

        # ✅ 지도 객체 생성 및 시각화
        m_store = folium.Map(location=map_center, zoom_start=11)
        add_color_legend(m_store, values, caption=metric_store_option + " (컬러 범례)", colors_used=legend_colors)
        draw_gu_colored_map_func(m_store, geo, gu_colors)


        # ✅ 서비스 필요도 점수 기준 상위 5개 구 추출 및 지도에 랭킹 표시
        top5 = values.sort_values(ascending=False).head(5)

        for rank, (gu, _) in enumerate(top5.items(), start=1):
            # 각 feature에서 geometry 중심 추출
            for feature in geo["features"]:
                if feature["properties"]["SIG_KOR_NM"] == gu:
                    geom = shape(feature["geometry"])  # 이게 polygon이나 multipolygon으로 자동 처리됨
                    lat, lon = geom.centroid.y, geom.centroid.x
                    # 텍스트를 중심에 넣는 코드 (배경 없고, 중앙 위치)
                    folium.Marker(
                        location=[lat, lon],
                        icon=DivIcon(
                            icon_size=(30, 30),
                            icon_anchor=(15, 15),
                            html=f"""
                                <div style="
                                    font-size: 18px;
                                    font-weight: bold;
                                    color: black;
                                    text-align: center;">
                                    {rank}
                                </div>
                            """
                            )
                        ).add_to(m_store)

        # ✅ 마커 클러스터링
        marker_cluster_all = MarkerCluster().add_to(m_store)
        for _, row in store_df.iterrows():
            marker = create_store_pop(row)
            marker.add_to(marker_cluster_all)

        st_folium(m_store, width=1100, height=600)

    # -----------------------------------------------------
    # 📍 2열 레이아웃 (우)
    # -----------------------------------------------------
    with col_rank:
        # 2️⃣ Top 5 데이터프레임
        st.markdown("#### 🏆 '서비스 필요도 점수' 기준 Top 5 시군구")
        top5_df = compute_top5_table(store_df, df, gu_names, metric="서비스 필요도 점수")
        st.dataframe(top5_df, use_container_width=True)#, height=300)

        st.markdown("#### 🏆 '스토어 수' 기준 Top 5 시군구")
        top5_store_df = compute_top5_table(store_df, df, gu_names, metric="스토어 수")
        st.dataframe(top5_store_df, use_container_width=True, height=250)

    # 3️⃣ 구별 스토어 데이터프레임
    st.subheader("🏪 구별 스토어 리스트")
    selected_gu = st.selectbox("구 선택", ["전체"] + gu_names)
    filtered_df = store_df if selected_gu == "전체" else store_df[store_df["시군구명"] == selected_gu]

    st.write(f"총 {len(filtered_df)}개 스토어")
    st.dataframe(filtered_df[["시군구명", "상호명", "도로명주소", "위도", "경도"]].reset_index(drop=True))


# ----------------------------------------------------------
# 👩‍👦 인구 분석 모드
# ----------------------------------------------------------
# 👥 인구 분석 모드
with tab2:
    st.subheader("👥 생활인구 기반 분석 & 스토어 위치")
    
    # (1) 지표 선택
    metric_pop_option = st.radio(
        "시각화할 인구 지표를 선택하세요",
        ["전체_2030", "여자_2030", "남자_2030", "여성비율"],
        horizontal=True
    )

    color_map = {
        "전체_2030": "#6A5ACD",  # 보라
        "여자_2030": "#FF69B4",  # 핑크
        "남자_2030": "#1E90FF",  # 파랑
        "여성비율": "#FFA07A",   # 살구
    }
    selected_color = color_map.get(metric_pop_option, "#888888")

    st.markdown(f"ℹ️ 지도는 `{metric_pop_option}` 기준 색상 + 선택 시 스토어 위치도 표시됩니다.")
    show_stores = st.toggle("🗺️ 스토어 위치 표시하기", value=False)

    # (2) 지도 & 데이터 계산
    metric_values = df.set_index("시군구명")[metric_pop_option].reindex(gu_names).fillna(0)
    gu_colors, legend_colors = generate_gu_colors_func(metric_values, base_color=selected_color)
    
    # 지도 생성
    m_metric = folium.Map(location=map_center, zoom_start=11)
    add_color_legend(m_metric, metric_values, caption=metric_pop_option + " (컬러 범례)", colors_used=legend_colors)
    draw_gu_colored_map_func(m_metric, geo, gu_colors)

    # (3) 지도에 상위 5개 구 마킹
    top5 = metric_values.sort_values(ascending=False).head(5)
    for rank, (gu, _) in enumerate(top5.items(), start=1):
        for feature in geo["features"]:
            if feature["properties"]["SIG_KOR_NM"] == gu:
                geom = shape(feature["geometry"])
                lat, lon = geom.centroid.y, geom.centroid.x
                folium.Marker(
                    location=[lat, lon],
                    icon=DivIcon(
                        icon_size=(30, 30),
                        icon_anchor=(15, 15),
                        html=f"""
                            <div style="
                                font-size: 18px;
                                font-weight: bold;
                                color: black;
                                text-align: center;">
                                {rank}
                            </div>
                        """
                    )
                ).add_to(m_metric)

    # (4) 마커 표시 (옵션)
    if show_stores:
        for _, row in store_df.iterrows():
            marker = create_store_pop(row)
            marker.add_to(m_metric)

    # (5) 지도 + 데이터프레임을 두 열로 배치
    col_map, col_data = st.columns([3, 2])
    with col_map:
        st_folium(m_metric, width=1000, height=600)

    with col_data:
        st.markdown(f"#### 📊 `{metric_pop_option}` 기준 Top 5 시군구")
        top5_df = (
            metric_values.reset_index()
            .rename(columns={metric_pop_option: "값"})
            .sort_values(by="값", ascending=False)
            .head(5)
            .reset_index(drop=True)  # 0부터 다시 시작하는 인덱스 제거
        )

        top5_df.index = top5_df.index + 1  # 인덱스를 1부터 시작하게 설정
        top5_df.index.name = "순위"

        st.dataframe(top5_df, use_container_width=True)
