import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
import random
from datetime import datetime, timedelta

# --- 1. データ管理（Google Sheets） ---
INTERVALS = {0: 0, 1: 1, 2: 3, 3: 7, 4: 14, 5: 30}

def get_master_structure():
    return [
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

# データベース（スプレッドシート）と接続
conn = st.connection("gsheets", type=GSheetsConnection)

def load_and_sync_data():
    # スプレッドシートからデータを読み込む
    try:
        df = conn.read(worksheet="Sheet1", usecols=[0, 1, 2, 3])
        df = df.dropna(how="all") # 空行を削除
        current_db = df.to_dict('records')
    except Exception:
        current_db = []

    existing_names = {f"{item['field']}_{item['q_num']}" for item in current_db if 'field' in item}
    new_added = False
    
    # マスターデータとの差分チェック
    for subject, category, start_num, end_num in get_master_structure():
        for i in range(start_num, end_num + 1):
            q_id = f"{category}No{i}"
            if f"{subject}_{q_id}" not in existing_names:
                current_db.append({"field": subject, "q_num": q_id, "level": 0, "last_date": ""})
                new_added = True
                
    if new_added:
        # 新しい問題が追加されたらスプレッドシートを更新
        updated_df = pd.DataFrame(current_db)
        conn.update(worksheet="Sheet1", data=updated_df)
        
    return current_db

def save_data(data):
    # スプレッドシートを上書き保存
    updated_df = pd.DataFrame(data)
    conn.update(worksheet="Sheet1", data=updated_df)

# --- 2. 状態管理（セッション） ---
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
        if selected_mode == "新規学習" and str(item.get("last_date", "")) in ["", "nan", "None"]:
            pool.append(item)
        elif selected_mode == "復習モード" and str(item.get("last_date", "")) not in ["", "nan", "None"]:
            try:
                last_date = datetime.strptime(str(item["last_date"]), '%Y-%m-%d').date()
                if today >= last_date + timedelta(days=INTERVALS[int(item["level"])]):
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
    
    status_text = "未学習" if str(current_q.get('last_date', '')) in ["", "nan", "None"] else f"前回: {int(current_q['level'])}点"
    st.info(f"残り: {len(st.session_state.test_pool)}問 | 状態: {status_text}")
    
    st.write("理解度を入力してください：")
    cols = st.columns(6)
    for i in range(6):
        if cols[i].button(f"{i}点", key=f"btn_{i}", use_container_width=True):
            st.session_state.history.append({
                "q_num": current_q["q_num"], "old_level": current_q.get("level", 0), "old_date": current_q.get("last_date", "")
            })
            
            # DBの該当データを更新
            for row in st.session_state.db:
                if row["q_num"] == current_q["q_num"]:
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
        
        # DBを履歴の状態に戻す
        for row in st.session_state.db:
            if row["q_num"] == last_action["q_num"]:
                row["level"] = last_action["old_level"]
                row["last_date"] = last_action["old_date"]
                st.session_state.test_pool.insert(0, row) # プールに戻す
                break
                
        save_data(st.session_state.db)
        st.rerun()
        
    if col_opt2.button("⏭️ スキップ", use_container_width=True):
        item = st.session_state.test_pool.pop(0)
        st.session_state.test_pool.append(item)
        st.rerun()
        
elif 'test_pool' in st.session_state and len(st.session_state.test_pool) == 0 and st.button("もう一度開始する"):
     st.success("🎉 完了しました！条件を変えて再度開始してください。")