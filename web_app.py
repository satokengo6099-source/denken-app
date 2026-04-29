import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
import random
from datetime import datetime, timedelta
import os  
import requests
import json

# --- 1. LINE通知用関数 ---
# 🌟 LINE通知用関数（エラー詳細表示版）
def send_line_notification(message):
    import streamlit as st # 画面にエラーを出すために追加
    try:
        url = "https://api.line.me/v2/bot/message/broadcast"
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {st.secrets['line_access_token']}"
        }
        payload = {
            "messages": [{"type": "text", "text": message}]
        }
        response = requests.post(url, headers=headers, data=json.dumps(payload))
        
        if response.status_code == 200:
            return True
        else:
            # 🌟 エラーが起きたら画面に赤文字でLINEからの返答をそのまま出す！
            st.error(f"🚨 LINE送信失敗！ コード: {response.status_code}\n理由: {response.text}")
            return False
            
    except Exception as e:
        st.error(f"🚨 根本的な通信エラー: {e}")
        return False

# --- 2. ユーザー別個別設定 ---
# メール通知廃止に伴い、email項目を削除しました
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
        "deadline": datetime(2026, 9, 1).date(),
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
        "deadline": datetime(2026, 10, 15).date(),
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
    }
}




# --- 3. データベース接続・型固定読み込み ---
conn = st.connection("gsheets", type=GSheetsConnection)
target_url = st.secrets["connections"]["gsheets"]["spreadsheet"]

def load_full_data():
    """スプレッドシートから全データを読み込み、型を整える"""
    try:
        # Sheet1（メインの学習記録）を読み込み
        df = conn.read(spreadsheet=target_url, worksheet="Sheet1", usecols=[0, 1, 2, 3, 4], ttl=0)
        df = df.dropna(how="all")
        
        # 型の強制固定（エラー防止）
        df['level'] = pd.to_numeric(df['level'], errors='coerce').fillna(0).astype(int)
        df['last_date'] = df['last_date'].astype(str).replace(['nan', 'None', 'NaN', '<NA>', ''], '')
        for col in ['user', 'field', 'q_num']:
            df[col] = df[col].astype(str).str.strip()
            
        return df
    except Exception as e:
        st.error(f"データ読み込みエラー: {e}")
        return pd.DataFrame(columns=["user", "field", "q_num", "level", "last_date"])

def sync_user_data(full_df, user_name):
    """USER_CONFIGに基づいて未登録の問題を生成し、スプレッドシートを更新する"""
    user_df = full_df[full_df['user'] == user_name].copy()
    # 既存の問題をセットで管理（重複チェック用）
    existing_q = set(user_df['field'] + "_" + user_df['q_num'])
    
    structure = USER_CONFIG[user_name]["structure"]
    new_rows = []
    
    for item in structure:
        field = str(item[0]) # 科目（例：理論2023）
        cat = str(item[1])   # 分野（例：静電気）
        
        # 形式の判定（要素が3つなら問題数、4つなら開始-終了番号）
        if len(item) == 3:
            start, end = 1, item[2]
        else:
            start, end = item[2], item[3]
            
        for i in range(start, end + 1):
            q_id = f"{cat}No{i}"
            if f"{field}_{q_id}" not in existing_q:
                new_rows.append({
                    "user": str(user_name),
                    "field": field,
                    "q_num": q_id,
                    "level": 0,
                    "last_date": ""
                })
                
    if new_rows:
        # 新しい問題を結合
        updated_user_df = pd.concat([user_df, pd.DataFrame(new_rows)], ignore_index=True)
        # 他のユーザーのデータと合わせて全体を更新
        other_users = full_df[full_df['user'] != user_name]
        new_full = pd.concat([other_users, updated_user_df], ignore_index=True)
        
        # 保存前に型を再固定
        new_full['level'] = new_full['level'].astype(int)
        new_full['last_date'] = new_full['last_date'].astype(str)
        
        conn.update(spreadsheet=target_url, worksheet="Sheet1", data=new_full)
        return updated_user_df
        
    return user_df


# --- 4. 通知・レポート管理機能 ---

