import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
import random
from datetime import datetime, timedelta

# --- 1. ユーザー別個別設定 ---
# ここでそれぞれの目標期日とリストの形式を設定します
USER_CONFIG = {
    "佐藤": {
        "deadline": datetime(2026, 8, 22).date(),
        "structure": [
            ("理論2023", "静電気", 15), ("理論2023", "磁気", 15), ("理論2023", "直流回路", 15),
            ("理論2023", "交流回路", 15), ("理論2023", "過渡現象", 15), ("理論2023", "電気計測", 15),
            ("理論2023", "半導体・電子回路", 24), ("理論2023", "電子理論・その他", 6),
            ("機械2024", "直流機", 2), ("機械2024", "誘導機", 13), ("機械2024", "同期機", 13),
            ("機械2024", "変圧器", 10), ("機械2024", "保護機器", 4), ("機械2024", "パワエレ", 15),
            ("機械2024", "照明", 15), ("機械2024", "電熱", 13), ("機械2024", "電気化学", 12),
            ("機械2024", "自動制御", 4), ("機械2024", "情報", 13), ("機械2024", "電気鉄道", 5), ("機械2024", "その他", 1),
            ("機械H25", "直流機", 6), ("機械H25", "誘導機", 15), ("機械H25", "同期機", 12),
            ("機械H25", "変圧器", 10), ("機械H25", "保護機器", 7), ("機械H25", "パワエレ", 15),
            ("機械H25", "照明", 13), ("機械H25", "電熱", 5), ("機械H25", "電気化学", 8),
            ("機械H25", "電動力応用", 1), ("機械H25", "自動制御", 10), ("機械H25", "情報", 16),
            ("機械H25", "電気鉄道", 1), ("機械H25", "その他", 1),
            ("電力2022", "水力発電", 13), ("電力2022", "汽力発電", 12), ("電力2022", "原子力発電", 2),
            ("電力2022", "発電一般・その他", 15), ("電力2022", "変電", 18), ("電力2022", "送電", 30), ("電力2022", "配電", 15),
            ("電力H25", "水力発電", 11), ("電力H25", "汽力発電", 18), ("電力H25", "原子力発電", 5),
            ("電力H25", "発電一般・その他", 14), ("電力H25", "変電", 19), ("電力H25", "送電", 26), ("電力H25", "配電", 12),
            ("法規2024", "電気事業法関連", 22), ("法規2024", "電気設備技術基準", 55), ("法規2024", "施設管理", 28),
            ("法規2024H27", "電気事業法関連", 26), ("法規2024H27", "電気設備技術基準", 47), ("法規2024H27", "施設管理", 32)
        ]
    },
    "稲垣": {
        "deadline": datetime(2026, 9, 1).date(), # 暫定の期日
        "structure": [
            ("理論", "直流回路", 1, 24), ("理論", "静電気", 25, 50), ("理論", "電磁力", 51, 70),
            ("理論", "交流回路", 71, 107), ("理論", "三相交流回路", 108, 120), ("理論", "過渡現象とその他の波形", 121, 130),
            ("理論", "電子理論", 131, 156), ("理論", "電気測定", 157, 172),
            ("機械", "直流機", 1, 22), ("機械", "変圧器", 23, 41), ("機械", "誘導機", 42, 61),
            ("機械", "同期機", 62, 84), ("機械", "パワエレ", 85, 103), ("機械", "自動制御", 104, 113),
            ("機械", "情報", 114, 122), ("機械", "照明", 123, 128), ("機械", "電熱", 129, 137),
            ("機械", "電動機応用", 138, 146), ("機械", "電気化学", 147, 157),
            ("電力", "水力発電", 1, 12), ("電力", "火力発電", 13, 42), ("電力", "原子力発電", 43, 56),
            ("電力", "その他の発電", 57, 68), ("電力", "変電", 69, 89), ("電力", "送電", 90, 101),
            ("電力", "配電", 102, 117), ("電力", "地中電線路", 118, 125), ("電力", "電気材料", 126, 141),
            ("電力", "電力計算", 142, 168), ("電力", "線路計算", 169, 172), ("電力", "電線のたるみと支線", 173, 175),
            ("法規", "電気事業法", 1, 13), ("法規", "その他の電気関係法規", 14, 17),
            ("法規", "電気設備の技術基準・解釈", 18, 31), ("法規", "電気設備技術基準(計算)", 32, 54),
            ("法規", "発電用風力設備の技術基準", 55, 57), ("法規", "電気施設管理", 58, 91)
        ]
    },
    "風穴": {
        "deadline": datetime(2026, 10, 15).date(), # 暫定の期日
        "structure": [
            # 稲垣さんと同じ構成
            ("理論", "直流回路", 1, 24), ("理論", "静電気", 25, 50), ("理論", "電磁力", 51, 70),
            ("理論", "交流回路", 71, 107), ("理論", "三相交流回路", 108, 120), ("理論", "過渡現象とその他の波形", 121, 130),
            ("理論", "電子理論", 131, 156), ("理論", "電気測定", 157, 172),
            ("機械", "直流機", 1, 22), ("機械", "変圧器", 23, 41), ("機械", "誘導機", 42, 61),
            ("機械", "同期機", 62, 84), ("機械", "パワエレ", 85, 103), ("機械", "自動制御", 104, 113),
            ("機械", "情報", 114, 122), ("機械", "照明", 123, 128), ("機械", "電熱", 129, 137),
            ("機械", "電動機応用", 138, 146), ("機械", "電気化学", 147, 157),
            ("電力", "水力発電", 1, 12), ("電力", "火力発電", 13, 42), ("電力", "原子力発電", 43, 56),
            ("電力", "その他の発電", 57, 68), ("電力", "変電", 69, 89), ("電力", "送電", 90, 101),
            ("電力", "配電", 102, 117), ("電力", "地中電線路", 118, 125), ("電力", "電気材料", 126, 141),
            ("電力", "電力計算", 142, 168), ("電力", "線路計算", 169, 172), ("電力", "電線のたるみと支線", 173, 175),
            ("法規", "電気事業法", 1, 13), ("法規", "その他の電気関係法規", 14, 17),
            ("法規", "電気設備の技術基準・解釈", 18, 31), ("法規", "電気設備技術基準(計算)", 32, 54),
            ("法規", "発電用風力設備の技術基準", 55, 57), ("法規", "電気施設管理", 58, 91)
        ]
    }
}

