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

# ==========================================
# 🌟 【事前準備】保存関数（コードの最上段、load_full_dataの下あたりに配置）
# ==========================================
def save_study_results():
    """あなたが決めた『4つのタイミング』のみで動く一括保存関数"""
    if st.session_state.get("unsaved_count", 0) == 0 and st.session_state.get("pending_time", 0) <= 0:
        return
        
    try:
        with st.spinner('クラウドと同期中...'):
            # 学習時間を更新（タイミング3, 4）
            if st.session_state.pending_time > 0:
                curr_field = st.session_state.test_pool[0]['field'] if st.session_state.get("test_pool") else "未分類"
                update_study_time(current_user, st.session_state.pending_time, curr_field)
            
            # メインデータを一括書き込み
            full = load_full_data()
            other_users = full[full['user'] != current_user]
            # 自分の最新データ(st.session_state.db)を合体
            new_full = pd.concat([other_users, st.session_state.db], ignore_index=True)
            conn.update(spreadsheet=target_url, worksheet="Sheet1", data=new_full)
            
            # 成功したら状態をリセット
            st.session_state.pending_time = 0
            st.session_state.unsaved_count = 0
            st.toast("✅ クラウドへの同期が完了しました！")
    except Exception as e:
        st.error(f"同期エラー: {e}")

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


# ==========================================
# --- 6. メインコンテンツの分岐 ---
# ==========================================

# 1. イントロダクション（パスワード保護版）
if mode_select == "イントロダクション":
    # 以前作成したイントロダクションのコードをここに
    st.title("📚 イントロダクション")
    st.write("資料閲覧システムを表示します...")
    # (中略：以前のコードをそのまま使用)

# 2. 学習・復習モードの「準備画面」
elif mode_select in ["学習モード", "復習モード"] and not st.session_state.get("test_pool"):
    # 🌟 タイミング1：モード選択時に最新データを取得
    if "dash_full_df" not in st.session_state:
        st.session_state.dash_full_df = load_full_data()
    
    if mode_select == "学習モード":
        st.title(f"⚡ 学習：{current_user}")
        # 未着手のみを抽出（last_dateが空）
        unstarted = db[db['last_date'].isin(["", "nan", "NaN", "None", "<NA>"])]
        fields = ["すべて"] + sorted(unstarted['field'].unique().tolist())
        selected_field = st.selectbox("学習する分野を選択", fields)
        
        pool = unstarted if selected_field == "すべて" else unstarted[unstarted['field'] == selected_field]
        
        if st.button("🚀 学習開始", use_container_width=True):
            # 🌟 タイミング2：開始時に改めてデータを整理
            st.session_state.test_pool = pool.to_dict('records')
            st.session_state.history = []
            st.rerun()

    elif mode_select == "復習モード":
        st.title(f"🔄 復習：{current_user}")
        # 実施済み かつ レベル5未満 を抽出
        review_df = db[(~db['last_date'].isin(["", "nan", "NaN", "None", "<NA>"])) & (db['level'] < 5)].copy()
        
        # 🌟 ここが「変」を直すキモ：Pandasで厳密にソート（分野 -> 点数昇順 -> 問題番号）
        review_df = review_df.sort_values(by=['field', 'level', 'q_num'], ascending=[True, True, True])
        
        st.info(f"現在の復習対象: {len(review_df)} 問")
        if st.button("🔥 復習開始", use_container_width=True):
            # 🌟 タイミング2：開始時にリスト化
            st.session_state.test_pool = review_df.to_dict('records')
            st.session_state.history = []
            st.rerun()

# 3. 分析ダッシュボード
elif mode_select == "分析ダッシュボード":
    # 以前作成したタブ・折れ線グラフ・過去振り返り機能付きのダッシュボードをここに
    # (中略)
    pass

# 4. 独り言掲示板
elif mode_select == mono_label:
    # 以前作成した掲示板コードをここに
    # (中略)
    pass

# ==========================================
# --- 7. 共通の問題表示・解答エリア ---
# ==========================================
# モード分岐の「外」に置くことで、学習・復習中なら常にこの画面を最優先する
if st.session_state.get("test_pool"):
    # 初期化
    if "pending_time" not in st.session_state: st.session_state.pending_time = 0
    if "unsaved_count" not in st.session_state: st.session_state.unsaved_count = 0
    if "last_time" not in st.session_state: st.session_state.last_time = time.time()

    curr = st.session_state.test_pool[0]
    st.divider()
    st.subheader(f"【{curr['field']}】 {curr['q_num']}")
    
    # 解答ボタン（0〜5点）
    cols = st.columns(6)
    for i in range(6):
        if cols[i].button(f"{i}点", key=f"score_{i}"):
            # 1. 学習時間の計算（メモリのみ）
            st.session_state.pending_time += (time.time() - st.session_state.last_time)
            st.session_state.last_time = time.time()
            
            # 2. ローカルデータの更新（メモリのみ）
            idx = st.session_state.db[(st.session_state.db['q_num'] == curr['q_num']) & (st.session_state.db['field'] == curr['field'])].index
            st.session_state.db.loc[idx, ['level', 'last_date']] = [i, datetime.today().strftime('%Y-%m-%d')]
            
            # 3. 未保存カウント
            st.session_state.unsaved_count += 1
            st.session_state.history.append(curr)
            
            # 🌟 タイミング3：5問ごとに自動同期
            if st.session_state.unsaved_count >= 5:
                save_study_results()
            
            st.session_state.test_pool.pop(0)
            st.rerun()

    # 下部操作エリア
    st.divider()
    c1, c2, c3 = st.columns(3)
    with c1:
        if st.button("↩️ 戻る", disabled=not st.session_state.history, use_container_width=True):
            last = st.session_state.history.pop()
            st.session_state.test_pool.insert(0, last)
            st.session_state.unsaved_count = max(0, st.session_state.unsaved_count - 1)
            st.rerun()
    with c2:
        if st.button("⏭️ 後回し", use_container_width=True):
            st.session_state.test_pool.append(st.session_state.test_pool.pop(0))
            st.rerun()
    with c3:
        # 🌟 タイミング4：終了して一括保存
        if st.button("⏹️ 終了・保存", type="primary", use_container_width=True):
            save_study_results()
            st.session_state.test_pool = []
            st.rerun()