def generate_report_message(full_df):
    """LINE送信用に精神攻撃レポートの本文を生成する"""
    yesterday_dt = (datetime.today() - timedelta(days=1)).date()
    yesterday_str = yesterday_dt.strftime('%Y-%m-%d')
    
    msg = f"📢 【電験監獄：朝の進捗報告】\n{yesterday_dt.strftime('%m/%d')} の処刑結果です。\n"
    msg += "="*15 + "\n"

    for user in USER_CONFIG.keys():
        u_data = full_df[full_df['user'] == user]
        
        # サボり日数の計算
        valid_dates = u_data[u_data['last_date'].astype(str).str.contains("-", na=False)]['last_date']
        if not valid_dates.empty:
            last_action_str = valid_dates.max()
            last_action_date = datetime.strptime(last_action_str, '%Y-%m-%d').date()
            slack_days = (yesterday_dt - last_action_date).days
        else:
            slack_days = 999 

        if slack_days < 0: slack_days = 0

        # 昨日のスコア
        y_data = u_data[u_data['last_date'] == yesterday_str]
        done = len(y_data)
        avg = pd.to_numeric(y_data['level'], errors='coerce').mean() if done > 0 else 0
        
        # 名前剥奪
        display_name = f"【💀】{user}(敗北者)" if done == 0 and slack_days >= 3 else user

        msg += f"👤 {display_name}\n📊 消化: {done}問 (平:{avg:.1f}点)\n"
        
        if done >= 20:
            msg += "💬: 合格確実。サボるゴミ達を置いて高みへ行きましょう。\n"
        elif done >= 1:
            msg += "💬: 記念受験。その程度で勉強したつもりですか？\n"
        else:
            if slack_days >= 3:
                days_text = f"{slack_days}日連続" if slack_days != 999 else "永遠に"
                msg += f"💬: 敗北者。{days_text}0問。恥を知りなさい。\n"
            else:
                msg += "💬: ゴミ。正気ですか？人生ごと不合格です。\n"
        msg += "-"*10 + "\n"
    
    msg += "※不満なら今すぐ机に向かえ。"
    return msg

def check_and_trigger_report():
    """1日の各タイミング（朝の報告・22時警告）で通知を飛ばす"""
    if st.session_state.get("report_checked", False):
        return

    today_str = datetime.today().strftime('%Y-%m-%d')
    now_hour = datetime.today().hour

    # --- A. 朝の進捗レポート送信 ---
    try:
        sys_df = conn.read(spreadsheet=target_url, worksheet="System", ttl=0)
        last_sent = str(sys_df.iloc[0, 0])
        if last_sent != today_str:
            # 更新処理
            conn.update(spreadsheet=target_url, worksheet="System", data=pd.DataFrame([[today_str]], columns=["last_report_date"]))
            full_df = load_full_data()
            report_msg = generate_report_message(full_df)
            if send_line_notification(report_msg):
                st.toast("LINEへ進捗レポートを送信しました📩")
    except: pass

    # --- B. 22時の未完了警告送信 ---
    if now_hour >= 22:
        try:
            # TaskLogsシートから今日の警告が送信済みか確認
            logs = conn.read(spreadsheet=target_url, worksheet="TaskLogs", ttl=0)
            warning_sent = logs[(logs['date'] == today_str) & (logs['type'] == '22h_warning')]
            
            if warning_sent.empty:
                full_df = load_full_data()
                unfinished = []
                for user in USER_CONFIG.keys():
                    done_today = len(full_df[(full_df['user'] == user) & (full_df['last_date'] == today_str)])
                    if done_today < 20:
                        unfinished.append(f"・{user} (現在{done_today}問)")
                
                if unfinished:
                    warn_msg = "🚨 【緊急警告：22時】\n以下の怠慢者がノルマ未達成です。\n\n" + "\n".join(unfinished) + "\n\n日付が変わる前に地獄の底から這い上がってきなさい。"
                    if send_line_notification(warn_msg):
                        new_log = pd.DataFrame([[today_str, "system", "22h_warning"]], columns=["date", "user", "type"])
                        # 既存ログと結合して更新
                        updated_logs = pd.concat([logs, new_log], ignore_index=True)
                        conn.update(spreadsheet=target_url, worksheet="TaskLogs", data=updated_logs)
        except Exception as e:
            print(f"22時警告エラー: {e}")

    st.session_state["report_checked"] = True