INTERVALS = {0: 0, 1: 1, 2: 3, 3: 7, 4: 14, 5: 30}

# --- 2. データベース接続関数 ---
conn = st.connection("gsheets", type=GSheetsConnection)
target_url = st.secrets["connections"]["gsheets"]["spreadsheet"]

def load_full_data():
    try:
        # 見出し: user, field, q_num, level, last_date (計5列)
        df = conn.read(spreadsheet=target_url, worksheet="Sheet1", usecols=[0, 1, 2, 3, 4])
        return df.dropna(how="all")
    except:
        return pd.DataFrame(columns=["user", "field", "q_num", "level", "last_date"])

def sync_user_data(full_df, user_name):
    """ユーザーごとのリスト形式（3項か4項か）を判別して同期"""
    user_df = full_df[full_df['user'] == user_name]
    existing_q = set(user_df['field'] + "_" + user_df['q_num'])
    
    structure = USER_CONFIG[user_name]["structure"]
    new_rows = []
    
    for item in structure:
        field = item[0]
        cat = item[1]
        # 形式判定：(field, cat, count) か (field, cat, start, end) か
        if len(item) == 3:
            start, end = 1, item[2]
        else:
            start, end = item[2], item[3]
            
        for i in range(start, end + 1):
            q_id = f"{cat}No{i}"
            if f"{field}_{q_id}" not in existing_q:
                new_rows.append({"user": user_name, "field": field, "q_num": q_id, "level": 0, "last_date": ""})
    
    if new_rows:
        updated_user_df = pd.concat([user_df, pd.DataFrame(new_rows)], ignore_index=True)
        other_users = full_df[full_df['user'] != user_name]
        new_full = pd.concat([other_users, updated_user_df], ignore_index=True)
        conn.update(spreadsheet=target_url, worksheet="Sheet1", data=new_full)
        return updated_user_df
    return user_df

# --- 3. UI構築 ---
st.set_page_config(page_title="電験 学習マネージャー", layout="centered", page_icon="⚡")

# ユーザー選択
st.sidebar.title("👤 ユーザー設定")
current_user = st.sidebar.selectbox("利用者を選択", list(USER_CONFIG.keys()))
target_date = USER_CONFIG[current_user]["deadline"]

# データの読み込み管理
if 'last_user' not in st.session_state or st.session_state.last_user != current_user:
    with st.spinner(f"{current_user}さんのデータを読み込み中..."):
        full_data = load_full_data()
        st.session_state.db = sync_user_data(full_data, current_user)
        st.session_state.last_user = current_user
        st.session_state.test_pool = []
        st.session_state.history = []

db = st.session_state.db

# メニュー切り替え
st.sidebar.divider()
mode_select = st.sidebar.radio("機能", ["学習モード", "復習モード", "分析ダッシュボード"])

