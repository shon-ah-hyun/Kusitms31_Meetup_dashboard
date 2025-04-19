# import folium
import requests
from data_pop import load_population_data
import pandas as pd
import time
import os
print("현재 작업 디렉토리:", os.getcwd())


df_pop = load_population_data("../../data/LOCAL_PEOPLE_DONG/preprocessed_LOCAL_PEOPLE_DONG_all.csv")
gu_list = df_pop['시군구명'].unique().tolist()

# 1. 카카오 API 키 설정
KAKAO_API_KEY = "7568cb481e91a75050665e84297b6ec5"
HEADERS = {"Authorization": f"KakaoAK {KAKAO_API_KEY}"}

# 2. 스토어 탐색
def search_stores(keyword, location, size=15):
    url = "https://dapi.kakao.com/v2/local/search/keyword.json"
    stores = []
    page = 1
    while True:
        params = {
            "query": f"{location} {keyword}",
            "page": page,
            "size": size
        }
        res = requests.get(url, headers=HEADERS, params=params)
        data = res.json()
        stores += data['documents']
        if not data['meta']['is_end']:
            page += 1
            time.sleep(0.3)  # 과호출 방지
        else:
            break
    return stores

# 3. 스토어 위치 수집
def collect_seoul_store_data(gu_list, keyword="레터링 케이크"):
    results = []
    for gu in gu_list:
        stores = search_stores(keyword, f"서울 {gu}")
        for s in stores:
            results.append({
                "시군구명": gu,
                "상호명": s['place_name'],
                "도로명주소": s.get('road_address_name', ''),
                "위도": float(s['y']),
                "경도": float(s['x'])
            })
        time.sleep(0.5)
    return results

# 데이터 수집 스크립트 (별도 실행)
store_data = collect_seoul_store_data(gu_list, keyword="레터링 케이크")
df_store = pd.DataFrame(store_data)
df_store.to_csv("data/seoul_store_data.csv", index=False)
print('csv 추출 완료')