def check_unread_monologue(current_user):
    """独り言掲示板の未読があるかチェック"""
    try:
        mono_df = conn.read(spreadsheet=target_url, worksheet="Monologues", ttl=0)
        status_df = conn.read(spreadsheet=target_url, worksheet="ReadStatus", ttl=0)
        
        user_status = status_df[status_df['user'] == current_user]
        if user_status.empty or mono_df.empty:
            return False
            
        last_read = pd.to_datetime(user_status['last_read_at'].iloc[0])
        mono_df['date_dt'] = pd.to_datetime(mono_df['date'], errors='coerce')
        
        new_posts = mono_df[
            (mono_df['user'] != current_user) & 
            (mono_df['date_dt'] > last_read)
        ]
        return len(new_posts) > 0
    except:
        return False

# --- 4. UI構築・メインロジック ---
st.set_page_config(page_title="電験 学習マネージャー", layout="centered", page_icon="⚡")

# ⚠️ current_user をここで一番最初に定義する！
current_user = st.sidebar.selectbox("利用者を選択", list(USER_CONFIG.keys()), key="user_selector")
target_date = USER_CONFIG[current_user]["deadline"]

# データの読み込み
if 'last_user' not in st.session_state or st.session_state.last_user != current_user:
    with st.spinner(f"{current_user}さんのデータを読み込み中..."):
        full_data = load_full_data()
        st.session_state.db = sync_user_data(full_data, current_user)
        st.session_state.last_user = current_user
        st.session_state.test_pool = []
        st.session_state.history = []

if "db" in st.session_state:
    db = st.session_state.db
else:
    st.stop()

# レポートと警告のチェック
check_and_trigger_report()

# ==========================================
# 👇 ここから「5. メニュー切り替え」に続く
# ==========================================

# --- 5. メニュー切り替えとサイドバー（通知・進捗） ---

# 独り言の未読チェック
has_unread = check_unread_monologue(current_user)
mono_label = "ただの独り言 🔴" if has_unread else "ただの独り言"

st.sidebar.divider()
mode_select = st.sidebar.radio("機能", ["学習モード", "復習モード", "分析ダッシュボード", mono_label])

# (以下、今のコードが続く...)

st.sidebar.divider()
mode_select = st.sidebar.radio("機能", ["学習モード", "復習モード", "分析ダッシュボード", mono_label])

# 📅 試験日カウントダウンと進捗計算
# 🌟 本試験の日付（2026年8月30日に設定しています）
EXAM_DATE = datetime(2026, 8, 30).date() 
today_dt = datetime.today().date()

# 今日の進捗（LINE通知判定用にも使う）
today_str = today_dt.strftime('%Y-%m-%d')
done_today_count = len(db[db['last_date'] == today_str])

# 全体進捗の計算
unstarted_list = [q for q in db.to_dict('records') if str(q.get("last_date", "")) in ["", "nan", "None", "NaN"]]
total_count = len(db)
answered_count = total_count - len(unstarted_list)

st.sidebar.divider()

# 1. 本試験までのカウントダウン
st.sidebar.metric("🔥 試験日まであと", f"{max(0, (EXAM_DATE - today_dt).days)}日")

# 2. 各自の目標期日と進捗バー
st.sidebar.metric("個人の目標期日まで", f"{max(0, (target_date - today_dt).days)}日")
st.sidebar.progress(answered_count / total_count if total_count > 0 else 0)
st.sidebar.caption(f"全体進捗: {answered_count}/{total_count} ({answered_count/total_count*100:.1f}%)")
st.sidebar.write(f"📊 本日のノルマ: **{done_today_count} / 20**")

# --- ✍️ モチベーションメッセージ（明朝体・イタリックデザイン） ---
st.sidebar.markdown("<br><br><br>", unsafe_allow_html=True)
st.sidebar.markdown("""
    <div style="text-align: center; color: #555; padding: 10px; border-top: 1px solid #ddd;">
        <p style="font-family: 'Georgia', serif; font-style: italic; font-size: 1.1em; margin-bottom: 2px;">
            Where there is a "will", there is a way.
        </p>
        <p style="font-family: 'Yu Mincho', 'MS Mincho', serif; font-size: 0.9em; letter-spacing: 1px;">
            意思あるところに道は開ける
        </p>
    </div>
""", unsafe_allow_html=True)


