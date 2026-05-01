import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
import random
from datetime import datetime, timedelta, timezone
import os  
import requests
import json
import time
import altair as alt  # 👈 ファイルの先頭付近に追加！

# 🌟 LINE通知用関数（エラー強制ストップ版）
def send_line_notification(message):
    import streamlit as st
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
            # 🌟 LINEから拒否されたら、画面を止めてエラー文を表示する！
            st.error(f"🚨 LINE送信失敗！\nコード: {response.status_code}\n理由: {response.text}")
            st.stop()  # ここでプログラムを強制停止させる
            return False
            
    except Exception as e:
        st.error(f"🚨 根本的な通信エラー: {e}")
        st.stop()
        return False


# 🌟 学習時間を記録する関数（分野別・重複防止・キャッシュ対策版）
def update_study_time(current_user, elapsed_seconds, field="未分類"):
    if elapsed_seconds <= 0: return
    try:
        # 強制的に最新の状態を読み込む (ttl=10)
        df = conn.read(spreadsheet=target_url, worksheet="StudyTime", ttl=10)
        today_str = datetime.today().strftime('%Y-%m-%d')
        
        # 文字列として扱い、空欄を「未分類」で埋める（エラー防止）
        if 'field' not in df.columns:
            df['field'] = "未分類"
        df['field'] = df['field'].fillna("未分類").astype(str)
        df['user'] = df['user'].astype(str)
        df['date'] = df['date'].astype(str)
        
        # 🌟 ここが重要：ユーザー、日付、さらに「分野」が【すべて一致】する行があるか探す
        mask = (df['user'] == str(current_user)) & (df['date'] == today_str) & (df['field'] == str(field))
        
        if mask.any():
            # 一致する行（同じユーザー・同じ日・同じ分野）があれば、その行に加算
            idx = df[mask].index[0]
            current_sec = pd.to_numeric(df.loc[idx, 'study_seconds'], errors='coerce')
            if pd.isna(current_sec): current_sec = 0
            df.loc[idx, 'study_seconds'] = int(current_sec + elapsed_seconds)
        else:
            # 一致する行がなければ（新しい分野なら）、新しい行を一番下に追加
            new_row = pd.DataFrame([{
                'user': str(current_user), 
                'date': today_str, 
                'study_seconds': int(elapsed_seconds), 
                'field': str(field)
            }])
            df = pd.concat([df, new_row], ignore_index=True)
            
        conn.update(spreadsheet=target_url, worksheet="StudyTime", data=df)
    except Exception as e:
        st.error(f"時間記録エラー: {e}")

# --- 2. ユーザー別個別設定 ---
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
            ("法規H27", "電気事業法関連", 26), ("法規H27", "電気設備技術基準", 47), ("法規H27", "施設管理", 32)
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
# ==========================================
#   未公開：2種移行用ユーザー設定（将来用）
# ※ 2種に切り替える際は、この中身を上の USER_CONFIG に移動させるだけでOKです。

#   その頃には僕はいないと思いますが、電験二種取得に向けて頑張ってください。僕も社会人として頑張ります。
# ==========================================

FUTURE_CONFIG = {
    "風穴2種用": {
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
            ("法規H27", "電気事業法関連", 26), ("法規H27", "電気設備技術基準", 47), ("法規H27", "施設管理", 32)
        ]
    },
    "稲垣2種用": {
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
            ("法規H27", "電気事業法関連", 26), ("法規H27", "電気設備技術基準", 47), ("法規H27", "施設管理", 32)
        ]
    }
}




# --- 3. データベース接続・型固定読み込み ---
conn = st.connection("gsheets", type=GSheetsConnection)
target_url = st.secrets["connections"]["gsheets"]["spreadsheet"]

def load_full_data():
    """スプレッドシートから全データを読み込み、型を整える"""
    try:
        # 🌟 【爆速化の要】ttl=15 から ttl=600 (10分) に大幅アップ！
        # これにより、解答ボタンを押すたびに発生していた通信ラグが消滅します。
        df = conn.read(spreadsheet=target_url, worksheet="Sheet1", usecols=[0, 1, 2, 3, 4], ttl=600)
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
        
        # 🌟 【鉄壁防御】通信エラーが起きてもアプリを落とさずスルーする！
        try:
            conn.update(spreadsheet=target_url, worksheet="Sheet1", data=new_full)
            return updated_user_df
        except Exception as e:
            # エラー時は画面上に一瞬だけ警告を出し、アプリはそのまま動かし続ける
            st.toast("⚠️ 通信制限のため新しい問題の同期をスキップしました。学習は継続できます。")
            return user_df # 追加前の既存データをとりあえず返す
        
    return user_df


# --- 4. 通知・レポート管理機能 ---

# 🌟 日本時間（JST）の設定を定義
JST = timezone(timedelta(hours=+9), 'JST')

