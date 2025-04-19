import pandas as pd
import json

def load_population_data(file_path):
    df = pd.read_csv(file_path)
    df['남자_2030'] = df[['남자20세부터24세','남자25세부터29세','남자30세부터34세','남자35세부터39세']].sum(axis=1)
    df['여자_2030'] = df[['여자20세부터24세','여자25세부터29세','여자30세부터34세','여자35세부터39세']].sum(axis=1)
    df['전체_2030'] = df['남자_2030'] + df['여자_2030']
    df['여성비율'] = df['여자_2030'] / df['전체_2030']
    df['여초_차이'] = df['여자_2030'] - df['남자_2030']
    df_grouped = df.groupby('시군구명')[['남자_2030','여자_2030','전체_2030','여성비율','여초_차이']].mean().reset_index()
    return df_grouped

def load_geojson(path):
    with open(path, encoding='utf-8') as f:
        return json.load(f)
    

# 1. 파일 불러오기
df_pop = load_population_data("data/LOCAL_PEOPLE_DONG/preprocessed_LOCAL_PEOPLE_DONG_all.csv")

# 2. 저장
df_pop.to_csv("data/seoul_pop_data.csv", index=False)
print("병합 완료! 저장됨 ✅")