# --- 6. メインコンテンツの分岐 ---
if mode_select == "学習モード":
    st.title(f"⚡ 学習：{current_user}")
    fields = ["すべて"] + list(db['field'].unique())
    selected_field = st.selectbox("分野を選択", fields, key="field_selector")
    pool = [q for q in unstarted_list if selected_field == "すべて" or q["field"] == selected_field]
    
    if st.button("🚀 学習開始", use_container_width=True):
        st.session_state.test_pool = pool
        st.session_state.history = []
        st.rerun()

elif mode_select == "復習モード":
    st.title(f"🔄 復習：{current_user}")
    review_pool = [q for q in db.to_dict('records') if str(q.get("last_date", "")) not in ["", "nan", "None", "NaN"] and int(q.get("level", 0)) < 5]
    review_pool.sort(key=lambda x: int(x.get("level", 0)))
    
    if st.button("🔥 復習開始", use_container_width=True):
        st.session_state.test_pool = review_pool
        st.session_state.history = []
        st.rerun()

elif mode_select == "分析ダッシュボード":
    # --- 📊 強化版：分析・自戒ダッシュボード ---
    st.title(f"📊 分析・自戒：{current_user}")
    
    full_df_ana = load_full_data()
    yesterday_str = (datetime.today() - timedelta(days=1)).strftime('%Y-%m-%d')
    user_yesterday = full_df_ana[(full_df_ana['user'] == current_user) & (full_df_ana['last_date'] == yesterday_str)]
    done_yesterday = len(user_yesterday)

    # 🧘 自戒の部屋
    st.subheader("🧘 自戒の部屋")
    if done_yesterday == 0:
        st.error(f"🚨 警告：昨日の進捗は 0 問です。")
        if f"unlocked_{current_user}" not in st.session_state:
            st.session_state[f"unlocked_{current_user}"] = False

        if not st.session_state[f"unlocked_{current_user}"]:
            reflection = st.text_area("反省文（30文字以上）を入力しない限り、ロックは解除されません", key="ref_input")
            if st.button("反省文を提出"):
                if len(reflection) >= 30:
                    try:
                        new_ref = pd.DataFrame([[datetime.today().strftime('%Y-%m-%d'), current_user, reflection]], columns=["date", "user", "content"])
                        conn.update(spreadsheet=target_url, worksheet="Reflections", data=new_ref)
                    except: pass
                    st.session_state[f"unlocked_{current_user}"] = True
                    st.rerun()
                else:
                    st.warning("反省が足りません。")
    else:
        st.session_state[f"unlocked_{current_user}"] = True
        st.success(f"✅ 昨日は {done_yesterday} 問の努力が確認されました。")

    st.divider()

    # 🏁 進捗比較
    st.subheader("🏁 メンバー進捗比較")
    comparison = []
    
    for user in USER_CONFIG.keys():
        u_df = full_df_ana[full_df_ana['user'] == user].copy()
        total = len(u_df)
        
        if total > 0:
            valid_done = u_df[u_df['last_date'].astype(str).str.contains("-", na=False)]
            done = len(valid_done)
            rate = round((done / total) * 100, 1)
        else:
            rate = 0.0
            
        comparison.append({"ユーザー": user, "進捗率": f"{rate}%"})
    
    st.table(pd.DataFrame(comparison))

    # 🚩 各ユーザーの苦手単元ワースト
    st.subheader("🚩 メンバー別 苦手単元ワースト7 ")
    
    cols = st.columns(len(USER_CONFIG.keys()))
    
    for idx, user in enumerate(USER_CONFIG.keys()):
        with cols[idx]:
            st.markdown(f"**👤 {user}の弱点**")
            u_df = full_df_ana[full_df_ana['user'] == user].copy()
            
            if u_df.empty:
                st.info("データ未生成")
                continue

            u_df['単元'] = u_df['q_num'].str.split('No').str[0]
            u_df['level_num'] = pd.to_numeric(u_df['level'], errors='coerce').fillna(0)
            u_df['is_done'] = u_df['last_date'].astype(str).str.contains("-", na=False)
            
            u_res = u_df.groupby(['field', '単元']).agg(
                total=('q_num', 'count'),
                correct=('level_num', lambda x: (x >= 3).sum()),
                done_q=('is_done', 'sum')
            ).reset_index()
            
            u_res['正答率'] = (u_res['correct'] / u_res['total'] * 100).round(1)
            worst = u_res[u_res['done_q'] > 0].sort_values('正答率').head(7)
            
            if not worst.empty:
                for r in worst.itertuples():
                    st.error(f"{r.field}：{r.単元}\n({r.正答率}%)")
            else:
                st.success("弱点データなし\n（または未着手）")