# 進捗・ノルマ計算
today_dt = datetime.today().date()
days_left = (target_date - today_dt).days
unstarted_list = [q for q in db.to_dict('records') if str(q.get("last_date", "")) in ["", "nan", "None", "NaN"]]
total_count = len(db)
answered_count = total_count - len(unstarted_list)

st.sidebar.metric("目標期日までの日数", f"{max(0, days_left)}日")
st.sidebar.progress(answered_count / total_count if total_count > 0 else 0)
st.sidebar.caption(f"全体進捗: {answered_count}/{total_count} ({answered_count/total_count*100:.1f}%)")

if mode_select == "学習モード":
    st.title(f"⚡ 学習：{current_user}")
    fields = ["すべて"] + list(db['field'].unique())
    selected_field = st.selectbox("分野を選択", fields)
    
    # 未着手のみ、リストの順番通りに抽出
    pool = [q for q in unstarted_list if selected_field == "すべて" or q["field"] == selected_field]
    
    if days_left > 0:
        quota = -(-len(pool) // days_left) if pool else 0
        st.info(f"📅 期日：{target_date}　今日のノルマ：**{quota}問**")
        if quota > 0:
            st.warning(f"🚩 本日の目標：{pool[0]['q_num']} 〜 {pool[min(quota-1, len(pool)-1)]['q_num']}")

    if st.button("🚀 学習開始", use_container_width=True):
        st.session_state.test_pool = pool
        st.session_state.history = []
        st.rerun()

elif mode_select == "復習モード":
    st.title(f"🔄 復習：{current_user}")
    review_pool = [q for q in db.to_dict('records') if str(q.get("last_date", "")) not in ["", "nan", "None", "NaN"] and int(float(q.get("level", 0))) < 5]
    review_pool.sort(key=lambda x: int(float(x.get("level", 0))))
    
    st.metric("復習が必要な問題", f"{len(review_pool)}問")
    if st.button("🔥 復習開始", use_container_width=True):
        st.session_state.test_pool = review_pool
        st.session_state.history = []
        st.rerun()

else:
    # --- 分析 ---
    st.title("📊 分析："+current_user)
    df_ana = db.copy()
    df_ana['level'] = pd.to_numeric(df_ana['level']).fillna(0)
    df_ana['単元'] = df_ana['q_num'].str.split('No').str[0]
    
    res = df_ana.groupby(['field', '単元']).agg(
        total=('q_num', 'count'),
        correct=('level', lambda x: (x >= 3).sum()),
        done=('last_date', lambda x: (x.astype(str) != "nan").sum())
    ).reset_index()
    res['正答率'] = (res['correct'] / res['total'] * 100).round(1)

    st.subheader("📈 科目別の平均正答率")
    st.bar_chart(res.groupby('field')['正答率'].mean())

    st.subheader("🚩 弱点克服ランキング")
    worst = res[res['done'] > 0].sort_values('正答率').head(10)
    if not worst.empty:
        for i, r in enumerate(worst.itertuples(), 1):
            st.error(f"{i}位: {r.field} / {r.単元} ({r.正答率}%)")
    else:
        st.info("データがたまると、ここに苦手単元が表示されます。")

# --- 4. 共通の問題表示 ---
if mode_select in ["学習モード", "復習モード"] and st.session_state.test_pool:
    st.divider()
    curr = st.session_state.test_pool[0]
    st.subheader(f"【{curr['field']}】")
    st.header(curr['q_num'])
    
    cols = st.columns(6)
    for i in range(6):
        if cols[i].button(f"{i}点", key=f"b{i}"):
            st.session_state.history.append({"q_num": curr["q_num"], "field": curr["field"], "old_level": curr.get("level", 0), "old_date": curr.get("last_date", "")})
            
            # DB更新
            idx = st.session_state.db[(st.session_state.db['q_num'] == curr['q_num']) & (st.session_state.db['field'] == curr['field'])].index
            st.session_state.db.loc[idx, 'level'] = i
            st.session_state.db.loc[idx, 'last_date'] = datetime.today().strftime('%Y-%m-%d')
            
            # 全体保存
            full_df = load_full_data()
            other_users = full_df[full_df['user'] != current_user]
            new_full = pd.concat([other_users, st.session_state.db], ignore_index=True)
            conn.update(spreadsheet=target_url, worksheet="Sheet1", data=new_full)
            
            st.session_state.test_pool.pop(0)
            st.rerun()

    if st.button("⏭️ スキップ"):
        st.session_state.test_pool.append(st.session_state.test_pool.pop(0))
        st.rerun()
