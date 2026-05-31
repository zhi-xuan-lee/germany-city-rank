import pandas as pd

def load_and_clean_data():
    # 讀取資料
    df = pd.read_csv("data/cities_data.csv")

    # 確保所有計算欄位都是數字格式 (防呆機制)
    df['rent_price'] = pd.to_numeric(df['rent_price'], errors='coerce')
    # 將缺失值(NaN)填補為該欄位的平均數，避免程式當機
    df.fillna(df.mean(numeric_only=True), inplace=True) 

    return df

import pandas as pd

def get_final_ranking(weight_rent, weight_safety):
    """
    這就是後台的大腦（配方）。
    它接收兩個變數：weight_rent (房租權重) 和 weight_safety (治安權重)
    """
    # 1. 拿取處理好的基礎數據 (通常是角色二和三已經整理好的 0-100 分標準化數據)
    data = {
        'City': ['慕尼黑', '柏林', '法蘭克福'],
        'rent_score': [20, 40, 30], # 分數越高代表房租越便宜
        'safety_score': [85, 60, 65]
    }
    df = pd.DataFrame(data)

    # 2. 進行加權計算 (套用使用者傳進來的權重)
    total_weight = weight_rent + weight_safety
    df['final_score'] = (df['rent_score'] * weight_rent + df['safety_score'] * weight_safety) / total_weight

    # 3. 依照總分由高到低排序
    sorted_df = df.sort_values(by='final_score', ascending=False)

    # 4. 關鍵：把排好序的資料表丟出去
    return sorted_df