elif mode_select == mono_label:
    st.title(f"📝 {mono_label.replace(' 🔴', '')}")
    
    # 既読更新
    try:
        status_df = conn.read(spreadsheet=target_url, worksheet="ReadStatus")
        status_df.loc[status_df['user'] == current_user, 'last_read_at'] = datetime.today().strftime('%Y-%m-%d %H:%M:%S')
        conn.update(spreadsheet=target_url, worksheet="ReadStatus", data=status_df)
    except Exception as e:
        st.error(f"既読状態の更新に失敗しました。ReadStatusシートを確認してください。")

    # 投稿フォーム（🌟 ダブっていたものを1つに統一し、LINE通知付きのものを残しました）
    with st.expander("💬 独り言（メモ・わからない問題）を投稿する"):
        note_content = st.text_area("内容（Markdown対応）")
        uploaded_file = st.file_uploader("資料をアップロード", type=['pdf', 'png', 'jpg', 'jpeg'])
        
        if st.button("投稿する"):
            if note_content:
                f_name = ""
                if uploaded_file:
                    f_name = uploaded_file.name
                    os.makedirs("uploads", exist_ok=True)
                    file_path = os.path.join("uploads", f_name)
                    with open(file_path, "wb") as f:
                        f.write(uploaded_file.getbuffer())
                
                new_mono = pd.DataFrame([[datetime.today().strftime('%Y-%m-%d %H:%M:%S'), current_user, note_content, f_name]], 
                                       columns=["date", "user", "content", "file_name"])
                try:
                    old_mono = conn.read(spreadsheet=target_url, worksheet="Monologues", ttl=0)
                    updated_mono = pd.concat([old_mono, new_mono], ignore_index=True)
                    conn.update(spreadsheet=target_url, worksheet="Monologues", data=updated_mono)
                    
                    # LINE通知
                    line_msg = f"💬 【新着：独り言】\n{current_user}さんが新しいメッセージを投稿しました。\n\n内容：\n{note_content[:50]}{'...' if len(note_content) > 50 else ''}"
                    send_line_notification(line_msg)
                    
                    st.success("投稿しました。メンバーに通知を送信しました。")
                    st.rerun()
                except Exception as e:
                    st.error(f"送信に失敗しました: {e}")

    # タイムライン表示
    st.divider()
    try:
        display_mono = conn.read(spreadsheet=target_url, worksheet="Monologues", ttl=0)
        if not display_mono.empty:
            display_mono.columns = display_mono.columns.str.strip()
            display_mono['date_sort'] = pd.to_datetime(display_mono['date'], errors='coerce')
            display_mono = display_mono.sort_values("date_sort", ascending=False)

            for m in display_mono.itertuples():
                is_me = (str(m.user).strip() == current_user)
                with st.chat_message("user" if is_me else "assistant"):
                    d_show = m.date if pd.isna(m.date_sort) else m.date_sort.strftime('%m/%d %H:%M')
                    st.write(f"**{m.user}** ({d_show})")
                    st.markdown(m.content)
                    
                    if hasattr(m, 'file_name') and str(m.file_name) != "nan" and m.file_name:
                        file_path = os.path.join("uploads", m.file_name)
                        if os.path.exists(file_path):
                            if m.file_name.lower().endswith(('.png', '.jpg', '.jpeg')):
                                st.image(file_path, caption=m.file_name, use_container_width=True)
                            else:
                                with open(file_path, "rb") as f:
                                    st.download_button(label=f"📥 {m.file_name} をダウンロード", data=f, file_name=m.file_name, mime="application/pdf")
                        else:
                            st.caption(f"📎 添付資料: {m.file_name} (※ファイル本体が見つかりません)")
        else:
            st.info("まだ投稿がありません。最初の独り言をどうぞ。")
    except Exception as e:
        st.error(f"表示エラー: {e}")

