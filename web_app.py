import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
import random
from datetime import datetime, timedelta

# --- 1. 定数・マスター構成 ---
# ⭐目標達成期日を設定
TARGET_DATE = datetime(2026, 8, 22).date() 

def get_master_structure():
    """全科目のマスター構成（分野, カテゴリ, 問題数）"""
    return [
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

# 接続設定
conn = st.connection("gsheets", type=GSheetsConnection)
try:
    target_url = st.secrets["connections"]["gsheets"]["spreadsheet"]
except:
    st.error("Secretsに 'spreadsheet' URLを設定してください"); st.stop()

def load_and_sync_data():
    try:
        df = conn.read(spreadsheet=target_url, worksheet="Sheet1", usecols=[0, 1, 2, 3])
        df = df.dropna(how="all")
        current_db = df.to_dict('records')
    except: current_db = []
    
    existing_names = {f"{item['field']}_{item['q_num']}" for item in current_db if 'field' in item}
    new_added = False
    for subject, category, count in get_master_structure():
        for i in range(1, count + 1):
            q_id = f"{category}No{i}"
            if f"{subject}_{q_id}" not in existing_names:
                current_db.append({"field": subject, "q_num": q_id, "level": 0, "last_date": ""})
                new_added = True
    if new_added: save_data(current_db)
    return current_db

def save_data(data):
    conn.update(spreadsheet=target_url, worksheet="Sheet1", data=pd.DataFrame(data))

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

# サイドバーメニュー
st.sidebar.title("🛠️ メニュー")
mode_select = st.sidebar.radio("機能切り替え", ["学習モード", "復習モード", "分析ダッシュボード"])

# --- 共用処理：進捗とノルマ ---
today_dt = datetime.today().date()
days_left = (TARGET_DATE - today_dt).days
unstarted_all = [q for q in db if str(q.get("last_date", "")) in ["", "nan", "None"]]
total_q_all = len(db)
answered_q_all = total_q_all - len(unstarted_all)

# サイドバーに基本統計を表示
st.sidebar.divider()
st.sidebar.metric("試験まで", f"{max(0, days_left)}日")
st.sidebar.progress(answered_q_all / total_q_all if total_q_all > 0 else 0)
st.sidebar.caption(f"全体進捗: {answered_q_all}/{total_q_all} ({answered_q_all/total_q_all*100:.1f}%)")

if mode_select == "学習モード":
    st.title("⚡ 学習モード (新規)")
    fields = ["すべて"] + list(dict.fromkeys([item["field"] for item in db]))
    selected_field = st.selectbox("分野を選択", fields)
    
    # 対象問題を抽出
    pool = [q for q in db if (selected_field == "すべて" or q["field"] == selected_field) and str(q.get("last_date", "")) in ["", "nan", "None"]]
    
    if days_left > 0:
        daily_quota = -(-len(pool) // days_left) if len(pool) > 0 else 0
        st.info(f"💡 今日のノルマ: **{daily_quota}問** (この分野の残り未着手: {len(pool)}問)")
    
    if st.button("🚀 学習開始", use_container_width=True):
        st.session_state.test_pool = pool
        st.session_state.history = []
        st.rerun()

elif mode_select == "復習モード":
    st.title("🔄 復習モード (弱点克服)")
    st.write("満点（5点）を取れていない問題を、点数の低い順に表示します。")
    
    fields = ["すべて"] + list(dict.fromkeys([item["field"] for item in db]))
    selected_field = st.selectbox("分野を選択", fields)
    
    # 対象問題を抽出（1回以上解いていて、かつ5点未満の問題）
    review_pool = [q for q in db if (selected_field == "すべて" or q["field"] == selected_field) and str(q.get("last_date", "")) not in ["", "nan", "None"] and int(float(q.get("level", 0))) < 5]
    
    # 点数の低い順にソート
    review_pool.sort(key=lambda x: int(float(x.get("level", 0))))
    
    st.metric("復習が必要な問題", f"{len(review_pool)}問")
    
    if st.button("🔥 復習開始", use_container_width=True):
        st.session_state.test_pool = review_pool
        st.session_state.history = []
        st.rerun()

else:
    # --- 分析ダッシュボード ---
    st.title("📊 学習分析ダッシュボード")
    df_raw = pd.DataFrame(db)
    df_raw['level'] = pd.to_numeric(df_raw['level'], errors='coerce').fillna(0)
    df_raw['単元'] = df_raw['q_num'].str.split('No').str[0]
    
    # 正答率（3点以上を正解とする）
    stats = df_raw.groupby(['field', '単元']).agg(
        total=('q_num', 'count'),
        correct=('level', lambda x: (x >= 3).sum()),
        answered=('last_date', lambda x: (x.astype(str) != "nan").sum())
    ).reset_index()
    stats['正答率'] = (stats['correct'] / stats['total'] * 100).round(1)

    st.subheader("📈 分野別 正答率 (%)")
    field_stats = stats.groupby('field')['正答率'].mean().sort_values(ascending=False)
    st.bar_chart(field_stats)

    st.subheader("🚩 苦手単元ランキング (正答率ワースト10)")
    # 少なくとも1問以上解いた単元のみを対象にランキング
    worst_10 = stats[stats['answered'] > 0].sort_values(by=['正答率', 'total'], ascending=[True, False]).head(10)
    
    if not worst_10.empty:
        for i, row in enumerate(worst_10.itertuples(), 1):
            st.error(f"{i}位: **{row.field} / {row.単元}** (正答率: {row.正答率}%)")
    else:
        st.info("データが不足しています。まずは学習を進めましょう！")

# --- 4. 共通の問題表示エリア ---
if mode_select in ["学習モード", "復習モード"] and len(st.session_state.test_pool) > 0:
    st.divider()
    current_q = st.session_state.test_pool[0]
    st.subheader(f"【{current_q['field']}】")
    st.header(f"{current_q['q_num']}")
    
    last_date_val = str(current_q.get('last_date', ''))
    status_text = "未学習" if last_date_val in ["", "nan", "None"] else f"前回スコア: {int(float(current_q['level']))}点"
    st.info(f"残り: {len(st.session_state.test_pool)}問 | {status_text}")
    
    cols = st.columns(6)
    for i in range(6):
        if cols[i].button(f"{i}点", key=f"btn_{i}", use_container_width=True):
            st.session_state.history.append({"q_num": current_q["q_num"], "field": current_q["field"], "old_level": current_q.get("level", 0), "old_date": current_q.get("last_date", "")})
            for row in st.session_state.db:
                if row["q_num"] == current_q["q_num"] and row["field"] == current_q["field"]:
                    row["level"], row["last_date"] = i, datetime.today().strftime('%Y-%m-%d')
                    break
            save_data(st.session_state.db); st.session_state.test_pool.pop(0); st.rerun()
    
    c_opt1, c_opt2 = st.columns(2)
    if c_opt1.button("↩️ 戻る", disabled=not st.session_state.history):
        h = st.session_state.history.pop()
        for r in st.session_state.db:
            if r["q_num"] == h["q_num"] and r["field"] == h["field"]:
                r["level"], r["last_date"] = h["old_level"], h["old_date"]; st.session_state.test_pool.insert(0, r); break
        save_data(st.session_state.db); st.rerun()
    if c_opt2.button("⏭️ スキップ"):
        st.session_state.test_pool.append(st.session_state.test_pool.pop(0)); st.rerun()
