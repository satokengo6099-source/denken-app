import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
import random
from datetime import datetime, timedelta

# --- 1. データ管理の設定 ---
INTERVALS = {0: 0, 1: 1, 2: 3, 3: 7, 4: 14, 5: 30}

def get_master_structure():
    """全科目のマスター構成を定義（分野, カテゴリ, 問題数）"""
    return [
        # --- 理論2023 ---
        ("理論2023", "静電気", 15),
        ("理論2023", "磁気", 15),
        ("理論2023", "直流回路", 15),
        ("理論2023", "交流回路", 15),
        ("理論2023", "過渡現象", 15),
        ("理論2023", "電気計測", 15),
        ("理論2023", "半導体・電子回路", 24),
        ("理論2023", "電子理論・その他", 6),
        
        # --- 機械2024 ---
        ("機械2024", "直流機", 2),
        ("機械2024", "誘導機", 13),
        ("機械2024", "同期機", 13),
        ("機械2024", "変圧器", 10),
        ("機械2024", "保護機器", 4),
        ("機械2024", "パワエレ", 15),
        ("機械2024", "照明", 15),
        ("機械2024", "電熱", 13),
        ("機械2024", "電気化学", 12),
        ("機械2024", "自動制御", 4),
        ("機械2024", "情報", 13),
        ("機械2024", "電気鉄道", 5),
        ("機械2024", "その他", 1),

        # --- 機械H25 ---
        ("機械H25", "直流機", 6),
        ("機械H25", "誘導機", 15),
        ("機械H25", "同期機", 12),
        ("機械H25", "変圧器", 10),
        ("機械H25", "保護機器", 7),
        ("機械H25", "パワエレ", 15),
        ("機械H25", "照明", 13),
        ("機械H25", "電熱", 5),
        ("機械H25", "電気化学", 8),
        ("機械H25", "電動力応用", 1),
        ("機械H25", "自動制御", 10),
        ("機械H25", "情報", 16),
        ("機械H25", "電気鉄道", 1),
        ("機械H25", "その他", 1),

        # --- 電力2022 ---
        ("電力2022", "水力発電", 13),
        ("電力2022", "汽力発電", 12),
        ("電力2022", "原子力発電", 2),
        ("電力2022", "発電一般・その他", 15),
        ("電力2022", "変電", 18),
        ("電力2022", "送電", 30),
        ("電力2022", "配電", 15),

        # --- 電力H25 ---
        ("電力H25", "水力発電", 11),
        ("電力H25", "汽力発電", 18),
        ("電力H25", "原子力発電", 5),
        ("電力H25", "発電一般・その他", 14),
        ("電力H25", "変電", 19),
        ("電力H25", "送電", 26),
        ("電力H25", "配電", 12),

        # --- 法規2024 ---
        ("法規2024", "電気事業法関連", 22),
        ("法規2024", "電気設備技術基準", 55),
        ("法規2024", "施設管理", 28),

        # --- 法規H27 ---
        ("法規2024H27", "電気事業法関連", 26),
        ("法規2024H27", "電気設備技術基準", 47),
        ("法規2024H27", "施設管理", 32)
    ]

# データベース（スプレッドシート）と接続
conn = st.connection("gsheets", type=GSheetsConnection)

# SecretsからURLを取得
try:
    target_url = st.secrets["connections"]["gsheets"]["spreadsheet"]
except Exception:
    st.error("Secretsに 'spreadsheet' URLを設定してください")
    st.stop()

def load_and_sync_data():
    try:
        df = conn.read(spreadsheet=target_url, worksheet="Sheet1", usecols=[0, 1, 2, 3])
        df = df.dropna(how="all")
        current_db = df.to_dict('records')
    except Exception:
        current_db = []

    existing_names = {f"{item['field']}_{item['q_num']}" for item in current_db if 'field' in item}
    new_added = False
    
    # リストに基づいて1番から連番で作成
    for subject, category, count in get_master_structure():
        for i in range(1, count + 1):
            q_id = f"{category}No{i}"
            if f"{subject}_{q_id}" not in existing_names:
                current_db.append({"field": subject, "q_num": q_id, "level": 0, "last_date": ""})
                new_added = True
                
    if new_added:
        save_data(current_db)
        
    return current_db

def save_data(data):
    updated_df = pd.DataFrame(data)
    conn.update(spreadsheet=target_url, worksheet="Sheet1", data=updated_df)

