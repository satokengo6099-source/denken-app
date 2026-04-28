import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
import random
from datetime import datetime, timedelta
import smtplib
from email.mime.text import MIMEText

# --- 1. ユーザー別個別設定（期日・問題リスト・形式） ---
USER_CONFIG = {
"佐藤": {
        "email": "satokengo6099@gmail.com", # 自分のアドレス
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
        "email": "inagaki@example.com", # 稲垣さんのアドレスに変える
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
        "email": "kazeana@example.com", # 風穴さんのアドレスに変える
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

# --- 2. データベース接続・型固定読み込み ---
conn = st.connection("gsheets", type=GSheetsConnection)
target_url = st.secrets["connections"]["gsheets"]["spreadsheet"]

def load_full_data():
    """スプレッドシートから全データを読み込み、型を強制固定する"""
    try:
        df = conn.read(spreadsheet=target_url, worksheet="Sheet1", usecols=[0, 1, 2, 3, 4])
        df = df.dropna(how="all")
        # 型の不一致エラーを根こそぎ解消
        df['level'] = pd.to_numeric(df['level'], errors='coerce').fillna(0).astype(int)
        df['last_date'] = df['last_date'].astype(str).replace(['nan', 'None', 'NaN', '<NA>'], '')
        for col in ['user', 'field', 'q_num']:
            df[col] = df[col].astype(str)
        return df
    except:
        return pd.DataFrame(columns=["user", "field", "q_num", "level", "last_date"])

def sync_user_data(full_df, user_name):
    """ユーザーごとのマスター構成を反映"""
    user_df = full_df[full_df['user'] == user_name].copy()
    existing_q = set(user_df['field'] + "_" + user_df['q_num'])
    structure = USER_CONFIG[user_name]["structure"]
    new_rows = []
    for item in structure:
        field, cat = str(item[0]), str(item[1])
        start, end = (1, item[2]) if len(item) == 3 else (item[2], item[3])
        for i in range(start, end + 1):
            q_id = f"{cat}No{i}"
            if f"{field}_{q_id}" not in existing_q:
                new_rows.append({"user": str(user_name), "field": field, "q_num": q_id, "level": 0, "last_date": ""})
    if new_rows:
        updated_user_df = pd.concat([user_df, pd.DataFrame(new_rows)], ignore_index=True)
        other_users = full_df[full_df['user'] != user_name]
        new_full = pd.concat([other_users, updated_user_df], ignore_index=True)
        new_full['level'] = new_full['level'].astype(int)
        conn.update(spreadsheet=target_url, worksheet="Sheet1", data=new_full)
        return updated_user_df
    return user_df








# --- 3. 精神攻撃メール送信機能 ---
def send_daily_report(full_df):
    try:
        sender = "satokengo6099@gmail.com"
        password = "wvht mzfv hiqh aefc"
        receiver = "satokengo6099@gmail.com"
        yesterday_str = (datetime.today() - timedelta(days=1)).strftime('%Y-%m-%d')
        display_date = (datetime.today() - timedelta(days=1)).strftime('%Y/%m/%d')
        
        body = f"⚠️ 【重要：学習怠慢者への警告】 {display_date} 進捗レポート\n" + "="*50 + "\n"
        body += "※このメールは、昨日のあなたの『やる気』を客観的に評価したものです。\n" + "="*50 + "\n\n"

        for user in USER_CONFIG.keys():
            u_data = full_df[full_df['user'] == user]
            y_data = u_data[u_data['last_date'] == yesterday_str]
            done = len(y_data)
            avg = pd.to_numeric(y_data['level'], errors='coerce').mean() if done > 0 else 0
            
            body += f"👤 利用者: {user}\n📊 消化数: {done}問 / 平均スコア: {avg:.1f}点\n"
            if done >= 20:
                body += "💬 評価: 【合格確実】素晴らしい努力です。他の二人が口先だけでサボっている間に、あなたは着実に合格に近づいています。このまま彼らを見捨てて自分だけ高みへ登りましょう。\n"
            elif done >= 10:
                body += "💬 評価: 【不合格予備軍】可もなく不可もない、一番『落ちる』タイプです。その程度で満足ですか？明日もそのぬるま湯に浸かって、試験当日に絶望してください。\n"
            elif done > 0:
                body += "💬 評価: 【記念受験】たった数問で勉強したつもりですか？試験会場で恥をかくだけです。これ以上醜態を晒す前に、いっそ今すぐ辞めたらどうですか？\n"
            else:
                body += "💬 評価: 【ゴミ】1問も解いていない？正気ですか？『合格したい』という言葉が聞いて呆れます。あなたの人生は無意味なゴミそのものです。恥を知りなさい。\n"
            body += "-"*30 + "\n\n"
        
        body += "\n※不満があるなら、言い訳する前に今すぐ机に向かいなさい。\n"
        msg = MIMEText(body)
        msg["Subject"] = f"🚨【電験】昨日のお前らの無様な結果だ"
        msg["From"], msg["To"] = sender, receiver
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as s:
            s.login(sender, password)
            s.send_message(msg)
        return True
    except Exception as e:
        st.error(f"メール送信失敗: {e}"); return False

# （send_daily_report 関数の終わり）
        return True
    except Exception as e:
        st.error(f"メール送信失敗: {e}"); return False

# ⭐ ここに「定義」を置く
def check_and_trigger_report():
    try:
        sys_df = conn.read(spreadsheet=target_url, worksheet="System")
        last_sent = str(sys_df.iloc[0, 0])
    except: 
        last_sent = "2000-01-01"
    
    today_str = datetime.today().strftime('%Y-%m-%d')
    if last_sent != today_str:
        full_df = load_full_data()
        if send_daily_report(full_df):
            conn.update(spreadsheet=target_url, worksheet="System", data=pd.DataFrame([[today_str]], columns=["last_report_date"]))
            st.toast("昨日のレポートを送信しました📩")


# --- 4. UI構築・メインロジック ---
st.set_page_config(page_title="電験 学習マネージャー", layout="centered", page_icon="⚡")
check_and_trigger_report()


# --- ユーザー選択とデータ読み込み管理 ---
current_user = st.sidebar.selectbox("利用者を選択", list(USER_CONFIG.keys()))
target_date = USER_CONFIG[current_user]["deadline"] # 💡これを忘れずに追加

if 'last_user' not in st.session_state or st.session_state.last_user != current_user:
    with st.spinner(f"{current_user}さんのデータを読み込み中..."):
        full_data = load_full_data()
        st.session_state.db = sync_user_data(full_data, current_user)
        st.session_state.last_user = current_user
        st.session_state.test_pool = []
        st.session_state.history = []

# ⭐【ここが重要！】
# セッションから db を取り出して、プログラム全体で使えるようにします
if "db" in st.session_state:
    db = st.session_state.db
else:
    # 初回アクセス時など、まだデータがない場合はリロードを促す
    st.stop() 

# --- メニュー切り替え ---
st.sidebar.divider()
mode_select = st.sidebar.radio("機能", ["学習モード", "復習モード", "分析ダッシュボード"])

# --- 3. 精神攻撃メール送信機能 ---
def send_daily_report(full_df):
    try:
        sender = "satokengo6099@gmail.com"
        password = "wvht mzfv hiqh aefc"
        
        # 🌟 変更: 宛先を USER_CONFIG から抽出して全員に送る設定
        all_emails = [info.get("email") for info in USER_CONFIG.values() if info.get("email")]
        receiver_str = ", ".join(all_emails) 
        
        yesterday_str = (datetime.today() - timedelta(days=1)).strftime('%Y-%m-%d')
        display_date = (datetime.today() - timedelta(days=1)).strftime('%Y/%m/%d')
        
        body = f"⚠️ 【重要：学習怠慢者への警告】 {display_date} 進捗レポート\n" + "="*50 + "\n"
        body += "※このメールは、昨日のあなたの『やる気』を客観的に評価したものです。\n" + "="*50 + "\n\n"

        for user in USER_CONFIG.keys():
            u_data = full_df[full_df['user'] == user]
            y_data = u_data[u_data['last_date'] == yesterday_str]
            done = len(y_data)
            avg = pd.to_numeric(y_data['level'], errors='coerce').mean() if done > 0 else 0
            
            body += f"👤 利用者: {user}\n📊 消化数: {done}問 / 平均スコア: {avg:.1f}点\n"
            if done >= 20:
                body += "💬 評価: 【合格確実】素晴らしい努力です。他の二人が口先だけでサボっている間に、あなたは着実に合格に近づいています。このまま彼らを見捨てて自分だけ高みへ登りましょう。\n"
            elif done >= 10:
                body += "💬 評価: 【不合格予備軍】可もなく不可もない、一番『落ちる』タイプです。その程度で満足ですか？明日もそのぬるま湯に浸かって、試験当日に絶望してください。\n"
            elif done > 0:
                body += "💬 評価: 【記念受験】たった数問で勉強したつもりですか？試験会場で恥をかくだけです。これ以上醜態を晒す前に、いっそ今すぐ辞めたらどうですか？\n"
            else:
                body += "💬 評価: 【ゴミ】1問も解いていない？正気ですか？『合格したい』という言葉が聞いて呆れます。あなたの人生は無意味なゴミそのものです。恥を知りなさい。\n"
            body += "-"*30 + "\n\n"
        
        body += "\n※不満があるなら、言い訳する前に今すぐ机に向かいなさい。\n"
        msg = MIMEText(body)
        msg["Subject"] = f"🚨【電験】昨日のお前らの無様な結果だ"
        msg["From"], msg["To"] = sender, receiver_str # 🌟 修正: 宛先をリスト化
        
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as s:
            s.login(sender, password)
            s.send_message(msg)
        return True
    except Exception as e:
        st.error(f"メール送信失敗: {e}")
        return False

# 🌟 変更: 二重送信防止を強化
def check_and_trigger_report():
    try:
        sys_df = conn.read(spreadsheet=target_url, worksheet="System")
        last_sent = str(sys_df.iloc[0, 0])
    except: 
        last_sent = "2000-01-01"
    
    today_str = datetime.today().strftime('%Y-%m-%d')
    if last_sent != today_str:
        # 送る前に「今日送った」ことにしちゃう（他人が同時にアクセスしたときの二重送信防止）
        conn.update(spreadsheet=target_url, worksheet="System", data=pd.DataFrame([[today_str]], columns=["last_report_date"]))
        
        full_df = load_full_data()
        if send_daily_report(full_df):
            st.toast("昨日のレポートを送信しました📩")
        else:
            # 送信失敗したら元に戻す
            conn.update(spreadsheet=target_url, worksheet="System", data=pd.DataFrame([[last_sent]], columns=["last_report_date"]))


# --- 4. UI構築・メインロジック ---
st.set_page_config(page_title="電験 学習マネージャー", layout="centered", page_icon="⚡")
check_and_trigger_report()


# --- ユーザー選択とデータ読み込み管理 ---
current_user = st.sidebar.selectbox("利用者を選択", list(USER_CONFIG.keys()))
target_date = USER_CONFIG[current_user]["deadline"]

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

# --- メニュー切り替え ---
st.sidebar.divider()
mode_select = st.sidebar.radio("機能", ["学習モード", "復習モード", "分析ダッシュボード"])

# 進捗・ノルマ計算（共通）
today_dt = datetime.today().date()
unstarted_list = [q for q in db.to_dict('records') if str(q.get("last_date", "")) in ["", "nan", "None", "NaN"]]
total_count = len(db)
answered_count = total_count - len(unstarted_list)

st.sidebar.metric("目標期日までの日数", f"{max(0, (target_date - today_dt).days)}日")
st.sidebar.progress(answered_count / total_count if total_count > 0 else 0)
st.sidebar.caption(f"全体進捗: {answered_count}/{total_count} ({answered_count/total_count*100:.1f}%)")

# --- メインコンテンツの分岐 ---
if mode_select == "学習モード":
    st.title(f"⚡ 学習：{current_user}")
    fields = ["すべて"] + list(db['field'].unique())
    selected_field = st.selectbox("分野を選択", fields)
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

else:
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
        u_df = full_df_ana[full_df_ana['user'] == user]
        total = len(u_df)
        # 🌟 変更: 0除算エラーの回避
        if total > 0:
            rate = round(len(u_df[u_df['last_date'] != ""]) / total * 100, 1)
        else:
            rate = 0.0
        comparison.append({"ユーザー": user, "進捗率(%)": rate})
    
    st.table(pd.DataFrame(comparison).sort_values("進捗率(%)", ascending=False))






    # 🚩 苦手ワースト10
    st.subheader("🚩 苦手ワースト10")
    df_ana = db.copy()
    df_ana['単元'] = df_ana['q_num'].str.split('No').str[0]
    res = df_ana.groupby(['field', '単元']).agg(total=('q_num', 'count'), correct=('level', lambda x: (x >= 3).sum()), done_q=('last_date', lambda x: (x != "").sum())).reset_index()
    res['正答率'] = (res['correct'] / res['total'] * 100).round(1)
    worst = res[res['done_q'] > 0].sort_values('正答率').head(10)
    for r in worst.itertuples():
        st.error(f"{r.field}：{r.単元} ({r.正答率}%)")

# --- 4. 共通の問題表示・解答エリア ---
is_unlocked = st.session_state.get(f"unlocked_{current_user}", False)

if mode_select in ["学習モード", "復習モード"]:
    if not is_unlocked:
        st.warning("🚨 現在ロックされています。「分析・自戒」メニューから反省文を提出してください。")
    elif st.session_state.test_pool:
        st.divider()
        # 🚀 ナビゲーション
        q_labels = [f"{i+1}: {q['field']} - {q['q_num']}" for i, q in enumerate(st.session_state.test_pool)]
        selected_idx = st.selectbox("問題ジャンプ／一括スキップ", range(len(q_labels)), format_func=lambda x: q_labels[x])
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
                st.session_state.history.append({"q_num": curr["q_num"], "field": curr["field"], "old_level": curr.get("level", 0), "old_date": curr.get("last_date", "")})
                idx = st.session_state.db[(st.session_state.db['q_num'] == curr['q_num']) & (st.session_state.db['field'] == curr['field'])].index
                st.session_state.db.loc[idx, ['level', 'last_date']] = [i, datetime.today().strftime('%Y-%m-%d')]
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