# --- 7. 共通の問題表示・解答エリア ---
is_unlocked = st.session_state.get(f"unlocked_{current_user}", False)

if mode_select in ["学習モード", "復習モード"]:
    if not is_unlocked:
        st.warning("🚨 現在ロックされています。「分析・自戒」メニューから反省文を提出してください。")
    elif st.session_state.test_pool:
        st.divider()
        # 🚀 ナビゲーション
        q_labels = [f"{i+1}: {q['field']} - {q['q_num']}" for i, q in enumerate(st.session_state.test_pool)]
        selected_idx = st.selectbox("問題ジャンプ／一括スキップ", range(len(q_labels)), format_func=lambda x: q_labels[x], key="jump_selector")
        if selected_idx > 0 and st.button("この問題まで一気に飛ばす"):
            st.session_state.test_pool = st.session_state.test_pool[selected_idx:]
            st.rerun()

        # 📖 問題表示
        curr = st.session_state.test_pool[0]
        st.subheader(f"【{curr['field']}】 {curr['q_num']}")
        
        # 解答ボタン
        cols = st.columns(6)
        for i in range(6):
            if cols[i].button(f"{i}点", key=f"b{i}"):
                # 履歴保存とデータ更新
                st.session_state.history.append({"q_num": curr["q_num"], "field": curr["field"], "old_level": curr.get("level", 0), "old_date": curr.get("last_date", "")})
                idx = st.session_state.db[(st.session_state.db['q_num'] == curr['q_num']) & (st.session_state.db['field'] == curr['field'])].index
                
                today_str = datetime.today().strftime('%Y-%m-%d')
                st.session_state.db.loc[idx, ['level', 'last_date']] = [i, today_str]
                
                # 🌟 追加：ノルマ達成チェックとLINE通知
                done_today = len(st.session_state.db[st.session_state.db['last_date'] == today_str])
                if done_today == 20:
                    try:
                        logs = conn.read(spreadsheet=target_url, worksheet="TaskLogs", ttl=0)
                        already_sent = logs[(logs['date'] == today_str) & 
                                            (logs['user'] == current_user) & 
                                            (logs['type'] == 'completed')]
                        if already_sent.empty:
                            msg = f"✅ 【速報】\n{current_user}が本日のノルマ(20問)を達成しました！\n\n彼は自由の身です。まだ終わっていない他のメンバーは、猛烈に自分を恥じなさい。"
                            if send_line_notification(msg):
                                new_log = pd.DataFrame([[today_str, current_user, "completed"]], columns=["date", "user", "type"])
                                conn.update(spreadsheet=target_url, worksheet="TaskLogs", data=pd.concat([logs, new_log], ignore_index=True))
                                st.toast("🎉 ノルマ達成をLINEで通知しました！")
                    except Exception as e:
                        print(f"達成通知エラー: {e}")

                # 全体保存して次へ
                full = load_full_data()
                conn.update(spreadsheet=target_url, worksheet="Sheet1", data=pd.concat([full[full['user'] != current_user], st.session_state.db], ignore_index=True))
                st.session_state.test_pool.pop(0)
                st.rerun()
        
        # 戻る・スキップ
        c1, c2 = st.columns(2)
        if c1.button("↩️ 1つ戻る", disabled=not st.session_state.history, use_container_width=True):
            last = st.session_state.history.pop()
            idx = st.session_state.db[(st.session_state.db['q_num'] == last['q_num']) & (st.session_state.db['field'] == last['field'])].index
            st.session_state.db.loc[idx, ['level', 'last_date']] = [last['old_level'], last['old_date']]
            st.session_state.test_pool.insert(0, st.session_state.db.loc[idx].to_dict('records')[0])
            full = load_full_data()
            conn.update(spreadsheet=target_url, worksheet="Sheet1", data=pd.concat([full[full['user'] != current_user], st.session_state.db], ignore_index=True))
            st.rerun()
        if c2.button("⏭️ 後回しにする", use_container_width=True):
            st.session_state.test_pool.append(st.session_state.test_pool.pop(0))
            st.rerun()