# --- 2. 状態管理 ---
if 'db' not in st.session_state:
    st.session_state.db = load_and_sync_data()
if 'test_pool' not in st.session_state:
    st.session_state.test_pool = []
if 'history' not in st.session_state:
    st.session_state.history = []

db = st.session_state.db

# --- 3. UI構築 ---
st.set_page_config(page_title="電験 学習マネージャー", layout="centered", page_icon="⚡")
st.title("⚡ 電験 学習マネージャー")

col1, col2 = st.columns(2)
fields = ["すべて"] + list(dict.fromkeys([item["field"] for item in db]))
selected_field = col1.selectbox("分野", fields)
selected_mode = col2.selectbox("モード", ["新規学習", "復習モード"])

if st.button("🚀 テスト開始", use_container_width=True):
    st.session_state.history = []
    today = datetime.today().date()
    pool = []
    
    for item in db:
        if selected_field != "すべて" and item["field"] != selected_field:
            continue
        
        last_date_val = str(item.get("last_date", ""))
        if selected_mode == "新規学習" and last_date_val in ["", "nan", "None"]:
            pool.append(item)
        elif selected_mode == "復習モード" and last_date_val not in ["", "nan", "None"]:
            try:
                last_date = datetime.strptime(last_date_val, '%Y-%m-%d').date()
                lv = int(float(item.get("level", 0)))
                if today >= last_date + timedelta(days=INTERVALS.get(lv, 0)):
                    pool.append(item)
            except:
                pass
                
    if selected_mode == "復習モード":
        random.shuffle(pool)
    st.session_state.test_pool = pool

# 進捗表示
total_q = len([q for q in db if selected_field == "すべて" or q["field"] == selected_field])
answered_q = len([q for q in db if (selected_field == "すべて" or q["field"] == selected_field) and str(q.get("last_date", "")) not in ["", "nan", "None"]])
if total_q > 0:
    st.progress(answered_q / total_q)
    st.caption(f"進捗: {answered_q} / {total_q}問完了 ({answered_q/total_q*100:.1f}%)")

st.divider()

if len(st.session_state.test_pool) > 0:
    current_q = st.session_state.test_pool[0]
    st.subheader(f"【{current_q['field']}】")
    st.header(f"{current_q['q_num']}")
    
    last_date_val = str(current_q.get('last_date', ''))
    status_text = "未学習" if last_date_val in ["", "nan", "None"] else f"前回: {int(float(current_q['level']))}点"
    st.info(f"残り: {len(st.session_state.test_pool)}問 | 状態: {status_text}")
    
    st.write("理解度を入力してください：")
    cols = st.columns(6)
    for i in range(6):
        if cols[i].button(f"{i}点", key=f"btn_{i}", use_container_width=True):
            st.session_state.history.append({
                "q_num": current_q["q_num"], 
                "field": current_q["field"],
                "old_level": current_q.get("level", 0), 
                "old_date": current_q.get("last_date", "")
            })
            
            for row in st.session_state.db:
                if row["q_num"] == current_q["q_num"] and row["field"] == current_q["field"]:
                    row["level"] = i
                    row["last_date"] = datetime.today().strftime('%Y-%m-%d')
                    break
                    
            save_data(st.session_state.db)
            st.session_state.test_pool.pop(0)
            st.rerun()
            
    st.divider()
    col_opt1, col_opt2 = st.columns(2)
    
    if col_opt1.button("↩️ 1つ戻る", disabled=len(st.session_state.history)==0, use_container_width=True):
        last_action = st.session_state.history.pop()
        for row in st.session_state.db:
            if row["q_num"] == last_action["q_num"] and row["field"] == last_action["field"]:
                row["level"] = last_action["old_level"]
                row["last_date"] = last_action["old_date"]
                st.session_state.test_pool.insert(0, row)
                break
        save_data(st.session_state.db)
        st.rerun()
        
    if col_opt2.button("⏭️ スキップ", use_container_width=True):
        item = st.session_state.test_pool.pop(0)
        st.session_state.test_pool.append(item)
        st.rerun()
        
elif 'test_pool' in st.session_state and len(st.session_state.test_pool) == 0 and st.button("もう一度開始する"):
     st.success("🎉 条件に合う問題はすべて完了しました！")
