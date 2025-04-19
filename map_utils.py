import numpy as np
import folium
import matplotlib.cm as cm
import matplotlib.pyplot as plt
from matplotlib import colors as mcolors
import branca.colormap as bcm
import matplotlib.colors as colors
import matplotlib.colors as mcolors
from folium import Popup

# 1️⃣ 구별 색상 딕셔너리 생성
def generate_gu_colors_func(data_series, base_color="#6A5ACD"):
    norm = mcolors.Normalize(vmin=data_series.min(), vmax=data_series.max())
    base_rgb = np.array(mcolors.to_rgb(base_color))

    def adjust_brightness(factor):
        return np.clip(base_rgb * factor + (1 - factor), 0, 1)
    
    gu_colors = {}
    color_steps = []
    sorted_values = data_series.sort_values()

    for gu in sorted_values.index:
        val = sorted_values[gu]
        factor = norm(val) * 0.7 + 0.3
        gu_rgb = adjust_brightness(factor)
        hex_color = mcolors.to_hex(gu_rgb)
        gu_colors[gu] = hex_color
        color_steps.append(hex_color)

    legend_colors = list(dict.fromkeys(color_steps))
    return gu_colors, legend_colors




# 2️⃣ 범례 함수
def add_color_legend(folium_map, data_series, caption="", colors_used=None):
    if colors_used is None:
        cmap = cm.get_cmap("YlOrRd", 6)
        colors_used = [mcolors.to_hex(cmap(i / 5)) for i in range(6)]

    colormap = bcm.LinearColormap(
        colors=colors_used,
        vmin=data_series.min(),
        vmax=data_series.max(),
        caption=caption
    )
    colormap.add_to(folium_map)


# 3️⃣ GeoJSON 영역을 지도 위에 컬러로 시각화
def draw_gu_colored_map_func(base_map, geojson_data, color_dict, tooltip_key="SIG_KOR_NM"):
    for feature in geojson_data["features"]:
        gu_name = feature["properties"].get(tooltip_key)
        color = color_dict.get(gu_name, "#cccccc")
        folium.GeoJson(
            feature,
            style_function=lambda x, color=color: {
                'fillColor': color,
                'color': 'black',
                'weight': 1,
                'fillOpacity': 0.5
            },
            tooltip=gu_name
        ).add_to(base_map)


# 팝업 노출 함수
def create_store_pop(row):
    popup_html = f"""
    <div style="font-size: 14px; line-height: 1.4;">
        <b>{row['상호명']}</b><br>
        {row['도로명주소']}
    </div>
    """
    popup = Popup(popup_html, max_width=250)
    return folium.Marker(
        location=[row["위도"], row["경도"]],
        popup=popup,
        icon=folium.Icon(color="darkblue", icon="cutlery", prefix="fa")
    )