def generate_report_message(full_df):
    """LINE送信用に精神攻撃レポートの本文を生成する"""
    now_jst = datetime.now(JST)
    yesterday_dt = (now_jst - timedelta(days=1)).date()
    yesterday_str = yesterday_dt.strftime('%Y-%m-%d')
    
    try:
        h_df = conn.read(spreadsheet=target_url, worksheet="Holidays", ttl=60)
    except:
        h_df = pd.DataFrame(columns=['user', 'holiday_date'])

    try:
        time_df = conn.read(spreadsheet=target_url, worksheet="StudyTime", ttl=60)
        time_df['study_seconds'] = pd.to_numeric(time_df['study_seconds'], errors='coerce').fillna(0)
    except:
        time_df = pd.DataFrame(columns=['user', 'date', 'study_seconds'])
    
    msg = f"📢 【電験：朝の進捗報告】\n{yesterday_dt.strftime('%m/%d')} の結果です。\n"
    msg += "="*15 + "\n"

    for user in USER_CONFIG.keys():
        is_holiday = False
        if not h_df.empty and 'user' in h_df.columns:
            user_holidays = h_df[h_df['user'] == user]['holiday_date'].tolist()
            if yesterday_str in user_holidays:
                is_holiday = True
        
        if is_holiday:
            msg += f"👤 {user}\n"
            msg += f"💬: リフレッシュ休暇中 ☕\n"
            msg += "-"*10 + "\n"
            continue 

        u_data = full_df[full_df['user'] == user]
        
        if not time_df.empty and 'date' in time_df.columns and 'user' in time_df.columns:
            y_time_data = time_df[(time_df['user'] == user) & (time_df['date'] == yesterday_str)]
            total_sec = y_time_data['study_seconds'].sum()
            total_min = int(total_sec // 60)
            if total_min >= 60:
                time_str = f"{total_min // 60}時間{total_min % 60}分"
            else:
                time_str = f"{total_min}分"
        else:
            time_str = "0分"

        valid_dates = u_data[u_data['last_date'].astype(str).str.contains("-", na=False)]['last_date']
        if not valid_dates.empty:
            last_action_str = valid_dates.max()
            last_action_date = datetime.strptime(last_action_str, '%Y-%m-%d').date()
            slack_days = (now_jst.date() - last_action_date).days - 1 
        else:
            slack_days = 999 

        if slack_days < 0: slack_days = 0

        y_data = u_data[u_data['last_date'] == yesterday_str]
        done = len(y_data)
        avg = pd.to_numeric(y_data['level'], errors='coerce').mean() if done > 0 else 0
        
        display_name = f"【💀】{user}(敗北者)" if done == 0 and slack_days >= 3 else user

        msg += f"👤 {display_name}\n📊 消化: {done}問 (平:{avg:.1f}点) / ⏱️ {time_str}\n"
        
        if done >= 20:
            msg += "💬: 合格確実。この調子で行きましょう。\n"
        elif done >= 1:
            msg += "💬: 記念受験。その程度で勉強したつもりですか？\n"
        else:
            if slack_days >= 3:
                days_text = f"{slack_days}日連続" if slack_days != 999 else "永遠に"
                msg += f"💬: かれは敗北者になってしまいました。{days_text}0問({time_str})。。\n"
            else:
                msg += "💬: 正気ですか？人生ごと不合格です。\n"
        msg += "-"*10 + "\n"
    
    msg += "※不満なら今すぐ机に向かえ。"
    return msg

def check_and_trigger_report():
    """1日の各タイミング（朝の報告・20時警告）で通知を飛ばす"""
    if st.session_state.get("report_checked", False):
        return

    now_jst = datetime.now(JST)
    today_str = now_jst.strftime('%Y-%m-%d')
    now_hour = now_jst.hour

    # --- A. 朝の進捗レポート送信 ---
    try:
        sys_df = conn.read(spreadsheet=target_url, worksheet="System", ttl=600)
        if sys_df.empty or len(sys_df.columns) == 0:
            st.error("Systemシートが空です！1行目のA列に『last_report_date』と入力してください。")
            return
            
        last_sent = str(sys_df.iloc[0, 0]) if not sys_df.empty else ""
        
        if last_sent != today_str:
            conn.update(spreadsheet=target_url, worksheet="System", data=pd.DataFrame([[today_str]], columns=["last_report_date"]))
            full_df = load_full_data()
            report_msg = generate_report_message(full_df)
            if send_line_notification(report_msg):
                st.toast("LINEへ進捗レポートを送信しました📩")
    except Exception as e:
        st.error(f"朝のレポート送信エラー: {e}")



# --- B. 20時の未完了警告送信 ---
    if now_hour >= 20:
        try:
            try:
                logs = conn.read(spreadsheet=target_url, worksheet="TaskLogs", ttl=1200)
                if 'date' not in logs.columns:
                    logs = pd.DataFrame(columns=['date', 'user', 'type'])
            except:
                logs = pd.DataFrame(columns=['date', 'user', 'type'])
            
            warning_sent = logs[(logs['date'] == today_str) & (logs['type'] == '20h_warning')]
            
            if warning_sent.empty:
                full_df = load_full_data()
                
                # 🌟 【追加】各ユーザーの目標期日を読み込む
                try:
                    goal_df = conn.read(spreadsheet=target_url, worksheet="GoalDates", ttl=600)
                except:
                    goal_df = pd.DataFrame(columns=['user', 'goal_date'])

                try:
                    h_df = conn.read(spreadsheet=target_url, worksheet="Holidays", ttl=600)
                    if 'user' not in h_df.columns:
                        h_df = pd.DataFrame(columns=['user', 'holiday_date'])
                except:
                    h_df = pd.DataFrame(columns=['user', 'holiday_date'])

                unfinished = []
                EXAM_DATE = datetime(2026, 8, 30).date()
                today_dt = datetime.today().date()

                for user in USER_CONFIG.keys():
                    # 1. 休日の人は問答無用でスキップ
                    my_h_list = []
                    if not h_df.empty and 'user' in h_df.columns:
                        my_h_list = h_df[h_df['user'] == user]['holiday_date'].dropna().tolist()
                        if today_str in my_h_list:
                            continue 
                    
                    # 2. その人の目標期日を取得
                    personal_target_date = EXAM_DATE
                    if not goal_df.empty and 'user' in goal_df.columns:
                        user_goal_row = goal_df[goal_df['user'] == user]
                        if not user_goal_row.empty:
                            personal_target_date = datetime.strptime(user_goal_row.iloc[0]['goal_date'], '%Y-%m-%d').date()

                    # 3. 残りの「実質稼働日数」を計算
                    total_days_range = [(today_dt + timedelta(days=i)) for i in range((personal_target_date - today_dt).days + 1)]
                    active_study_days = [d for d in total_days_range if d.strftime('%Y-%m-%d') not in my_h_list]
                    net_days_left = len(active_study_days)

                    # 4. 残り問題数から「1日のノルマ」を計算
                    u_df = full_df[full_df['user'] == user]
                    total_count = len(u_df)
                    unstarted_count = len(u_df[u_df['last_date'].astype(str).replace(['nan', 'None', 'NaN', '<NA>', ''], '') == ''])
                    answered_count = total_count - unstarted_count
                    remaining_questions = total_count - answered_count
                    
                    import math
                    daily_pace = math.ceil(remaining_questions / net_days_left) if net_days_left > 0 else remaining_questions
                    
                    if daily_pace <= 0:
                        continue # ノルマ0（全問完了済みなど）ならスキップ

                    # 🌟 5. 今日の進捗と「本当のノルマ」を比較！
                    done_today = len(u_df[u_df['last_date'] == today_str])
                    if done_today < daily_pace:
                        unfinished.append(f"・{user} (現在{done_today}問 / ノルマ{daily_pace}問)")
                
                if unfinished:
                    warn_msg = "🚨 【緊急警告：20時】\n以下の怠慢者が本日のノルマ未達成です。\n\n" + "\n".join(unfinished) + "\n\n日付が変わる前に挽回しましょう。"
                    if send_line_notification(warn_msg):
                        new_log = pd.DataFrame([[today_str, "system", "20h_warning"]], columns=["date", "user", "type"])
                        updated_logs = pd.concat([logs, new_log], ignore_index=True)
                        conn.update(spreadsheet=target_url, worksheet="TaskLogs", data=updated_logs)
        except Exception as e:
            st.error(f"20時警告エラー: {e}")

    st.session_state["report_checked"] = True

def check_unread_monologue(current_user):
    """独り言掲示板の未読があるかチェック"""
    try:
        mono_df = conn.read(spreadsheet=target_url, worksheet="Monologues", ttl=1300)
        status_df = conn.read(spreadsheet=target_url, worksheet="ReadStatus", ttl=1000)
        
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

# ==========================================
# 👇 ここから「5. メニュー切り替え」に続く
# ==========================================

# --- 5. メニュー切り替えとサイドバー（通知・進捗） ---

st.sidebar.title("⚡ 電験学習管理システム")

# 🌟 1. 【復活】ここでユーザーを選択・決定する！
current_user = st.sidebar.selectbox("👤 ユーザーを選択", list(USER_CONFIG.keys()))

# 🌟 2. 【復活】選ばれたユーザーのデータを読み込む（これがないと後でエラーになります）
full_df_main = load_full_data()
if 'db' not in st.session_state or st.session_state.get('current_user') != current_user:
    st.session_state.db = sync_user_data(full_df_main, current_user)
    st.session_state.current_user = current_user
db = st.session_state.db

# 🌟 3. 自動通知のチェックを走らせる
check_and_trigger_report()

# 🌟 4. ユーザーが決まったので未読チェックができる！
has_unread = check_unread_monologue(current_user)
mono_label = "ただの独り言 🔴" if has_unread else "ただの独り言"

st.sidebar.divider()
mode_select = st.sidebar.radio("機能", ["学習モード", "復習モード", "分析ダッシュボード", mono_label])


# 📅 試験日カウントダウンと進捗計算
# 🌟 本試験の日付（固定）
EXAM_DATE = datetime(2026, 8, 30).date() 
today_dt = datetime.today().date()

import math # 👈 自動計算の切り上げ(ceil)に使うため追加

# --- 🎯 1. 個人の目標期日をスプレッドシートから取得 ---
try:
    goal_df_sidebar = conn.read(spreadsheet=target_url, worksheet="GoalDates", ttl=60)
    user_goal_row = goal_df_sidebar[goal_df_sidebar['user'] == current_user]
    
    if not user_goal_row.empty:
        goal_date_str = user_goal_row.iloc[0]['goal_date']
        personal_target_date = datetime.strptime(goal_date_str, '%Y-%m-%d').date()
    else:
        personal_target_date = EXAM_DATE
except:
    personal_target_date = EXAM_DATE

# --- 📅 2. 休日を除いた「実質残り日数」の計算 と 休日LINE通知 ---
try:
    h_df = conn.read(spreadsheet=target_url, worksheet="Holidays", ttl=1200)
    my_h_list = h_df[h_df['user'] == current_user]['holiday_date'].tolist()
    
    # 今日から目標期日までの全日程
    total_days_range = [(today_dt + timedelta(days=i)) for i in range((personal_target_date - today_dt).days + 1)]
    
    # 休日を除外（勉強する日だけを残す）
    active_study_days = [d for d in total_days_range if d.strftime('%Y-%m-%d') not in my_h_list]
    net_days_left = len(active_study_days)
    
    # 🌟 追加：今日が休みの日なら、アプリを開いた瞬間にLINEで1回だけ優しく通知する
    today_str = today_dt.strftime('%Y-%m-%d')
    if today_str in my_h_list:
        try:
            # 重複送信を防ぐためにログを確認
            logs = conn.read(spreadsheet=target_url, worksheet="TaskLogs", ttl=15)
            already_sent = logs[(logs['date'] == today_str) & 
                                (logs['user'] == current_user) & 
                                (logs['type'] == 'holiday')]
            if already_sent.empty:
                # ☕ 優しいメッセージを送信（煽り一切なし！）
                msg = f"☕ 【お知らせ】\n{current_user}は今日、勉強おやすみです。\n\nたまには休息も必要ですね。しっかりリフレッシュしてください！"
                
                if send_line_notification(msg):
                    # 送信履歴を記録して、今日2回目以降は送らないようにする
                    new_log = pd.DataFrame([[today_str, current_user, "holiday"]], columns=["date", "user", "type"])
                    conn.update(spreadsheet=target_url, worksheet="TaskLogs", data=pd.concat([logs, new_log], ignore_index=True))
        except Exception as e:
            print(f"休日通知エラー: {e}")

except Exception as e:
    net_days_left = max(1, (personal_target_date - today_dt).days)

# --- 📊 3. 進捗とノルマの計算 ---
today_str = today_dt.strftime('%Y-%m-%d')
done_today_count = len(db[db['last_date'] == today_str])

unstarted_list = [q for q in db.to_dict('records') if str(q.get("last_date", "")) in ["", "nan", "None", "NaN"]]
total_count = len(db)
answered_count = total_count - len(unstarted_list)

# 残り問題数と1日あたりの必要数（自動計算）
remaining_questions = total_count - answered_count
daily_pace = math.ceil(remaining_questions / net_days_left) if net_days_left > 0 else remaining_questions

st.sidebar.divider()

# 1. 本試験までのカウントダウン（全員共通）
st.sidebar.metric("🔥 本試験まであと", f"{max(0, (EXAM_DATE - today_dt).days)}日")

# 2. 個人の目標期日と実質稼働日（ユーザーごとに可変！）
days_left_personal = (personal_target_date - today_dt).days
st.sidebar.metric(
    label=f"🏁 {current_user}の目標まで", 
    value=f"{max(0, days_left_personal)}日",
    delta=f"実質勉強日: {net_days_left}日", 
    delta_color="normal"
)

st.sidebar.progress(answered_count / total_count if total_count > 0 else 0)
st.sidebar.caption(f"全体進捗: {answered_count}/{total_count} ({answered_count/total_count*100:.1f}%)")

# 🌟 本日のノルマが「固定の20問」から「カレンダーに基づく自動計算」に進化！
st.sidebar.write(f"📊 本日のノルマ: **{done_today_count} / {daily_pace}** 問")
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
    
    # 🌟 【修正箇所】ここが「分野(field) -> 点数(level) -> 問題番号(q_num)」の順で並び替える魔法です！
    review_pool.sort(key=lambda x: (str(x.get("field", "")), int(x.get("level", 0)), str(x.get("q_num", ""))))
    
    if st.button("🔥 復習開始", use_container_width=True):
        st.session_state.test_pool = review_pool
        st.session_state.history = []
        st.rerun()

elif mode_select == "分析ダッシュボード":
    # 🌟 【完全手動更新システム】
    col_t1, col_t2 = st.columns([3, 1])
    with col_t1:
        st.title(f"📊 分析：{current_user}")
    with col_t2:
        st.write("") # 位置合わせ用
        if st.button("🔄 最新データに更新", use_container_width=True):
            # ボタンが押されたら一時メモリを消去して強制リロード
            for key in ["dash_full_df", "dash_time_df", "dash_goal_df", "dash_holiday_df"]:
                if key in st.session_state:
                    del st.session_state[key]
            st.cache_data.clear() # 他のキャッシュも念のためクリア
            st.rerun()

# --- 🌟 データの読み込み（メモリになければ取得し、永続保存） ---
    if "dash_full_df" not in st.session_state:
        with st.spinner("最新データを取得中..."):
            
            # 🌟 【鉄壁防御】メインデータ（Sheet1）もエラーから守る！
            try:
                st.session_state.dash_full_df = conn.read(spreadsheet=target_url, worksheet="Sheet1", ttl=0)
            except Exception as e:
                # 通信制限でエラーが起きた場合は、とりあえずキャッシュ（load_full_data）で代用してクラッシュを防ぐ
                st.session_state.dash_full_df = load_full_data()
                st.toast("⚠️ 通信制限中です。一部古いデータが表示されている可能性があります。1分後に再更新してください。")
                
            try:
                t_df = conn.read(spreadsheet=target_url, worksheet="StudyTime", ttl=0)
                t_df['study_seconds'] = pd.to_numeric(t_df['study_seconds'], errors='coerce').fillna(0)
                t_df['study_minutes'] = t_df['study_seconds'] / 60.0
                if 'field' not in t_df.columns:
                    t_df['field'] = '未分類'
                t_df['field'] = t_df['field'].fillna('未分類')
                t_df.loc[t_df['field'] == '', 'field'] = '未分類'
                st.session_state.dash_time_df = t_df
            except:
                st.session_state.dash_time_df = pd.DataFrame(columns=['user', 'date', 'study_seconds', 'study_minutes', 'field'])
                
            try:
                st.session_state.dash_goal_df = conn.read(spreadsheet=target_url, worksheet="GoalDates", ttl=0)
            except:
                st.session_state.dash_goal_df = pd.DataFrame(columns=['user', 'goal_date'])
                
            try:
                h_df = conn.read(spreadsheet=target_url, worksheet="Holidays", ttl=0)
                if 'user' not in h_df.columns:
                    h_df = pd.DataFrame(columns=['user', 'holiday_date'])
                st.session_state.dash_holiday_df = h_df
            except:
                st.session_state.dash_holiday_df = pd.DataFrame(columns=['user', 'holiday_date'])

    # メモリからデータを展開（以降の処理はすべて一瞬で終わります）
    full_df_ana = st.session_state.dash_full_df.copy()
    time_df = st.session_state.dash_time_df.copy()
    goal_df = st.session_state.dash_goal_df.copy()
    holiday_df = st.session_state.dash_holiday_df.copy()

    yesterday_str = (datetime.today() - timedelta(days=1)).strftime('%Y-%m-%d')
    user_yesterday = full_df_ana[(full_df_ana['user'] == current_user) & (full_df_ana['last_date'] == yesterday_str)]
    done_yesterday = len(user_yesterday)

    # シンプルな進捗報告
    if done_yesterday == 0:
        st.error(f"🚨 警告：昨日の進捗は 0 問です。言い訳せずに今日は遅れを取り戻しましょう。")
    else:
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

    # ⏱️ メンバー学習時間比較グラフ
    st.divider()
    st.subheader("⏱️ メンバー学習時間比較")
    if not time_df.empty:
        today_str = datetime.today().strftime('%Y-%m-%d')
        this_month_prefix = datetime.today().strftime('%Y-%m')
        
        today_data = time_df[time_df['date'] == today_str].groupby('user')['study_minutes'].sum().reset_index()
        month_data = time_df[time_df['date'].str.startswith(this_month_prefix, na=False)].groupby('user')['study_minutes'].sum().reset_index()
        total_data = time_df.groupby('user')['study_minutes'].sum().reset_index()
        
        col_g1, col_g2, col_g3 = st.columns(3)
        def create_altair_chart(data, title):
            return alt.Chart(data).mark_bar().encode(
                x=alt.X('user', title='ユーザー'),
                y=alt.Y('study_minutes', title='学習時間 (分)'),
                color=alt.Color('user', title='ユーザー', scale=alt.Scale(scheme='tableau10')), 
                tooltip=[alt.Tooltip('user', title='ユーザー'), alt.Tooltip('study_minutes', title='時間 (分)', format='.1f')]
            ).properties(title=title)

        with col_g1:
            st.markdown("##### 📅 今日の学習 (分)")
            if not today_data.empty and today_data['study_minutes'].sum() > 0:
                st.altair_chart(create_altair_chart(today_data, '今日の学習'), use_container_width=True)
            else: st.info("記録なし")
        with col_g2:
            st.markdown("##### 🗓️ 今月の学習 (分)")
            if not month_data.empty and month_data['study_minutes'].sum() > 0:
                st.altair_chart(create_altair_chart(month_data, '今月の学習'), use_container_width=True)
            else: st.info("記録なし")
        with col_g3:
            st.markdown("##### 🏆 累計学習 (分)")
            if not total_data.empty and total_data['study_minutes'].sum() > 0:
                st.altair_chart(create_altair_chart(total_data, '累計学習'), use_container_width=True)
            else: st.info("記録なし")
    else:
        st.info("学習時間の記録がまだありません。")

    # ==========================================
    # 👤 個人専用ダッシュボード
    st.divider()
    st.header(f"👤 {current_user} 専用ダッシュボード")

    st.subheader("🎯 分野・単元別の正解率（理解度）")
    user_db = full_df_ana[full_df_ana['user'] == current_user].copy()
    attempted = user_db[user_db['last_date'].astype(str).str.contains("-", na=False)].copy()

    if not attempted.empty:
        attempted['level'] = pd.to_numeric(attempted['level'], errors='coerce').fillna(0)
        attempted['accuracy'] = (attempted['level'] / 5.0) * 100
        col_p1, col_p2 = st.columns(2)
        with col_p1:
            st.markdown("##### 📚 分野別の理解度")
            field_acc = attempted.groupby('field')['accuracy'].mean().reset_index()
            chart_field = alt.Chart(field_acc).mark_bar(opacity=0.8).encode(
                x=alt.X('field', title='分野'),
                y=alt.Y('accuracy', title='理解度 (%)', scale=alt.Scale(domain=[0, 100])),
                color=alt.Color('field', legend=None, scale=alt.Scale(scheme='set2')),
                tooltip=[alt.Tooltip('field'), alt.Tooltip('accuracy', format='.1f')]
            ).properties(height=300)
            st.altair_chart(chart_field, use_container_width=True)
        with col_p2:
            st.markdown("##### 📖 分野ごとの単元別理解度")
            attempted['unit'] = attempted['q_num'].apply(lambda x: str(x).split('No')[0] if 'No' in str(x) else str(x))
            
            unique_fields = attempted['field'].unique()
            if len(unique_fields) > 0:
                # 🌟 【改善1】分野ごとに「タブ」を作成して横にスッキリまとめる
                tabs = st.tabs([str(f) for f in unique_fields])
                
                for idx, field_name in enumerate(unique_fields):
                    with tabs[idx]:
                        unit_acc = attempted[attempted['field'] == field_name].groupby('unit')['accuracy'].mean().reset_index()
                        
                        # 🌟 【改善2】単元の数に合わせてグラフの高さを自動計算（最低150px、1単元あたり40px確保）
                        chart_height = max(150, len(unit_acc) * 40)
                        
                        chart_unit = alt.Chart(unit_acc).mark_bar(opacity=0.8).encode(
                            x=alt.X('accuracy', title='理解度 (%)', scale=alt.Scale(domain=[0, 100])),
                            y=alt.Y('unit', title='単元', sort='-x'),
                            color=alt.Color('unit', legend=None, scale=alt.Scale(scheme='set3')),
                            tooltip=[alt.Tooltip('unit', title='単元'), alt.Tooltip('accuracy', title='理解度(%)', format='.1f')]
                        ).properties(height=chart_height)
                        
                        st.altair_chart(chart_unit, use_container_width=True)
    else: st.info("解答データがありません。")

    st.subheader("⏱️ 分野別の学習時間 (累計)")
    if not time_df.empty:
        user_time = time_df[time_df['user'] == current_user].copy()
        if not user_time.empty:
            field_time = user_time.groupby('field')['study_minutes'].sum().reset_index()
            field_time = field_time[field_time['study_minutes'] > 0]
            if not field_time.empty:
                chart_time = alt.Chart(field_time).mark_arc(innerRadius=50).encode(
                    theta=alt.Theta(field="study_minutes", type="quantitative"),
                    color=alt.Color(field="field", type="nominal", title="分野", scale=alt.Scale(scheme='pastel1')),
                    tooltip=[alt.Tooltip('field'), alt.Tooltip('study_minutes', format='.1f')]
                ).properties(height=300)
                st.altair_chart(chart_time, use_container_width=True)

    # --- 📅 目標期日 ＆ 休日設定エリア ---
    st.divider()
    st.info(f"💡 {current_user}さんの目標設定")
    try:
        my_goal_row = goal_df[goal_df['user'] == current_user]
        default_date = datetime.today() + timedelta(days=115)
        if not my_goal_row.empty:
            default_date = datetime.strptime(my_goal_row.iloc[0]['goal_date'], '%Y-%m-%d')
        new_goal = st.date_input("個人の目標期日を変更する", default_date, key="goal_date_input")
        if st.button("目標期日を更新する", key="goal_btn"):
            new_goal_str = new_goal.strftime('%Y-%m-%d')
            if not my_goal_row.empty:
                idx = goal_df[goal_df['user'] == current_user].index[0]
                goal_df.loc[idx, 'goal_date'] = new_goal_str
            else:
                new_row = pd.DataFrame([{'user': current_user, 'goal_date': new_goal_str}])
                goal_df = pd.concat([goal_df, new_row], ignore_index=True)
            
            conn.update(spreadsheet=target_url, worksheet="GoalDates", data=goal_df)
            st.session_state.dash_goal_df = goal_df # 🌟 メモリも即座に更新！
            st.success(f"目標期日を {new_goal_str} に更新しました！")
            time.sleep(1)
            st.rerun()
    except Exception as e:
        st.error(f"目標期日エラー: {e}")

    st.divider()
    st.info(f"📅 {current_user}さんの休日（勉強しない日）設定")
    try:
        my_holidays = sorted(list(set(holiday_df[holiday_df['user'] == current_user]['holiday_date'].dropna().tolist())))
        col_h1, col_h2 = st.columns(2)
        with col_h1:
            st.markdown("##### ➕ 休日の追加")
            selected_dates = st.date_input("休みにする日（または期間）を選択", value=[], key="holiday_date_input")
            if st.button("休日を追加する", key="add_holiday_btn"):
                new_dates = []
                if isinstance(selected_dates, tuple) and len(selected_dates) == 2:
                    start_d, end_d = selected_dates
                    new_dates = [(start_d + timedelta(days=i)).strftime('%Y-%m-%d') for i in range((end_d - start_d).days + 1)]
                elif isinstance(selected_dates, tuple) and len(selected_dates) == 1:
                    new_dates = [selected_dates[0].strftime('%Y-%m-%d')]
                elif selected_dates is not None and not isinstance(selected_dates, tuple):
                    new_dates = [selected_dates.strftime('%Y-%m-%d')]

                if new_dates:
                    updated_holidays = sorted(list(set(my_holidays + new_dates)))
                    other_users_holidays = holiday_df[holiday_df['user'] != current_user]
                    new_my_holidays = pd.DataFrame({'user': [current_user] * len(updated_holidays), 'holiday_date': updated_holidays})
                    updated_holiday_df = pd.concat([other_users_holidays, new_my_holidays], ignore_index=True)
                    
                    conn.update(spreadsheet=target_url, worksheet="Holidays", data=updated_holiday_df)
                    st.session_state.dash_holiday_df = updated_holiday_df # 🌟 メモリも即座に更新！
                    st.success(f"{len(new_dates)}日分追加しました！")
                    time.sleep(1)
                    st.rerun()

        with col_h2:
            st.markdown("##### 🗑️ 登録済みの休日")
            if my_holidays:
                to_remove = st.multiselect("削除する日を選択", my_holidays, key="remove_holiday_select")
                if st.button("選択した休日を消す", key="remove_holiday_btn"):
                    if to_remove:
                        updated_holidays = [d for d in my_holidays if d not in to_remove]
                        other_users_holidays = holiday_df[holiday_df['user'] != current_user]
                        new_my_holidays = pd.DataFrame({'user': [current_user] * len(updated_holidays), 'holiday_date': updated_holidays})
                        updated_holiday_df = pd.concat([other_users_holidays, new_my_holidays], ignore_index=True)
                        
                        conn.update(spreadsheet=target_url, worksheet="Holidays", data=updated_holiday_df)
                        st.session_state.dash_holiday_df = updated_holiday_df # 🌟 メモリも即座に更新！
                        st.success("休日を取り消しました！")
                        time.sleep(1)
                        st.rerun()
            else:
                st.write("登録されている休日はありません。")
    except Exception as e:
        st.error(f"休日設定エラー: {e}")

    # 🚩 各ユーザーの苦手単元ワースト
    st.divider()
    st.subheader("🚩 メンバー別 苦手単元ワースト7 ")
    cols = st.columns(len(USER_CONFIG.keys()))
    for idx, user in enumerate(USER_CONFIG.keys()):
        with cols[idx]:
            st.markdown(f"**👤 {user}の弱点**")
            u_df = full_df_ana[full_df_ana['user'] == user].copy()
            if not u_df.empty:
                u_df['単元'] = u_df['q_num'].str.split('No').str[0]
                u_df['level_num'] = pd.to_numeric(u_df['level'], errors='coerce').fillna(0)
                u_df['is_done'] = u_df['last_date'].astype(str).str.contains("-", na=False)
                attempted_df = u_df[u_df['is_done']].copy()
                if not attempted_df.empty:
                    attempted_df['理解度'] = (attempted_df['level_num'] / 5.0) * 100
                    u_res = attempted_df.groupby(['field', '単元'])['理解度'].mean().reset_index()
                    u_res['理解度'] = u_res['理解度'].round(1)
                    worst = u_res.sort_values('理解度').head(7)
                    if not worst.empty:
                        for r in worst.itertuples():
                            st.error(f"{r.field}：{r.単元}\n({r.理解度}%)")
                    else:
                        st.success("弱点なし")
                else:
                    st.success("弱点データなし\n（または未着手）")






    # ==========================================
    # 👤 個人専用ダッシュボード
    # ==========================================
    st.divider()
    st.header(f"👤 {current_user} 専用ダッシュボード")
    st.caption("※このデータはあなたしか見ることができません。")

    # --- 🎯 1. 分野・単元別の正解率 ---
    st.subheader("🎯 分野・単元別の正解率（理解度）")
    user_db = full_df_ana[full_df_ana['user'] == current_user].copy()
    attempted = user_db[user_db['last_date'].astype(str).str.contains("-", na=False)].copy()

    if not attempted.empty:
        attempted['level'] = pd.to_numeric(attempted['level'], errors='coerce').fillna(0)
        attempted['accuracy'] = (attempted['level'] / 5.0) * 100
        col_p1, col_p2 = st.columns(2)
        
        with col_p1:
            st.markdown("##### 📚 分野別の理解度")
            field_acc = attempted.groupby('field')['accuracy'].mean().reset_index()
            chart_field = alt.Chart(field_acc).mark_bar(opacity=0.8).encode(
                x=alt.X('field', title='分野'),
                y=alt.Y('accuracy', title='理解度 (%)', scale=alt.Scale(domain=[0, 100])),
                color=alt.Color('field', legend=None, scale=alt.Scale(scheme='set2')),
                tooltip=[alt.Tooltip('field', title='分野'), alt.Tooltip('accuracy', title='理解度(%)', format='.1f')]
            ).properties(height=300)
            st.altair_chart(chart_field, use_container_width=True)
            
        with col_p2:
            st.markdown("##### 📖 分野ごとの単元別理解度")
            attempted['unit'] = attempted['q_num'].apply(lambda x: str(x).split('No')[0] if 'No' in str(x) else str(x))
            unique_fields = attempted['field'].unique()
            for field_name in unique_fields:
                st.markdown(f"###### 📘 {field_name}")
                field_data = attempted[attempted['field'] == field_name]
                unit_acc = field_data.groupby('unit')['accuracy'].mean().reset_index()
                chart_unit = alt.Chart(unit_acc).mark_bar(opacity=0.8).encode(
                    x=alt.X('accuracy', title='理解度 (%)', scale=alt.Scale(domain=[0, 100])),
                    y=alt.Y('unit', title='単元', sort='-x'),
                    color=alt.Color('unit', legend=None, scale=alt.Scale(scheme='set3')),
                    tooltip=[alt.Tooltip('unit', title='単元'), alt.Tooltip('accuracy', title='理解度(%)', format='.1f')]
                ).properties(height=200)
                st.altair_chart(chart_unit, use_container_width=True)
    else:
        st.info("解答データがありません。")

    # --- ⏱️ 2. 分野別の学習時間 ---
    st.subheader("⏱️ 分野別の学習時間 (累計)")
    
    # 🌟 【改善】読み込み直さず、一番上で取得した time_df を使い回す
    if not time_df.empty:
        user_time = time_df[time_df['user'] == current_user].copy()
        if not user_time.empty:
            field_time = user_time.groupby('field')['study_minutes'].sum().reset_index()
            field_time = field_time[field_time['study_minutes'] > 0]
            if not field_time.empty:
                chart_time = alt.Chart(field_time).mark_arc(innerRadius=50).encode(
                    theta=alt.Theta(field="study_minutes", type="quantitative"),
                    color=alt.Color(field="field", type="nominal", title="分野", scale=alt.Scale(scheme='pastel1')),
                    tooltip=[alt.Tooltip('field', title='分野'), alt.Tooltip('study_minutes', title='学習時間(分)', format='.1f')]
                ).properties(height=300)
                st.altair_chart(chart_time, use_container_width=True)

    

    # 🚩 各ユーザーの苦手単元ワースト
    st.divider()
    st.subheader("🚩 メンバー別 苦手単元ワースト7 ")
    cols = st.columns(len(USER_CONFIG.keys()))
    for idx, user in enumerate(USER_CONFIG.keys()):
        with cols[idx]:
            st.markdown(f"**👤 {user}の弱点**")
            u_df = full_df_ana[full_df_ana['user'] == user].copy()
            if not u_df.empty:
                # 単元名の抽出と型の固定
                u_df['単元'] = u_df['q_num'].str.split('No').str[0]
                u_df['level_num'] = pd.to_numeric(u_df['level'], errors='coerce').fillna(0)
                u_df['is_done'] = u_df['last_date'].astype(str).str.contains("-", na=False)
                
                # 🌟 1. 「着手済み」の問題だけに絞り込む（未着手による正答率低下を防ぐ）
                attempted_df = u_df[u_df['is_done']].copy()
                
                if not attempted_df.empty:
                    # 🌟 2. 個人ダッシュボードと同じ「5点満点中の理解度(%)」を計算
                    attempted_df['理解度'] = (attempted_df['level_num'] / 5.0) * 100
                    
                    # 単元ごとに平均理解度を算出
                    u_res = attempted_df.groupby(['field', '単元'])['理解度'].mean().reset_index()
                    u_res['理解度'] = u_res['理解度'].round(1)
                    
                    # 🌟 3. 理解度が低い順に並べ替え（本当に苦手なものだけ抽出）
                    worst = u_res.sort_values('理解度').head(7)
                    
                    if not worst.empty:
                        for r in worst.itertuples():
                            st.error(f"{r.field}：{r.単元}\n({r.理解度}%)")
                    else:
                        st.success("弱点なし")
                else:
                    st.success("弱点データなし\n（または未着手）")







elif mode_select == mono_label:
    st.title(f"📝 {mono_label.replace(' 🔴', '')}")
    
    # 既読更新
    try:
        # 🌟 ここに ttl=60 を追加！
        status_df = conn.read(spreadsheet=target_url, worksheet="ReadStatus", ttl=60)
        status_df.loc[status_df['user'] == current_user, 'last_read_at'] = datetime.today().strftime('%Y-%m-%d %H:%M:%S')
        conn.update(spreadsheet=target_url, worksheet="ReadStatus", data=status_df)
    except Exception as e:
        st.error(f"既読状態の更新に失敗しました。ReadStatusシートを確認してください。")

    # 投稿フォーム
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
                    # 🌟 ここも ttl=15 から ttl=60 に変更！
                    old_mono = conn.read(spreadsheet=target_url, worksheet="Monologues", ttl=60)
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
        # 🌟 表示エラーの元凶！ここも ttl=15 から ttl=60 に変更！
        display_mono = conn.read(spreadsheet=target_url, worksheet="Monologues", ttl=60)
        
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
if mode_select in ["学習モード", "復習モード"]:
    if st.session_state.get("test_pool"):
        
        # 🌟 初期化：一時保存用と「自動セーブカウンター」を準備
        if "pending_study_time" not in st.session_state:
            st.session_state.pending_study_time = 0
        if "unsaved_count" not in st.session_state:
            st.session_state.unsaved_count = 0
        if "unsaved_answers" not in st.session_state:
            st.session_state.unsaved_answers = False

        # ⏱️ タイマー開始
        if "last_action_time" not in st.session_state:
            st.session_state.last_action_time = time.time()
            
        st.divider()
        
        # 🚀 ナビゲーションと「手動セーブ・終了」ボタンエリア
        col_nav1, col_nav2 = st.columns([2, 2])
        with col_nav1:
            q_labels = [f"{i+1}: {q['field']} - {q['q_num']}" for i, q in enumerate(st.session_state.test_pool)]
            selected_idx = st.selectbox("問題ジャンプ／一括スキップ", range(len(q_labels)), format_func=lambda x: q_labels[x], key="jump_selector")
            if selected_idx > 0 and st.button("この問題まで一気に飛ばす"):
                st.session_state.test_pool = st.session_state.test_pool[selected_idx:]
                st.rerun()
                
        with col_nav2:
            # 🌟 未保存データがある時だけ赤文字でカウントを警告
            if st.session_state.unsaved_answers:
                st.markdown(f"<div style='text-align: right; color: red; font-size: 0.8em; font-weight: bold;'>⚠️ 未保存データ({st.session_state.unsaved_count}問) / 5問で自動保存</div>", unsafe_allow_html=True)
            else:
                st.markdown("<div style='text-align: right; color: green; font-size: 0.8em;'>✅ 全てのデータが保存されています</div>", unsafe_allow_html=True)
            
            col_btn1, col_btn2 = st.columns(2)
            
            with col_btn1:
                # 💾 手動セーブ（更新）ボタン
                if st.button("💾 データ記録", disabled=not st.session_state.unsaved_answers, use_container_width=True):
                    with st.spinner('データを同期中...'):
                        curr_field = st.session_state.test_pool[0]['field'] if st.session_state.get("test_pool") else "未分類"
                        if st.session_state.pending_study_time > 0:
                            update_study_time(current_user, st.session_state.pending_study_time, curr_field)
                        if st.session_state.unsaved_answers:
                            full = load_full_data()
                            conn.update(spreadsheet=target_url, worksheet="Sheet1", data=pd.concat([full[full['user'] != current_user], st.session_state.db], ignore_index=True))
                        
                        # カウントとフラグをリセット
                        st.session_state.pending_study_time = 0
                        st.session_state.unsaved_count = 0
                        st.session_state.unsaved_answers = False
                        st.success("✅ 手動セーブ完了！")
                        time.sleep(1)
                        st.rerun()

            with col_btn2:
                # ⏹️ 学習終了ボタン（残りを保存して退出）
                if st.button("⏹️ 終了して退出", type="primary", use_container_width=True):
                    with st.spinner('最終データを保存中...'):
                        curr_field = st.session_state.test_pool[0]['field'] if st.session_state.get("test_pool") else "未分類"
                        if st.session_state.pending_study_time > 0:
                            update_study_time(current_user, st.session_state.pending_study_time, curr_field)
                        if st.session_state.unsaved_answers:
                            full = load_full_data()
                            conn.update(spreadsheet=target_url, worksheet="Sheet1", data=pd.concat([full[full['user'] != current_user], st.session_state.db], ignore_index=True))
                            
                    st.session_state.test_pool = []
                    st.session_state.pending_study_time = 0
                    st.session_state.unsaved_count = 0
                    st.session_state.unsaved_answers = False
                    if "last_action_time" in st.session_state:
                        del st.session_state["last_action_time"]
                    st.success("✅ お疲れ様でした！記録は完全に保存されました。")
                    time.sleep(1)
                    st.rerun()

        # 📖 現在の問題を表示
        curr = st.session_state.test_pool[0]
        st.subheader(f"【{curr['field']}】 {curr['q_num']}")
        
        # 解答ボタン
        cols = st.columns(6)
        for i in range(6):
            if cols[i].button(f"{i}点", key=f"b{i}"):
                
                # 🌟 時間計算とメモリの更新
                elapsed = time.time() - st.session_state.last_action_time
                st.session_state.pending_study_time += elapsed
                st.session_state.last_action_time = time.time() # タイマーリセット
                st.session_state.unsaved_count += 1 # 未保存カウントアップ
                
                st.session_state.history.append({"q_num": curr["q_num"], "field": curr["field"], "old_level": curr.get("level", 0), "old_date": curr.get("last_date", "")})
                idx = st.session_state.db[(st.session_state.db['q_num'] == curr['q_num']) & (st.session_state.db['field'] == curr['field'])].index
                
                today_str = datetime.today().strftime('%Y-%m-%d')
                st.session_state.db.loc[idx, ['level', 'last_date']] = [i, today_str]
                st.session_state.unsaved_answers = True 
                
                # 🌟 ノルマ達成チェック
                done_today = len(st.session_state.db[st.session_state.db['last_date'] == today_str])
                if done_today == 20:
                    try:
                        logs = conn.read(spreadsheet=target_url, worksheet="TaskLogs", ttl=600)
                        if logs[(logs['date'] == today_str) & (logs['user'] == current_user) & (logs['type'] == 'completed')].empty:
                            msg = f"✅ 【速報】\n{current_user}が本日の目標を突破しました！\n\n彼は自由の身です。まだ終わっていない他のメンバーは、猛烈に自分を恥じなさい。"
                            if send_line_notification(msg):
                                new_log = pd.DataFrame([[today_str, current_user, "completed"]], columns=["date", "user", "type"])
                                conn.update(spreadsheet=target_url, worksheet="TaskLogs", data=pd.concat([logs, new_log], ignore_index=True))
                                st.toast("🎉 ノルマ達成をLINEで通知しました！")
                    except: pass

                # 🌟 【復活】5問解くごとにバックグラウンドで自動セーブ！
                if st.session_state.unsaved_count >= 5:
                    try:
                        update_study_time(current_user, st.session_state.pending_study_time, curr['field'])
                        full = load_full_data()
                        conn.update(spreadsheet=target_url, worksheet="Sheet1", data=pd.concat([full[full['user'] != current_user], st.session_state.db], ignore_index=True))
                        
                        st.session_state.pending_study_time = 0
                        st.session_state.unsaved_count = 0
                        st.session_state.unsaved_answers = False
                        st.toast("💾 5問分のデータを自動セーブしました！")
                    except Exception as e:
                        st.toast("⚠️ 自動セーブに失敗しましたが、学習は継続できます。")

                st.session_state.test_pool.pop(0)
                st.rerun()

        # 戻る・スキップ
        c1, c2 = st.columns(2)
        if c1.button("↩️ 1つ戻る", disabled=not st.session_state.history, use_container_width=True):
            last = st.session_state.history.pop()
            idx = st.session_state.db[(st.session_state.db['q_num'] == last['q_num']) & (st.session_state.db['field'] == last['field'])].index
            st.session_state.db.loc[idx, ['level', 'last_date']] = [last['old_level'], last['old_date']]
            st.session_state.test_pool.insert(0, st.session_state.db.loc[idx].to_dict('records')[0])
            st.session_state.unsaved_answers = True 
            
            # 戻った分、未保存カウントを減らす
            st.session_state.unsaved_count = max(0, st.session_state.unsaved_count - 1)
            st.rerun()
            
        if c2.button("⏭️ 後回しにする", use_container_width=True):
            st.session_state.test_pool.append(st.session_state.test_pool.pop(0))
            st.rerun()
