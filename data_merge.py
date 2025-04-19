import pandas as pd
import json
from shapely.geometry import shape

# --------- [1] 데이터 경로 설정 ---------
POP_PATH = "data/seoul_pop_data.csv"
STORE_PATH = "data/seoul_store_data.csv"
GEO_PATH = "data/서울_시군구.geojson"
MERGE_PATH = "data/merged_store_pop_data.csv"

# --------- [2] GeoJSON에서 시군구 중심 좌표 추출 ---------
def extract_centers(geojson_path):
    with open(geojson_path, encoding='utf-8') as f:
        geo = json.load(f)

    rows = []
    for feature in geo['features']:
        geom = shape(feature['geometry'])
        name = feature['properties']['SIG_KOR_NM']
        rows.append({
            '시군구명': name,
            '위도': geom.centroid.y,
            '경도': geom.centroid.x
        })

    return pd.DataFrame(rows)

# --------- [3] 병합 처리 ---------
def merge_data(pop_path, store_path, geo_path, merge_path):
    # 인구 & 매장 데이터 로드
    df_pop = pd.read_csv(pop_path)
    df_store = pd.read_csv(store_path)

    # 중심 좌표 추출
    df_center = extract_centers(geo_path)

    # 인구 + 중심 좌표 merge
    df_pop = pd.merge(df_pop, df_center, on='시군구명', how='left')

    # 매장 수 집계
    df_store_count = df_store.groupby("시군구명").size().reset_index(name="매장 수")

    # 최종 merge
    df_merged = pd.merge(df_pop, df_store_count, on="시군구명", how="left")
    df_merged["매장 수"] = df_merged["매장 수"].fillna(0).astype(int)

    # 컬럼 추가  
    df_merged["서비스 필요도 점수"] = df_merged["전체_2030"] * df_merged["매장 수"]


# --------- [4] 저장 및 실행 ---------
    # 저장
    ## 인구 + 매장 수 + 중심 좌표 병합 및 저장
    df_merged.to_csv(merge_path, index=False)
    print(f"[✅ 병합 완료] 파일 저장됨: {merge_path}")


# --------- [5] Top5 분석 테이블 생성 ---------
def compute_top5_table(df_store, df_merged, gu_names, metric="서비스 필요도 점수"):
    store_counts = df_store["시군구명"].value_counts().reindex(gu_names).fillna(0)
    population = df_merged.set_index("시군구명")["전체_2030"].reindex(gu_names).fillna(0)
    score = store_counts * population
    ratio = population / store_counts.replace(0, 1)

    full_df = pd.DataFrame({
        "스토어 수": store_counts,
        "2030 생활인구수": population,
        "인구 대비 스토어 수": ratio.round(1),
        "서비스 필요도 점수": score
    })

    # 선택된 기준으로 정렬
    if metric in full_df.columns:
        sorted_df = full_df.sort_values(metric, ascending=False).head(5)
    else:
        sorted_df = full_df.sort_values("서비스 필요도 점수", ascending=False).head(5)

    sorted_df.index.name = "시군구명"
    sorted_df.reset_index(inplace=True)
    sorted_df.index = sorted_df.index + 1
    return sorted_df



if __name__ == "__main__":
    merge_data(POP_PATH, STORE_PATH, GEO_PATH, MERGE_PATH)
