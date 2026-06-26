#　429エラー対策、DBアクセス最適化

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








# 🌟 429エラー発生時のカウントダウン＆自動更新システム
def handle_api_error(e):
    error_msg = str(e).lower()
    # 429エラーやアクセス制限系のエラーか判定
    if "429" in error_msg or "too many requests" in error_msg or "quota" in error_msg:
        st.error("🚨 Googleの通信制限（429エラー）が発生しました。一時待機します。")
        
        # カウントダウン表示用の空箱を用意
        timer_placeholder = st.empty()
        
        # 45秒のカウントダウン
        for i in range(60, 0, -1):
            timer_placeholder.warning(f"⏳ 復帰までお待ちください... {i}秒後に自動で再試行します。")
            time.sleep(1)
            
        timer_placeholder.success("🔄 通信制限が解除されました！自動更新を実行します！")
        time.sleep(1)
        

        st.rerun()
    else:
        # 429以外のエラーの場合は、今まで通りストップさせる
        st.error(f"🚨 通信エラーが発生しました。データを保護するためアプリを停止します。\n詳細: {e}")
        st.stop()

# 🌟 LINE通知用関数（エラー強制ストップ版）
def send_line_notification(message):
    # 👇 🌟 LINE機能を一時停止（再開時はこの1行を消すか # でコメントアウトしてください）
    return True 

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


# 🌟 学習時間を記録する関数（メモリ一元管理・完全ノー通信版）
def update_study_time(current_user, elapsed_seconds, field="未分類"):
    if elapsed_seconds <= 0: return
    try:
        # 変更: 通信せず、メモリ(session_state)から直接読み込む
        df = st.session_state.study_time_df.copy()
        today_str = datetime.today().strftime('%Y-%m-%d')
        
        if 'field' not in df.columns: df['field'] = "未分類"
        df['field'] = df['field'].fillna("未分類").astype(str)
        df['user'] = df['user'].astype(str)
        df['date'] = df['date'].astype(str)
        
        mask = (df['user'] == str(current_user)) & (df['date'] == today_str) & (df['field'] == str(field))
        
        if mask.any():
            idx = df[mask].index[0]
            current_sec = pd.to_numeric(df.loc[idx, 'study_seconds'], errors='coerce')
            if pd.isna(current_sec): current_sec = 0
            df.loc[idx, 'study_seconds'] = int(current_sec + elapsed_seconds)
        else:
            new_row = pd.DataFrame([{'user': str(current_user), 'date': today_str, 'study_seconds': int(elapsed_seconds), 'field': str(field)}])
            df = pd.concat([df, new_row], ignore_index=True)
            
        # データベースを更新し、メモリ内のデータも最新に上書きする！
        conn.update(spreadsheet=target_url, worksheet="StudyTime", data=df)
        st.session_state.study_time_df = df
    except Exception as e:
        handle_api_error(e)

# --- 2. ユーザー別個別設定 ---
# --- 2. ユーザー別個別設定 ---
# 👇 FUTURE_CONFIG を USER_CONFIG に書き換えるだけ！
USER_CONFIG = {
    "佐藤1種用": {
        "deadline": datetime(2026, 8, 22).date(),
        "structure": [
            # ----- 理論 -----
            ("理論", "電界と電位", 1, 4), ("理論", "静電容量と静電エネルギー", 5, 11), ("理論", "影像法", 12, 15),
            ("理論", "磁界と磁束密度", 16, 21), ("理論", "インダクタンスと磁気エネルギー", 22, 29),
            ("理論", "回路の諸定理", 1, 10), ("理論", "三相交流回路", 11, 18), ("理論", "過渡現象", 19, 27), ("理論", "分布定数回路", 18, 31),
            ("理論", "真空電子理論", 1, 4), ("理論", "pn接合ダイオード", 5, 8), ("理論", "バイポーラトランジスタ", 9, 14),
            ("理論", "MOS形FET", 15, 19), ("理論", "演算増幅器・負帰還増幅回路・発振回路", 20, 28),
            ("理論", "電力測定", 1, 6), ("理論", "抵抗・インピーダンス測定", 7, 9), ("理論", "電気・電子応用計測", 10, 14),

            # ----- 機械 -----
            ("機械", "同期発電機", 1, 11), ("機械", "同期電動機", 12, 15),
            ("機械", "誘導電動機", 1, 9), ("機械", "誘導発電機", 10, 11), ("機械", "直流機", 12, 12),
            ("機械", "変圧器", 1, 10), ("機械", "機器", 11, 16),
            ("機械", "半導体素子", 1, 2), ("機械", "整流回路", 3, 4), ("機械", "チョッパ回路", 6, 6), ("機械", "インバータと応用", 7, 11),
            ("機械", "電気鉄道", 1, 2), ("機械", "電動機応用", 3, 4),
            ("機械", "照明の基本的事項と照明計算", 1, 7), ("機械", "光源と特徴", 8, 11), ("機械", "照明設計", 12, 14), ("機械", "電気加熱・加工", 15, 19),
            ("機械", "電池", 1, 4), ("機械", "燃料電池", 5, 6), ("機械", "電解", 7, 10),
            ("機械", "自動制御", 1, 2), ("機械", "センサおよびメカトロニクス", 3, 7),
            ("機械", "コンピュータシステム", 1, 4), ("機械", "ネットワーク", 5, 11),

            # ----- 電力 -----
            ("電力", "水車の構造と出力", 1, 8), ("電力", "調速機と負荷遮断", 9, 11), ("電力", "揚水発電所", 12, 15),
            ("電力", "火力発電所の燃料と構造", 1, 10), ("電力", "ガスタービンとコンバインドサイクル発電", 11, 14), ("電力", "火力発電所の運用", 15, 18),
            ("電力", "原子力発電", 1, 5), ("電力", "再生可能エネルギー", 1, 3),
            ("電力", "送電系統の等価回路", 1, 2), ("電力", "電力系統における故障", 3, 4), ("電力", "電力系統の安定性", 5, 12),
            ("電力", "変圧器", 1, 7), ("電力", "開閉設備・調相設備", 8, 12), ("電力", "保護リレー", 13, 19), ("電力", "開閉サージ", 20, 21), ("電力", "変電所の絶縁協調・塩害対策・耐震設計", 22, 28),
            ("電力", "架空送電", 1, 10), ("電力", "地中送電", 11, 14), ("電力", "直流送電", 15, 16),
            ("電力", "配電系統", 1, 14), ("電力", "配電線の保護", 15, 17), ("電力", "電気材料", 1, 4),

            # ----- 法規 -----
            ("法規", "電気事業法・電気事業法施行令・電気事業法施行規則", 1, 19), ("法規", "電気工事士法・電気工事業法・電気用品安全法", 20, 23),
            ("法規", "絶縁", 1, 2), ("法規", "接地", 3, 7), ("法規", "各種設備の施設", 8, 43),
            ("法規", "電力需給・周波数と電圧", 1, 15), ("法規", "施設管理全般", 16, 27)
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

# --- 3. データベース接続・型固定読み込み ---
conn = st.connection("gsheets", type=GSheetsConnection)
target_url = st.secrets["connections"]["gsheets"]["spreadsheet"]

def load_full_data():
    """全ユーザーの個別シートを読み込んで結合する（競合防止＆爆速化）"""
    all_dfs = []
    
    for user in USER_CONFIG.keys():
        try:
            sheet_name = f"Sheet_{user}"
            df = conn.read(spreadsheet=target_url, worksheet=sheet_name, ttl=600)
            
            if df.empty:
                st.error(f"🚨 警告: 『{sheet_name}』のデータが0件として読み込まれました。誤ったリセットを防ぐためシステムを停止します。")
                st.stop()

            df = df.dropna(how="all", subset=['user', 'q_num'])
            df['level'] = pd.to_numeric(df.get('level', 0), errors='coerce').fillna(0).astype(int)
            
            # 文字列のブレ（NaNなど）を排除するクレンジング
            df['last_date'] = df.get('last_date', '').fillna('').astype(str).str.strip()
            df['last_date'] = df['last_date'].replace(['nan', 'None', 'NaN', '<NA>', 'NaT'], '')
            
            # スプレッドシートに first_date 列がない場合のお守り
            if 'first_date' not in df.columns:
                df['first_date'] = ""
                
            df['first_date'] = df.get('first_date', '').fillna('').astype(str).str.strip()
            df['first_date'] = df['first_date'].replace(['nan', 'None', 'NaN', '<NA>', 'NaT'], '')
                
            for col in ['user', 'field', 'q_num']:
                df[col] = df.get(col, '').astype(str).str.strip()
                
            all_dfs.append(df[['user', 'field', 'q_num', 'level', 'last_date', 'first_date']])
            
        except Exception as e:
            handle_api_error(e)
            
    if not all_dfs:
        st.error("🚨 致命的なエラー: どのユーザーのデータも読み込めませんでした。データを保護するため停止します。")
        st.stop()
        
    return pd.concat(all_dfs, ignore_index=True)

def sync_user_data(full_df, user_name):
    """USER_CONFIGに基づいて未登録の問題を生成し、個人の専用シートを更新する"""
    user_df = full_df[full_df['user'] == user_name].copy()
    existing_q = set(user_df['field'] + "_" + user_df['q_num'])
    
    structure = USER_CONFIG[user_name]["structure"]
    new_rows = []
    
    for item in structure:
        field = str(item[0])
        cat = str(item[1])   
        
        if len(item) == 3: start, end = 1, item[2]
        else: start, end = item[2], item[3]
            
        for i in range(start, end + 1):
            q_id = f"{cat}No{i}"
            if f"{field}_{q_id}" not in existing_q:
                new_rows.append({
                    "user": str(user_name),
                    "field": field,
                    "q_num": q_id,
                    "level": 0,
                    "last_date": "",
                    "first_date": ""  # 👈 🌟ここを追加！
                })
                
    if new_rows:
        # 新しい問題を結合した「その人だけのデータ」
        updated_user_df = pd.concat([user_df, pd.DataFrame(new_rows)], ignore_index=True)
        updated_user_df['level'] = updated_user_df['level'].astype(int)
        updated_user_df['last_date'] = updated_user_df['last_date'].astype(str)
        
        try:
            # 🌟 自分の専用シートだけに上書き保存！他人のデータは一切触らない！
            conn.update(spreadsheet=target_url, worksheet=f"Sheet_{user_name}", data=updated_user_df)
            
            
            
            return updated_user_df
        except Exception as e:
            handle_api_error(e)
            return user_df
        
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
        h_df = st.session_state.holidays_df.copy()
    except:
        h_df = pd.DataFrame(columns=['user', 'holiday_date'])

    try:
        time_df = st.session_state.study_time_df.copy()
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
            msg += "💬: ノルマ達成できませんでした。\n"
        else:
            if slack_days >= 3:
                days_text = f"{slack_days}日連続" if slack_days != 999 else "永遠に"
                msg += f"💬: {days_text}0問({time_str})。。\n"
            else:
                msg += "💬: ノルマ未達成\n"
        msg += "-"*10 + "\n"
    

    return msg


def check_and_trigger_report():
    """1日の各タイミング（朝の報告・20時警告）で通知を飛ばす"""
    now_jst = datetime.now(JST)
    today_str = now_jst.strftime('%Y-%m-%d')
    now_hour = now_jst.hour

    # --- A. 朝の進捗レポート送信 ---
    if not st.session_state.get("morning_checked", False):
        # 🌟 対策1：通信を行う【前】にフラグを立てて完全ロック！二重起動を防止
        st.session_state["morning_checked"] = True
        
        try:
            # 🌟 対策2：ttl=0 に設定！ キャッシュ（記憶）を無視して最新のシートを直接確認！
            sys_df = conn.read(spreadsheet=target_url, worksheet="System", ttl=0)
            if sys_df.empty or len(sys_df.columns) == 0:
                st.error("Systemシートが空です！1行目のA列に『last_report_date』と入力してください。")
            else:
                last_sent = str(sys_df.iloc[0, 0]) if not sys_df.empty else ""
                
                if last_sent != today_str:
                    # 🌟 対策3：LINEを送る【前】にスプレッドシートを更新！
                    conn.update(spreadsheet=target_url, worksheet="System", data=pd.DataFrame([[today_str]], columns=["last_report_date"]))
                    full_df = st.session_state.master_df.copy()
                    report_msg = generate_report_message(full_df)
                    if send_line_notification(report_msg):
                        st.toast("LINEへ進捗レポートを送信しました📩")
        except Exception as e:
            st.error(f"朝のレポート送信エラー: {e}")

    # --- B. 20時の未完了警告送信 ---
    if now_hour >= 20 and not st.session_state.get("warning_checked", False):
        # 🌟 対策1：通信を行う【前】にフラグを立てて完全ロック！
        st.session_state["warning_checked"] = True
        
        try:
            # 🌟 対策2：ttl=0 に設定！ 他人の送信状況もキャッシュ無視で最新を確認！
            try:
                logs = conn.read(spreadsheet=target_url, worksheet="TaskLogs", ttl=0)
                if 'date' not in logs.columns:
                    logs = pd.DataFrame(columns=['date', 'user', 'type'])
            except:
                logs = pd.DataFrame(columns=['date', 'user', 'type'])
            
            warning_sent = logs[(logs['date'] == today_str) & (logs['type'] == '20h_warning')]
            
            if warning_sent.empty:
                full_df = st.session_state.master_df.copy()
                
                try:
                    goal_df = st.session_state.goal_dates_df.copy()
                except:
                    goal_df = pd.DataFrame(columns=['user', 'goal_date'])

                try:
                    h_df = st.session_state.holidays_df.copy()
                    if 'user' not in h_df.columns:
                        h_df = pd.DataFrame(columns=['user', 'holiday_date'])
                except:
                    h_df = pd.DataFrame(columns=['user', 'holiday_date'])

                unfinished = []
                EXAM_DATE = datetime(2026, 8, 30).date()
                today_dt = datetime.today().date()

                for user in USER_CONFIG.keys():
                    my_h_list = []
                    if not h_df.empty and 'user' in h_df.columns:
                        my_h_list = h_df[h_df['user'] == user]['holiday_date'].dropna().tolist()
                        if today_str in my_h_list:
                            continue 
                    
                    personal_target_date = EXAM_DATE
                    if not goal_df.empty and 'user' in goal_df.columns:
                        user_goal_row = goal_df[goal_df['user'] == user]
                        if not user_goal_row.empty:
                            personal_target_date = datetime.strptime(user_goal_row.iloc[0]['goal_date'], '%Y-%m-%d').date()

                    total_days_range = [(today_dt + timedelta(days=i)) for i in range((personal_target_date - today_dt).days + 1)]
                    active_study_days = [d for d in total_days_range if d.strftime('%Y-%m-%d') not in my_h_list]
                    net_days_left = len(active_study_days)

                    u_df = full_df[full_df['user'] == user]
                    total_count = len(u_df)
                    unstarted_count = len(u_df[u_df['last_date'].astype(str).replace(['nan', 'None', 'NaN', '<NA>', ''], '') == ''])
                    answered_count = total_count - unstarted_count
                    remaining_questions = total_count - answered_count
                    
                    import math
                    daily_pace = math.ceil(remaining_questions / net_days_left) if net_days_left > 0 else remaining_questions
                    
                    if daily_pace <= 0:
                        continue 

                    done_today = len(u_df[u_df['last_date'] == today_str])
                    if done_today < daily_pace:
                        unfinished.append(f"・{user} (現在{done_today}問 / ノルマ{daily_pace}問)")
                
                if unfinished:
                    warn_msg = "🚨 【緊急警告：20時】\n以下の怠慢者が本日のノルマ未達成です。\n\n" + "\n".join(unfinished) + "\n\n日付が変わる前に挽回しましょう。"
                    
                    # 🌟 対策3：LINEを送る【前】にスプレッドシートを更新！
                    new_log = pd.DataFrame([[today_str, "system", "20h_warning"]], columns=["date", "user", "type"])
                    updated_logs = pd.concat([logs, new_log], ignore_index=True)
                    conn.update(spreadsheet=target_url, worksheet="TaskLogs", data=updated_logs)
                    st.session_state.task_logs_df = updated_logs  
                    
                    send_line_notification(warn_msg)
        except Exception as e:
            st.error(f"20時警告エラー: {e}")

        st.session_state["warning_checked"] = True

def check_unread_monologue(current_user):
    """独り言掲示板の未読があるかチェック"""
    try:
        mono_df = st.session_state.monologues_df.copy()
        status_df = st.session_state.read_status_df.copy()
        
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

# --- 5. メニュー切り替えとサイドバー（通知・進捗） ---

# 🌟 アプリ起動時に「1回だけ」全データを読み込み、メモリに永続化する
if "data_initialized" not in st.session_state:
    with st.spinner("データベースを初期化しています...（初回のみ）"):
        st.session_state.master_df = load_full_data()
        
        # 👇 429対策：他の全シートも1回だけ読み込んでメモリに保存する（ttlは使わない）
        def safe_read(sheet_name, columns):
            try:
                # ttlを指定しないことで、純粋な1回限りの読み込みにする
                df = conn.read(spreadsheet=target_url, worksheet=sheet_name)
                return df if not df.empty else pd.DataFrame(columns=columns)
            except:
                return pd.DataFrame(columns=columns)

        st.session_state.study_time_df = safe_read("StudyTime", ['user', 'date', 'study_seconds', 'field'])
        st.session_state.holidays_df = safe_read("Holidays", ['user', 'holiday_date'])
        st.session_state.goal_dates_df = safe_read("GoalDates", ['user', 'goal_date'])
        st.session_state.task_logs_df = safe_read("TaskLogs", ['date', 'user', 'type'])
        st.session_state.monologues_df = safe_read("Monologues", ["date", "user", "content", "file_name"])
        st.session_state.read_status_df = safe_read("ReadStatus", ['user', 'last_read_at'])
        
        st.session_state.data_initialized = True

# 👇 この下の st.sidebar.title... はそのまま残ります
st.sidebar.title("⚡ 電験学習管理システム")



# 🌟 1. 【復活】ここでユーザーを選択・決定する！
current_user = st.sidebar.selectbox("👤 ユーザーを選択", list(USER_CONFIG.keys()))

# 🌟 2. 【復活】選ばれたユーザーのデータを読み込む（これがないと後でエラーになります）
full_df_main = st.session_state.master_df.copy()
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
mode_select = st.sidebar.radio("機能", ["学習モード", "復習モード", "分析ダッシュボード", mono_label, "英単語暗記アプリ"])




# 📅 試験日カウントダウンと進捗計算
# 🌟 本試験の日付（固定）
EXAM_DATE = datetime(2026, 8, 30).date() 
today_dt = datetime.today().date()

import math # 👈 自動計算の切り上げ(ceil)に使うため追加

# --- 🎯 1. 個人の目標期日をスプレッドシートから取得 ---
try:
    goal_df_sidebar = goal_df = st.session_state.goal_dates_df.copy()
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
    h_df = st.session_state.holidays_df.copy()
    my_h_list = h_df[h_df['user'] == current_user]['holiday_date'].tolist()
    
    # 今日から目標期日までの全日程
    total_days_range = [(today_dt + timedelta(days=i)) for i in range((personal_target_date - today_dt).days + 1)]
    
    # 休日を除外（勉強する日だけを残す）
    active_study_days = [d for d in total_days_range if d.strftime('%Y-%m-%d') not in my_h_list]
    net_days_left = len(active_study_days)
    
# 🌟 追加：今日が休みの日なら、アプリを開いた瞬間にLINEで1回だけ優しく通知する
    today_str = today_dt.strftime('%Y-%m-%d')
    if today_str in my_h_list:
        session_flag = f"holiday_notified_{today_str}_{current_user}"
        
        # 🌟 【対策1】通信の「前」にフラグを確認＆即ロック！これで画面操作のたびに通信するのを防ぐ
        if not st.session_state.get(session_flag, False):
            st.session_state[session_flag] = True  # 即座にロック！
            
            try:
                # 🌟 【対策2】ttl=600に戻して、Googleのアクセス制限（APIリミット）を回避！
                logs = st.session_state.task_logs_df.copy()
                
                if 'date' not in logs.columns:
                    logs = pd.DataFrame(columns=['date', 'user', 'type'])

                already_sent = logs[(logs['date'] == today_str) & 
                                    (logs['user'] == current_user) & 
                                    (logs['type'] == 'holiday')]
                
                if already_sent.empty:
                    # ☕ 優しいメッセージを送信（煽り一切なし！）
                    msg = f"☕ 【お知らせ】\n{current_user}は今日、勉強おやすみです。\n\nたまにはも必要ですね。しっかりリフレッシュしてください！"
                    
                    if send_line_notification(msg):
                        new_log = pd.DataFrame([[today_str, current_user, "holiday"]], columns=["date", "user", "type"])
                        conn.update(spreadsheet=target_url, worksheet="TaskLogs", data=pd.concat([logs, new_log], ignore_index=True))
                        
                        

            except Exception as e:
                print(f"休日通知エラー: {e}")

except Exception as e:
    net_days_left = max(1, (personal_target_date - today_dt).days)

# --- 📊 3. 進捗とノルマの計算 ---
today_str = today_dt.strftime('%Y-%m-%d')
# 🌟 復習が混ざらないように「初回学習日(first_date)」で今日のノルマをカウント！
done_today_count = len(db[db['first_date'] == today_str])

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
progress_percentage = (answered_count / total_count * 100) if total_count > 0 else 0.0
st.sidebar.caption(f"全体進捗: {answered_count}/{total_count} ({progress_percentage:.1f}%)")

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

# 1️⃣ 分析ダッシュボード
if mode_select == "分析ダッシュボード":
    st.title(f"📊 分析ダッシュボード：{current_user}")
    full_df_ana = st.session_state.master_df.copy()
    
    try:
        time_df = st.session_state.study_time_df.copy()
        time_df['study_seconds'] = pd.to_numeric(time_df['study_seconds'], errors='coerce').fillna(0)
        time_df['study_minutes'] = time_df['study_seconds'] / 60.0
        if 'field' not in time_df.columns: time_df['field'] = '未分類'
        time_df['field'] = time_df['field'].fillna('未分類')
        time_df.loc[time_df['field'] == '', 'field'] = '未分類'
    except:
        time_df = pd.DataFrame(columns=['user', 'date', 'study_seconds', 'study_minutes', 'field'])

    yesterday_str = (datetime.today() - timedelta(days=1)).strftime('%Y-%m-%d')
    user_yesterday = full_df_ana[(full_df_ana['user'] == current_user) & (full_df_ana['last_date'] == yesterday_str)]
    done_yesterday = len(user_yesterday)

    if done_yesterday == 0:
        st.error(f"🚨 警告：昨日の進捗は 0 問です。言い訳せずに今日は遅れを取り戻しましょう。")
    else:
        st.success(f"✅ 昨日は {done_yesterday} 問の努力が確認されました。")

    st.divider()

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

    # --- 🌟 ここから学習時間推移（空日0分対応版） ---
    st.divider()
    st.subheader("⏱️ メンバー学習時間推移")
    
    if not time_df.empty:
        user_list = sorted(time_df['user'].unique().tolist())
        color_scale = alt.Scale(domain=user_list, scheme='tableau10')

        daily_df = time_df.groupby(['date', 'user'])['study_minutes'].sum().reset_index()
        total_data = time_df.groupby('user')['study_minutes'].sum().reset_index()
        
        tab_w, tab_m, tab_t = st.tabs(["📅 週間推移", "🗓️ 月間推移", "🏆 累計学習"])
        
        with tab_w:
            st.markdown("##### 📅 週間推移 (月曜始まり)")
            try:
                min_date_str = time_df['date'].min()
                min_date = datetime.strptime(min_date_str, '%Y-%m-%d').date()
            except:
                min_date = datetime.today().date()
                
            oldest_monday = min_date - timedelta(days=min_date.weekday())
            current_monday = datetime.today().date() - timedelta(days=datetime.today().date().weekday())
            
            week_choices = []
            temp_monday = current_monday
            while temp_monday >= oldest_monday:
                temp_sunday = temp_monday + timedelta(days=6)
                label = f"{temp_monday.month}月{temp_monday.day}日 〜 {temp_sunday.month}月{temp_sunday.day}日"
                if temp_monday == current_monday:
                    label = "今週 (" + label + ")"
                week_choices.append({"label": label, "monday": temp_monday})
                temp_monday -= timedelta(days=7)
            
            selected_label = st.selectbox("確認したい週を選択", [w["label"] for w in week_choices], key="week_select")
            start_of_week = next(w["monday"] for w in week_choices if w["label"] == selected_label)
            
            week_dates = [(start_of_week + timedelta(days=i)).strftime('%Y-%m-%d') for i in range(7)]
            
            empty_w_records = [{'date': d, 'user': u, 'study_minutes': 0.0} for d in week_dates for u in user_list]
            empty_w_df = pd.DataFrame(empty_w_records)
            
            week_data = daily_df[daily_df['date'].isin(week_dates)]
            merged_w_df = pd.concat([empty_w_df, week_data]).groupby(['date', 'user'], as_index=False)['study_minutes'].sum()
            merged_w_df['display_date'] = pd.to_datetime(merged_w_df['date']).dt.strftime('%m/%d')
            
            if merged_w_df['study_minutes'].sum() > 0:
                chart_w = alt.Chart(merged_w_df).mark_line(point=True, size=3).encode(
                    x=alt.X('display_date:O', title='日付', sort=None, axis=alt.Axis(labelAngle=0)),
                    y=alt.Y('study_minutes:Q', title='学習時間 (分)'),
                    color=alt.Color('user:N', title='ユーザー', scale=color_scale),
                    tooltip=[alt.Tooltip('user:N', title='ユーザー'), alt.Tooltip('display_date:O', title='日付'), alt.Tooltip('study_minutes:Q', title='時間 (分)', format='.1f')]
                ).properties(height=350)
                st.altair_chart(chart_w, use_container_width=True)
            else: 
                st.info("この週の学習記録はありません。")
                
        with tab_m:
            st.markdown("##### 🗓️ 月間推移")
            col_y, col_m = st.columns(2)
            today_date = datetime.today()
            
            with col_y:
                sel_year = st.selectbox("年を選択", [today_date.year, today_date.year-1, today_date.year-2], index=0, key="month_year")
            with col_m:
                sel_month = st.selectbox("月を選択", list(range(1, 13)), index=today_date.month-1, key="month_month")
                
            import calendar
            _, num_days = calendar.monthrange(sel_year, sel_month)
            month_dates = [f"{sel_year}-{sel_month:02d}-{d:02d}" for d in range(1, num_days + 1)]
            
            empty_m_records = [{'date': d, 'user': u, 'study_minutes': 0.0} for d in month_dates for u in user_list]
            empty_m_df = pd.DataFrame(empty_m_records)
            
            month_prefix = f"{sel_year}-{sel_month:02d}"
            month_data = daily_df[daily_df['date'].str.startswith(month_prefix, na=False)]
            
            merged_m_df = pd.concat([empty_m_df, month_data]).groupby(['date', 'user'], as_index=False)['study_minutes'].sum()
            merged_m_df['display_date'] = pd.to_datetime(merged_m_df['date']).dt.strftime('%m/%d')
            
            if merged_m_df['study_minutes'].sum() > 0:
                chart_m = alt.Chart(merged_m_df).mark_line(point=True, size=3).encode(
                    x=alt.X('date:T', title='日付', axis=alt.Axis(format='%m/%d', tickCount=10)),
                    y=alt.Y('study_minutes:Q', title='学習時間 (分)'),
                    color=alt.Color('user:N', title='ユーザー', scale=color_scale),
                    tooltip=[alt.Tooltip('user:N', title='ユーザー'), alt.Tooltip('display_date:O', title='日付'), alt.Tooltip('study_minutes:Q', title='時間 (分)', format='.1f')]
                ).properties(height=350)
                st.altair_chart(chart_m, use_container_width=True)
            else: 
                st.info("この月の学習記録はありません。")

        with tab_t:
            st.markdown("##### 🏆 累計学習時間")
            if not total_data.empty:
                chart_t = alt.Chart(total_data).mark_bar().encode(
                    x=alt.X('user:N', title='ユーザー', axis=alt.Axis(labelAngle=0)),
                    y=alt.Y('study_minutes:Q', title='累計学習時間 (分)'),
                    color=alt.Color('user:N', title='ユーザー', scale=color_scale),
                    tooltip=[alt.Tooltip('user:N', title='ユーザー'), alt.Tooltip('study_minutes:Q', title='時間 (分)', format='.1f')]
                ).properties(height=350)
                st.altair_chart(chart_t, use_container_width=True)
            else: 
                st.info("記録なし")
    else:
        st.info("学習時間の記録がまだありません。")

    # --- 🌟 ここから個人(管理者)ダッシュボード（単元別タブ対応） ---
    st.divider()
    
    # 🌟 「佐藤」なら全員分、それ以外なら自分だけのリストを作る
    if current_user == "佐藤":
        st.header("佐藤用：全ユーザーダッシュボード")
        st.caption("※佐藤さんにのみ、全メンバーの詳細データが表示されています。")
        display_users = list(USER_CONFIG.keys())
    else:
        st.header(f"👤 {current_user} 専用ダッシュボード")
        st.caption("※このデータはあなたしか見ることができません。")
        display_users = [current_user]

    # リストに入っているユーザーの数だけ、グラフを繰り返し生成する
    for u in display_users:
        if current_user == "佐藤":
            st.markdown(f"### ▶ {u} さんのデータ")
            
        st.subheader(f"🎯 分野・単元別の正解率（理解度）{ ' - ' + u if current_user == '佐藤' else ''}")
        user_db = full_df_ana[full_df_ana['user'] == u].copy()
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
                
                unique_fields = list(attempted['field'].unique())
                if unique_fields:
                    tabs = st.tabs(unique_fields)
                    
                    for idx, field_name in enumerate(unique_fields):
                        with tabs[idx]:
                            field_data = attempted[attempted['field'] == field_name]
                            unit_acc = field_data.groupby('unit')['accuracy'].mean().reset_index()
                            
                            chart_height = max(200, len(unit_acc) * 40)
                            
                            chart_unit = alt.Chart(unit_acc).mark_bar(opacity=0.8).encode(
                                x=alt.X('accuracy', title='理解度 (%)', scale=alt.Scale(domain=[0, 100])),
                                y=alt.Y('unit', title='単元', sort='-x'),
                                color=alt.Color('unit', legend=None, scale=alt.Scale(scheme='set3')),
                                tooltip=[alt.Tooltip('unit', title='単元'), alt.Tooltip('accuracy', title='理解度(%)', format='.1f')]
                            ).properties(height=chart_height)
                            st.altair_chart(chart_unit, use_container_width=True)
        else:
            st.info(f"{u} さんの解答データがありません。")

        st.subheader(f"⏱️ 分野別の学習時間 (累計){ ' - ' + u if current_user == '佐藤' else ''}")
        if not time_df.empty:
            user_time = time_df[time_df['user'] == u].copy()
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
                else:
                    st.info("分野別の学習時間データがありません。")
            else:
                st.info("学習時間データがありません。")
        else:
            st.info("学習時間データがありません。")
            
        # 佐藤さんの場合、次のユーザーグラフとの間に区切り線を入れる
        if current_user == "佐藤":
            st.markdown("<br><br>", unsafe_allow_html=True)
            st.divider()

    st.divider()
    st.info(f"💡 {current_user}さんの目標設定")
    try:
        goal_df = st.session_state.goal_dates_df.copy()
        my_goal_row = goal_df[goal_df['user'] == current_user]
        default_date = datetime.today() + timedelta(days=115)
        if not my_goal_row.empty:
            current_goal_str = my_goal_row.iloc[0]['goal_date']
            default_date = datetime.strptime(current_goal_str, '%Y-%m-%d')
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
            st.session_state.goal_dates_df = goal_df  # 👈 修正：メモリも更新する！
            
            st.success(f"目標期日を {new_goal_str} に更新しました！")
            time.sleep(1)
            st.rerun()
            
    except Exception as e:
        handle_api_error(e)


        

    st.divider()
    st.info(f"📅 {current_user}さんの休日（勉強しない日）設定")
    try:
        holiday_df = st.session_state.holidays_df.copy()
        if 'user' not in holiday_df.columns:
            holiday_df = pd.DataFrame(columns=['user', 'holiday_date'])
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
                    
                    # 👇 修正： updated_h_df を作ってから保存するように直しました
                    updated_h_df = pd.concat([other_users_holidays, new_my_holidays], ignore_index=True)
                    conn.update(spreadsheet=target_url, worksheet="Holidays", data=updated_h_df)
                    st.session_state.holidays_df = updated_h_df
                    
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
                        
                        # 👇 修正： こちらも updated_h_df を作ってから保存するように直しました
                        updated_h_df = pd.concat([other_users_holidays, new_my_holidays], ignore_index=True)
                        conn.update(spreadsheet=target_url, worksheet="Holidays", data=updated_h_df)
                        st.session_state.holidays_df = updated_h_df
                        
                        st.success("休日を取り消しました！")
                        time.sleep(1)
                        st.rerun()
            else:
                st.write("登録されている休日はありません。")
    except Exception as e:
        handle_api_error(e)

    st.subheader("🚩 メンバー別 単元別スコア・ワースト7")
    cols = st.columns(len(USER_CONFIG.keys()))
    for idx, user in enumerate(USER_CONFIG.keys()):
        with cols[idx]:
            st.markdown(f"**👤 {user}の苦手単元**")
            u_df = full_df_ana[full_df_ana['user'] == user].copy()
            if not u_df.empty:
                # 🌟 単元名を抽出（q_numから「No」より前の文字を取り出す）
                u_df['単元'] = u_df['q_num'].apply(lambda x: str(x).split('No')[0] if 'No' in str(x) else str(x))
                
                # 数値変換と着手判定
                u_df['level_num'] = pd.to_numeric(u_df['level'], errors='coerce').fillna(0)
                u_df['is_done'] = u_df['last_date'].astype(str).str.contains("-", na=False)
                
                # 🌟 【修正点】着手済みの問題「だけ」に絞り込む（未着手の幽霊スコアを排除！）
                done_df = u_df[u_df['is_done']].copy()
                
                if not done_df.empty:
                    # 着手済みのデータだけで、平均点と問題数を集計
                    u_res = done_df.groupby(['field', '単元']).agg(
                        done_q=('level_num', 'count'),  # 解いた問題数
                        avg_score=('level_num', 'mean') # 平均点（絶対に5以下になる）
                    ).reset_index()
                    
                    # 達成率の計算（平均点 ÷ 5点満点 × 100）
                    u_res['達成率'] = (u_res['avg_score'] / 5.0 * 100).round(1)
                    
                    # 達成率が低い順（昇順）にソートし、最大7件に制限
                    worst_ranking = u_res.sort_values('達成率', ascending=True).head(7)
                    
                    for r in worst_ranking.itertuples():
                        # ご指定の条件で色分け
                        if r.達成率 <= 50:
                            st.error(f"🔴 {r.field}：{r.単元}\n({r.達成率}% : 平均{r.avg_score:.1f}点)")
                        elif r.達成率 >= 70:
                            st.success(f"🟢 {r.field}：{r.単元}\n({r.達成率}% : 平均{r.avg_score:.1f}点)")
                        else:
                            st.warning(f"🟡 {r.field}：{r.単元}\n({r.達成率}% : 平均{r.avg_score:.1f}点)")
                else:
                    st.info("着手済みの問題がありません")
            else:
                st.write("データなし")



# 2️⃣ 独り言掲示板
elif mode_select == mono_label:
    st.title(f"📝 {mono_label.replace(' 🔴', '')}")
    try:
        status_df = st.session_state.read_status_df.copy()
        status_df.loc[status_df['user'] == current_user, 'last_read_at'] = datetime.today().strftime('%Y-%m-%d %H:%M:%S')
        conn.update(spreadsheet=target_url, worksheet="ReadStatus", data=status_df)
        st.session_state.read_status_df = status_df  # 👈 修正：メモリも更新！
    except: pass

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
                
                new_mono = pd.DataFrame([[datetime.today().strftime('%Y-%m-%d %H:%M:%S'), current_user, note_content, f_name]], columns=["date", "user", "content", "file_name"])
                try:
                    mono_df = st.session_state.monologues_df.copy()
                    # 👇 修正：old_mono という存在しない変数名をやめました
                    updated_mono = pd.concat([mono_df, new_mono], ignore_index=True)
                    conn.update(spreadsheet=target_url, worksheet="Monologues", data=updated_mono)
                    st.session_state.monologues_df = updated_mono  # 👈 修正：メモリも更新！
                    
                    line_msg = f"💬 【新着：独り言】\n{current_user}さんが新しいメッセージを投稿しました。\n\n内容：\n{note_content[:50]}{'...' if len(note_content) > 50 else ''}"
                    send_line_notification(line_msg)
                    
                    st.success("投稿しました。メンバーに通知を送信しました。")
                    time.sleep(1)
                    st.rerun()
                except Exception as e:
                    handle_api_error(e)

    st.divider()
    try:
        display_mono = mono_df = st.session_state.monologues_df.copy()
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
        handle_api_error(e)

# 3️⃣ 学習モード ＆ 復習モードの分岐
elif mode_select in ["学習モード", "復習モード"]:

    # 🌟 コールバック関数：ボタンが押された瞬間に確実にデータをセット（バグ回避用）
    def start_test(pool_df):
        st.session_state.test_pool = pool_df.to_dict('records')
        st.session_state.history = []
        st.session_state.pending_study_time = 0
        st.session_state.unsaved_count = 0
        st.session_state.unsaved_answers = False
        st.session_state.last_action_time = time.time()
        st.session_state.timer_running = False # 👈 タイマーのリセット用

    # 🌟 A. 進行中のテストがあれば、優先して解答エリアを表示！
    if st.session_state.get("test_pool") and len(st.session_state.test_pool) > 0:
        
        if "pending_study_time" not in st.session_state: st.session_state.pending_study_time = 0
        if "unsaved_count" not in st.session_state: st.session_state.unsaved_count = 0
        if "unsaved_answers" not in st.session_state: st.session_state.unsaved_answers = False
        if "last_action_time" not in st.session_state: st.session_state.last_action_time = time.time()
            
        st.divider()
        
        # 🌟 消えていた機能（問題ジャンプや保存状態テキスト）も復活させつつ、インデントを完璧に修正！
        col_nav1, col_nav2 = st.columns([2, 2])
        with col_nav1:
            q_labels = [f"{i+1}: {q['field']} - {q['q_num']}" for i, q in enumerate(st.session_state.test_pool)]
            selected_idx = st.selectbox("問題ジャンプ／一括スキップ", range(len(q_labels)), format_func=lambda x: q_labels[x], key="jump_selector")
            if selected_idx > 0 and st.button("この問題まで一気に飛ばす"):
                st.session_state.test_pool = st.session_state.test_pool[selected_idx:]
                st.rerun()
                
        with col_nav2:
            if st.session_state.unsaved_answers:
                st.markdown(f"<div style='text-align: right; color: red; font-size: 0.8em; font-weight: bold;'>⚠️ 未保存データ({st.session_state.unsaved_count}問) / 5問で自動保存</div>", unsafe_allow_html=True)
            else:
                st.markdown("<div style='text-align: right; color: green; font-size: 0.8em;'>✅ 全てのデータが保存されています</div>", unsafe_allow_html=True)
            
            col_btn1, col_btn2 = st.columns(2)
            with col_btn1:
                # 🌟 key="save_btn_unique" を追加してIDを固定！
                if st.button("💾 クラウドに保存", disabled=not st.session_state.unsaved_answers, use_container_width=True, key="save_btn_unique"):
                    with st.spinner('データを同期中...'):
                        curr_field = st.session_state.test_pool[0]['field'] if st.session_state.get("test_pool") else "未分類"
                        if st.session_state.pending_study_time > 0:
                            update_study_time(current_user, st.session_state.pending_study_time, curr_field)
                        
                        if st.session_state.unsaved_answers:
                            try:
                                conn.update(spreadsheet=target_url, worksheet=f"Sheet_{current_user}", data=st.session_state.db)
                                
                                # 🌟 【最適化】再ダウンロードせず、メモリ上の全体データを直接書き換える！
                                master = st.session_state.master_df
                                st.session_state.master_df = pd.concat([master[master['user'] != current_user], st.session_state.db], ignore_index=True)
                                
                                st.session_state.pending_study_time = 0
                                st.session_state.unsaved_count = 0
                                st.session_state.unsaved_answers = False
                                st.success("✅ 手動セーブ完了！")
                                time.sleep(1)
                                st.rerun()
                            except Exception as e:
                                handle_api_error(e)

            with col_btn2:
                # 🌟 key="exit_btn_unique" を追加してIDを固定！
                if st.button("⏹️ 終了して退出", type="primary", use_container_width=True, key="exit_btn_unique"):
                    with st.spinner('最終データをクラウドに強制保存中...'):
                        curr_field = st.session_state.test_pool[0]['field'] if st.session_state.get("test_pool") else "未分類"
                        
                        # 1. 学習時間の保存
                        if st.session_state.pending_study_time > 0:
                            update_study_time(current_user, st.session_state.pending_study_time, curr_field)
                        
                        # 2. 条件を外し、終了時は問答無用で強制的にクラウドへセーブする！
                        try:
                            conn.update(spreadsheet=target_url, worksheet=f"Sheet_{current_user}", data=st.session_state.db)
                            
                            # 🌟 メモリ上の全体データも最新に更新
                            master = st.session_state.master_df
                            st.session_state.master_df = pd.concat([master[master['user'] != current_user], st.session_state.db], ignore_index=True)
                            
                        except Exception as e:
                            handle_api_error(e)
                            
                    # 3. テスト状態の完全リセット
                    st.session_state.test_pool = []
                    st.session_state.pending_study_time = 0
                    st.session_state.unsaved_count = 0
                    st.session_state.unsaved_answers = False
                    st.session_state.timer_running = False
                    if "last_action_time" in st.session_state:
                        del st.session_state["last_action_time"]
                        
                    st.success("✅ お疲れ様でした！クラウドへの最終記録が完全に保存されました。")
                    time.sleep(1)
                    st.rerun()
            

        curr = st.session_state.test_pool[0]
        st.subheader(f"【{curr['field']}】 {curr['q_num']}")


        # ✂️ ================= ここから下を上書き！ ================= ✂️

        # 👇 ====== ここから追加：メイン画面用の時間カウンター ====== 👇
        if "timer_enabled" not in st.session_state: st.session_state.timer_enabled = False
        if "timer_min" not in st.session_state: st.session_state.timer_min = 2
        if "timer_sec" not in st.session_state: st.session_state.timer_sec = 0

        st.markdown("##### ⏱️ 時間カウンター")
        c_tog, c_min, c_sec, c_btn = st.columns([1.5, 1, 1, 2.5])
        
        # 変数への代入をやめて、key="" で管理する
        c_tog.toggle("タイマーON", key="timer_enabled")
        
        if st.session_state.timer_enabled:
            c_min.number_input("分", min_value=0, max_value=60, key="timer_min", label_visibility="collapsed")
            c_sec.number_input("秒", min_value=0, max_value=59, key="timer_sec", label_visibility="collapsed")
            
            # まだスタートしていない場合（1問目の初回）
            if not st.session_state.timer_running:
                if c_btn.button("▶️ カウントスタート", type="primary", use_container_width=True):
                    st.session_state.timer_running = True
                    st.rerun()
            # スタート中の場合
            else:
                if c_btn.button("⏸️ ストップ", use_container_width=True):
                    st.session_state.timer_running = False
                    st.rerun()
                
                total_sec = st.session_state.timer_min * 60 + st.session_state.timer_sec
                if total_sec > 0:
                    
                    # 毎回リセットするのではなく「点数ボタンを押した時」だけリセットする
                    reset_key = st.session_state.get("last_action_time", 0)
                    
                    timer_html = f"""
                    <!DOCTYPE html>
                    <html>
                    <head>
                        <style>
                            body {{ margin: 0; display: flex; align-items: center; justify-content: center; font-family: sans-serif; }}
                            #timer {{ font-size: 36px; font-weight: bold; color: #333; background: #fff; padding: 10px 20px; border-radius: 10px; border: 2px solid #ddd; box-shadow: 0 4px 6px rgba(0,0,0,0.1); min-width: 160px; text-align: center; white-space: nowrap; }}
                            .urgent {{ color: white !important; background: #d62728 !important; border-color: #d62728 !important; animation: blink 1s infinite; }}
                            @keyframes blink {{ 50% {{ opacity: 0.8; }} }}
                        </style>
                    </head>
                    <body>
                        <div id="timer">{st.session_state.timer_min:02d}:{st.session_state.timer_sec:02d}</div>
                        <script>
                            var timeLeft = {total_sec};
                            var display = document.getElementById("timer");
                            
                            function playSound() {{
                                var ctx = new (window.AudioContext || window.webkitAudioContext)();
                                function beep(time, freq) {{
                                    var osc = ctx.createOscillator();
                                    var gainNode = ctx.createGain();
                                    osc.connect(gainNode);
                                    gainNode.connect(ctx.destination);
                                    osc.type = 'square';
                                    osc.frequency.setValueAtTime(freq, ctx.currentTime);
                                    gainNode.gain.setValueAtTime(0.05, ctx.currentTime);
                                    osc.start(ctx.currentTime + time);
                                    osc.stop(ctx.currentTime + time + 0.15);
                                }}
                                beep(0, 880);   
                                beep(0.25, 880); 
                                beep(0.5, 880);  
                            }}

                            var myTimer = setInterval(function() {{
                                timeLeft--;
                                if (timeLeft <= 0) {{
                                    clearInterval(myTimer);
                                    display.innerHTML = "Time Up!";
                                    display.classList.add("urgent");
                                    playSound();
                                }} else {{
                                    var m = Math.floor(timeLeft / 60);
                                    var s = timeLeft % 60;
                                    display.innerHTML = (m < 10 ? "0" : "") + m + ":" + (s < 10 ? "0" : "") + s;
                                    if (timeLeft <= 10) {{
                                        display.style.color = "#d62728"; 
                                    }}
                                }}
                            }}, 1000);
                        </script>
                    </body>
                    </html>
                    """
                    import streamlit.components.v1 as components
                    st.markdown("<br>", unsafe_allow_html=True)
                    components.html(timer_html, height=100)
        st.divider()

# ✂️ ================= 上書きするのはここまで！ ================= ✂️




        
        
        cols = st.columns(6)
        for i in range(6):
            if cols[i].button(f"{i}点", key=f"b{i}"):
                elapsed = time.time() - st.session_state.last_action_time
                st.session_state.pending_study_time += elapsed
                st.session_state.last_action_time = time.time() 
                st.session_state.unsaved_count += 1 
                
                # 🌟 old_first も履歴に保存
                st.session_state.history.append({
                    "q_num": curr["q_num"], 
                    "field": curr["field"], 
                    "old_level": curr.get("level", 0), 
                    "old_date": curr.get("last_date", ""),
                    "old_first": curr.get("first_date", "")
                })
                
                idx = st.session_state.db[(st.session_state.db['q_num'] == curr['q_num']) & (st.session_state.db['field'] == curr['field'])].index
                
                today_str = datetime.today().strftime('%Y-%m-%d')
                
                # 🌟 ここで first_date を記録する！
                old_first = curr.get("first_date", "")
                new_first = today_str if old_first in ["", "nan", "None", "NaN"] else old_first
                
                st.session_state.db.loc[idx, ['level', 'last_date', 'first_date']] = [i, today_str, new_first]
                st.session_state.unsaved_answers = True 
                
                # 🌟 今日のノルマ判定も first_date で行う！
                done_today = len(st.session_state.db[st.session_state.db['first_date'] == today_str])
                
                if done_today == daily_pace:
                    try:
                        logs = st.session_state.task_logs_df.copy()
                        if logs[(logs['date'] == today_str) & (logs['user'] == current_user) & (logs['type'] == 'completed')].empty:
                            msg = f"✅ 【速報】\n{current_user}が本日のノルマを終わらせました。\n\nお疲れ様です。"
                            if send_line_notification(msg):
                                new_log = pd.DataFrame([[today_str, current_user, "completed"]], columns=["date", "user", "type"])
                                updated_logs = pd.concat([logs, new_log], ignore_index=True)
                                
                                conn.update(spreadsheet=target_url, worksheet="TaskLogs", data=updated_logs)
                                st.session_state.task_logs_df = updated_logs  
                                
                                st.toast("🎉 ノルマ達成をLINEで通知しました！")
                    except: pass

                if st.session_state.unsaved_count >= 5:
                    try:
                        update_study_time(current_user, st.session_state.pending_study_time, curr['field'])
                        conn.update(spreadsheet=target_url, worksheet=f"Sheet_{current_user}", data=st.session_state.db)
                        
                        master = st.session_state.master_df
                        st.session_state.master_df = pd.concat([master[master['user'] != current_user], st.session_state.db], ignore_index=True)
                        
                        st.session_state.pending_study_time = 0
                        st.session_state.unsaved_count = 0
                        st.session_state.unsaved_answers = False
                        st.toast("💾 5問分のデータを自動セーブしました！")
                    except Exception as e:
                        handle_api_error(e) 

                st.session_state.test_pool.pop(0)
                st.rerun()

        c1, c2 = st.columns(2)
        if c1.button("↩️ 1つ戻る", disabled=not st.session_state.history, use_container_width=True):
            last = st.session_state.history.pop()
            idx = st.session_state.db[(st.session_state.db['q_num'] == last['q_num']) & (st.session_state.db['field'] == last['field'])].index
            
            # 🌟 戻る時も first_date を復元する
            st.session_state.db.loc[idx, ['level', 'last_date', 'first_date']] = [last['old_level'], last['old_date'], last['old_first']]
            st.session_state.test_pool.insert(0, st.session_state.db.loc[idx].to_dict('records')[0])
            st.session_state.unsaved_answers = True 
            st.session_state.unsaved_count = max(0, st.session_state.unsaved_count - 1)
            st.rerun()
            
        if c2.button("⏭️ 後回しにする", use_container_width=True):
            st.session_state.test_pool.append(st.session_state.test_pool.pop(0))
            st.rerun()

# 🌟 B. 進行中のテストがない場合は、それぞれの「準備画面」を表示
    else:
        if "dash_full_df" not in st.session_state:
            st.session_state.dash_full_df = load_full_data()

        # 🌟 【絶対判定フラグ】日付に「- (ハイフン)」が含まれていれば「解いたことがある（着手済み）」
        is_started = st.session_state.db['last_date'].astype(str).str.contains("-", na=False)

        # 🌟 【最適化】USER_CONFIGから「本来のカリキュラム順」を抽出する
        original_order = []
        for item in USER_CONFIG[current_user]["structure"]:
            field_name = str(item[0])
            if field_name not in original_order:
                original_order.append(field_name)

        # 1️⃣ 学習モードの準備画面（未着手のみ）
        if mode_select == "学習モード":
            st.title(f"⚡ 学習：{current_user}")
            
            unstarted_df = st.session_state.db[~is_started].copy()

            if unstarted_df.empty:
                st.success("🎉 おめでとうございます！すべての問題を一度は解きました。復習モードへ進みましょう！")
            else:
                # 🌟 【修正】あいうえお順（sorted）をやめて、本来のリスト順に並び替える
                available_fields = unstarted_df['field'].unique().tolist()
                field_list = [f for f in original_order if f in available_fields]
                # 万が一リストにないイレギュラーな分野名があった場合のお守り
                field_list += [f for f in available_fields if f not in original_order]
                
                field_options = ["すべて"] + field_list
                selected_field = st.selectbox("学習する分野（科目）を選んでください", field_options, key="learn_field_select")

                final_pool_df = unstarted_df if selected_field == "すべて" else unstarted_df[unstarted_df['field'] == selected_field]

                st.info(f"対象： **{selected_field}** （未着手問題：{len(final_pool_df)}問）")
                
                st.button("🚀 この内容で学習を開始する", use_container_width=True, on_click=start_test, args=(final_pool_df,))

        # 2️⃣ 復習モードの準備画面（着手済み ＆ 5点未満 ＆ 苦手順）
        elif mode_select == "復習モード":
            st.title(f"🔄 復習：{current_user}")
            
            review_df = st.session_state.db[is_started & (st.session_state.db['level'].astype(int) < 5)].copy()
            
            review_df = review_df.sort_values(by=['field', 'level', 'q_num'], ascending=[True, True, True])
            
            if review_df.empty:
                st.success("🎉 現在、復習が必要な問題（レベル5未満）はありません！完璧です！")
            else:
                # 🌟 【修正】ここに警告を入れるのが最も安全で表示も綺麗です
                if len(review_df) >= 15:
                    st.error(f"🚨 **警告：復習が溜まっています（現在 全 {len(review_df)} 問）**")
                    st.markdown("""
                        <div style="background-color: #ffebee; padding: 15px; border-radius: 10px; border: 1px solid #ffcdd2; color: #b71c1c;">
                            <b>⚠️ レベル5に到達していない問題が15問以上蓄積しています。</b><br>
                            新しい問題を進める前に、まずはこれらを優先して解消しましょう！
                        </div>
                        <br>
                    """, unsafe_allow_html=True)

                # 🌟 【修正】復習モードも本来のリスト順に並び替える
                available_fields = review_df['field'].unique().tolist()
                field_list = [f for f in original_order if f in available_fields]
                field_list += [f for f in available_fields if f not in original_order]
                
                field_options = ["すべて"] + field_list
                selected_field = st.selectbox("復習する分野（科目）を選んでください", field_options, key="review_field_select")

                final_review_df = review_df if selected_field == "すべて" else review_df[review_df['field'] == selected_field]

                st.info(f"対象： **{selected_field}** （選択中の復習対象：{len(final_review_df)}問）")
                
                st.button("🔥 この内容で復習開始", use_container_width=True, on_click=start_test, args=(final_review_df,))

        # 4️⃣ 英単語暗記アプリ
elif mode_select == "英単語暗記アプリ":
    import streamlit.components.v1 as components
    
    st.title("🔤 高機能・英単語暗記アプリ")
    st.info("※ブラウザの音声読み上げ機能とPDF出力を使用しています。")
    
    # いただいたHTMLコードをそのまま文字列として読み込ませる
    vocab_html = """
    <!DOCTYPE html>
    <html lang="ja">
    <head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>高機能・英単語暗記アプリ</title>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/html2pdf.js/0.10.1/html2pdf.bundle.min.js"></script>

    <style>
      body { font-family: 'Helvetica Neue', Arial, sans-serif; display: flex; flex-direction: column; align-items: center; justify-content: center; min-height: 100vh; margin: 0; background-color: #f0f2f5; padding: 20px 0; box-sizing: border-box; }
      
      .settings-container { display: flex; flex-direction: column; gap: 10px; margin-bottom: 20px; width: 80%; max-width: 320px; text-align: center; }
      select { width: 100%; padding: 10px; font-size: 16px; border-radius: 8px; border: 1px solid #ccc; background-color: white; cursor: pointer; }
      
      /* アクションボタン群のスタイル */
      .action-buttons { display: flex; gap: 10px; width: 80%; max-width: 320px; margin-bottom: 15px; }
      .action-btn { flex: 1; padding: 12px; font-size: 14px; border: none; border-radius: 8px; color: white; cursor: pointer; font-weight: bold; transition: all 0.3s; }
      #listenBtn { background-color: #17a2b8; }
      #listenBtn.active { background-color: #ffc107; color: #333; }
      #pdfBtn { background-color: #6f42c1; }
      .action-btn:active { transform: scale(0.95); }

      #card { width: 80%; max-width: 320px; height: 200px; background: white; border-radius: 15px; box-shadow: 0 4px 12px rgba(0,0,0,0.1); display: flex; flex-direction: column; align-items: center; justify-content: center; font-size: 28px; font-weight: bold; cursor: pointer; transition: all 0.3s ease; text-align: center; padding: 20px; user-select: none; position: relative; }
      #card:active { transform: scale(0.95); }
      
      .audio-btn { position: absolute; top: 15px; right: 15px; background: none; border: none; font-size: 24px; cursor: pointer; box-shadow: none; padding: 5px; }
      .audio-btn:active { transform: scale(0.9); }

      .review-controls { margin-top: 20px; display: flex; gap: 15px; width: 80%; max-width: 320px; }
      .review-btn { flex: 1; padding: 12px; font-size: 16px; border: none; border-radius: 25px; color: white; cursor: pointer; font-weight: bold; }
      .btn-good { background-color: #28a745; }
      .btn-bad { background-color: #dc3545; }

      .controls { margin-top: 25px; display: flex; gap: 40px; }
      .nav-btn { padding: 8px 16px; font-size: 14px; border: none; border-radius: 8px; background-color: #6c757d; color: white; cursor: pointer; }
      
      button:disabled { background-color: #ccc; cursor: not-allowed; opacity: 0.6; }
      #progress { margin-bottom: 15px; font-size: 18px; color: #555; font-weight: bold; }
      .hint { font-size: 14px; color: #888; margin-top: 15px; }
      #status { font-size: 16px; color: #007bff; margin-bottom: 20px; }
      .count-badge { font-size: 12px; color: #666; margin-top: 8px; font-weight: normal; }
    </style>
    </head>
    <body>

    <div class="settings-container">
      <select id="fileSelector" onchange="onFileSelected()">
        <option value="">-- 単語帳を選択してください --</option>
      </select>
      <select id="modeSelector" onchange="onModeSelected()">
        <option value="en-ja">英語 ➔ 日本語</option>
        <option value="ja-en">日本語 ➔ 英語</option>
      </select>
    </div>

    <div id="status">単語帳のリストを読み込み中...</div>

    <div id="mainContent" style="display: none; text-align: center; width: 100%; flex-direction: column; align-items: center;">
      
      <div class="action-buttons">
        <button id="listenBtn" class="action-btn" onclick="toggleListening()">🎧 リスニング</button>
        <button id="pdfBtn" class="action-btn" onclick="generatePDF()">📄 PDF出力</button>
      </div>
      
      <div id="progress"></div>
      
      <div id="card" onclick="manualFlipCard()">
        <button class="audio-btn" onclick="speakEnglish(event)">🔊</button>
        <div id="wordText"></div>
        <div id="countText" class="count-badge"></div>
      </div>
      
      <div class="hint">👆 カードをタップして意味を確認</div>

      <div class="review-controls">
        <button class="review-btn btn-bad" onclick="submitReview('bad')">❌ わからない</button>
        <button class="review-btn btn-good" onclick="submitReview('good')">⭕ 覚えてる</button>
      </div>

      <div class="controls">
        <button id="prevBtn" class="nav-btn" onclick="prevWord()">◀ 前へ</button>
        <button id="nextBtn" class="nav-btn" onclick="nextWord()">次へ ▶</button>
      </div>
    </div>

    <script>
      const API_URL = "https://script.google.com/macros/s/AKfycbw7ZOnsbYxup71L-5eJB5jSNQLV0C-MdYrjuTzTI63shmknipaAsjSPFbYVGzyA-ILp/exec";

      let words = [];
      let currentIndex = 0;
      let isFlipped = false;
      let currentFileId = "";
      let currentFileName = "単語リスト"; // PDFのタイトル用
      let studyMode = "en-ja"; 
      let isListening = false; 
      let wakeLock = null; 
      
      let availableVoices = [];
      window.speechSynthesis.onvoiceschanged = () => {
        availableVoices = window.speechSynthesis.getVoices();
      };

      const fileSelector = document.getElementById("fileSelector");
      const modeSelector = document.getElementById("modeSelector");
      const listenBtn = document.getElementById("listenBtn");
      const statusEl = document.getElementById("status");
      const mainContent = document.getElementById("mainContent");
      const wordTextEl = document.getElementById("wordText");
      const countTextEl = document.getElementById("countText");
      const cardEl = document.getElementById("card");
      const progressEl = document.getElementById("progress");
      const prevBtn = document.getElementById("prevBtn");
      const nextBtn = document.getElementById("nextBtn");

      async function loadFileList() {
        try {
          const response = await fetch(`${API_URL}?action=list`);
          const files = await response.json();
          if (files.error) { statusEl.innerText = `エラー: ${files.error}`; return; }
          files.forEach(file => {
            const option = document.createElement("option");
            option.value = file.id;
            option.text = file.name;
            fileSelector.appendChild(option);
          });
          statusEl.innerText = "単語帳を選んでください。";
        } catch (error) { statusEl.innerText = "ファイル一覧の取得に失敗しました。"; }
      }

      async function onFileSelected() {
        stopListening(); 
        currentFileId = fileSelector.value;
        
        // 選択されたファイル名を取得（PDFタイトルに使用）
        if (fileSelector.selectedIndex > 0) {
          currentFileName = fileSelector.options[fileSelector.selectedIndex].text;
        }

        if (!currentFileId) {
          mainContent.style.display = "none";
          statusEl.innerText = "単語帳を選んでください。";
          return;
        }
        statusEl.style.display = "block";
        statusEl.innerText = "単語データを読み込み中...";
        mainContent.style.display = "none";

        try {
          const response = await fetch(`${API_URL}?action=words&id=${currentFileId}`);
          words = await response.json();
          if (words.error) { statusEl.innerText = `エラー: ${words.error}`; return; }
          
          if (words.length > 0) {
            for (let i = words.length - 1; i > 0; i--) {
              const j = Math.floor(Math.random() * (i + 1));
              [words[i], words[j]] = [words[j], words[i]];
            }
            statusEl.style.display = "none";
            mainContent.style.display = "flex";
            currentIndex = 0;
            updateCard();
          } else {
            statusEl.innerText = "学習する単語がありません。";
          }
        } catch (error) { statusEl.innerText = "単語データの読み込みに失敗しました。"; }
      }

      function onModeSelected() {
        studyMode = modeSelector.value;
        stopListening();
        if (words.length > 0) {
          updateCard();
        }
      }

      function updateCard() {
        isFlipped = false;
        renderCardView();
        prevBtn.disabled = currentIndex === 0;
        nextBtn.disabled = currentIndex === words.length - 1;
        
        if (!isListening) {
          if (studyMode === "en-ja") {
            speakEnglish();
          }
        }
      }

      function renderCardView() {
        let currentWord = words[currentIndex];
        let safeCount = currentWord.count || 0;
        let showEnglish = (studyMode === "en-ja" && !isFlipped) || (studyMode === "ja-en" && isFlipped);
        
        if (showEnglish) {
          wordTextEl.innerText = currentWord.en;
        } else {
          wordTextEl.innerText = currentWord.ja;
        }

        if (isFlipped) {
          countTextEl.innerText = ""; 
          cardEl.style.backgroundColor = "#e3f2fd";
          cardEl.style.color = "#0277bd";
        } else {
          countTextEl.innerText = `覚えた回数: ${safeCount} / 10`;
          cardEl.style.backgroundColor = "white";
          cardEl.style.color = "black";
        }
        progressEl.innerText = `${currentIndex + 1} / ${words.length}`;
      }

      function manualFlipCard() {
        stopListening(); 
        flipCard();
      }

      function flipCard() {
        isFlipped = !isFlipped;
        renderCardView();
        
        if (!isListening) {
          if (studyMode === "ja-en" && isFlipped) {
            speakEnglish();
          }
        }
      }

      function speakEnglish(event) {
        if (event) {
          event.stopPropagation();
          stopListening();
        }
        if (!words[currentIndex]) return;
        playVoice(words[currentIndex].en, 'en');
      }

      function playVoice(text, langCode, onEndCallback) {
        const uttr = new SpeechSynthesisUtterance(text);
        uttr.lang = langCode === 'en' ? "en-US" : "ja-JP";
        
        if (availableVoices.length === 0) availableVoices = window.speechSynthesis.getVoices();
        const voices = availableVoices.filter(v => v.lang.startsWith(langCode));
        
        let preferredVoice;
        if (langCode === 'en') {
          preferredVoice = voices.find(v => v.name.includes('Samantha') || v.name.includes('Zira') || v.name.includes('Female'));
        } else {
          preferredVoice = voices.find(v => v.name.includes('Kyoko') || v.name.includes('Google 日本語') || v.name.includes('Hattori'));
        }
        
        if (preferredVoice) uttr.voice = preferredVoice;
        else if (voices.length > 0) uttr.voice = voices[0]; 

        if (onEndCallback) {
          uttr.onend = onEndCallback;
          uttr.onerror = onEndCallback; 
        }

        window.speechSynthesis.cancel(); 
        window.speechSynthesis.speak(uttr);
      }

      async function toggleListening() {
        if (isListening) {
          stopListening();
        } else {
          isListening = true;
          listenBtn.innerText = "⏹️ 停止";
          listenBtn.classList.add("active");
          
          try {
            if ('wakeLock' in navigator) {
              wakeLock = await navigator.wakeLock.request('screen');
            }
          } catch (err) {
            console.log("スリープ防止非対応");
          }
          playNextListeningSequence();
        }
      }

      function stopListening() {
        isListening = false;
        window.speechSynthesis.cancel();
        listenBtn.innerText = "🎧 リスニング";
        listenBtn.classList.remove("active");
        
        if (wakeLock !== null) {
          wakeLock.release().then(() => { wakeLock = null; });
        }
      }

      function playNextListeningSequence() {
        if (!isListening) return;

        let currentWord = words[currentIndex];
        
        let firstText = studyMode === "en-ja" ? currentWord.en : currentWord.ja;
        let firstLang = studyMode === "en-ja" ? 'en' : 'ja';
        let secondText = studyMode === "en-ja" ? currentWord.ja : currentWord.en;
        let secondLang = studyMode === "en-ja" ? 'ja' : 'en';

        isFlipped = false;
        renderCardView();

        playVoice(firstText, firstLang, () => {
          if (!isListening) return;
          
          setTimeout(() => {
            if (!isListening) return;
            isFlipped = true;
            renderCardView();

            playVoice(secondText, secondLang, () => {
              if (!isListening) return;

              setTimeout(() => {
                if (!isListening) return;
                
                if (currentIndex < words.length - 1) {
                  currentIndex++;
                } else {
                  currentIndex = 0;
                }
                playNextListeningSequence(); 
              }, 1500); 
            });
          }, 1000); 
        });
      }

      async function submitReview(status) {
        stopListening(); 
        const currentWord = words[currentIndex];
        let currentCount = currentWord.count || 0;
        
        fetch(`${API_URL}?action=review&id=${currentFileId}&en=${encodeURIComponent(currentWord.en)}&status=${status}`);

        if (status === 'good') {
          currentWord.count = currentCount + 1;
          if (currentWord.count >= 10) {
            alert(`🎉「${currentWord.en}」を10回覚えました！この単語は1ヶ月間表示されなくなります。`);
            words.splice(currentIndex, 1);
            if (words.length === 0) {
              mainContent.style.display = "none";
              statusEl.style.display = "block";
              statusEl.innerText = "素晴らしい！すべての単語の学習が完了しました！";
              return;
            }
            if (currentIndex >= words.length) { currentIndex = words.length - 1; }
            updateCard();
            return;
          }
        } else {
          currentWord.count = 0; 
        }

        if (currentIndex < words.length - 1) {
          currentIndex++;
          updateCard();
        } else {
          updateCard();
          alert("最後の単語です！");
        }
      }

      function nextWord() { stopListening(); if (currentIndex < words.length - 1) { currentIndex++; updateCard(); } }
      function prevWord() { stopListening(); if (currentIndex > 0) { currentIndex--; updateCard(); } }

      // =====================
      // 📄 PDF生成機能
      // =====================
      function generatePDF() {
        if (words.length === 0) {
          alert("出力する単語がありません。");
          return;
        }

        // PDF生成中であることをユーザーに知らせる
        const pdfBtn = document.getElementById("pdfBtn");
        const originalText = pdfBtn.innerText;
        pdfBtn.innerText = "⏳ 処理中...";
        pdfBtn.disabled = true;

        // PDF化するための専用の見えない画面（表）を作成
        const container = document.createElement("div");
        container.style.padding = "30px";
        container.style.fontFamily = "'Helvetica Neue', Arial, sans-serif";
        container.style.color = "#333";

        // タイトル
        const title = document.createElement("h2");
        title.innerText = `${currentFileName} - 学習リスト`;
        title.style.textAlign = "center";
        title.style.borderBottom = "2px solid #007bff";
        title.style.paddingBottom = "10px";
        container.appendChild(title);

        // 単語のテーブル（表）
        const table = document.createElement("table");
        table.style.width = "100%";
        table.style.borderCollapse = "collapse";
        table.style.marginTop = "20px";
        table.style.fontSize = "14px";

        // 表のヘッダー
        const thead = document.createElement("thead");
        thead.innerHTML = `
          <tr>
            <th style="border: 1px solid #ccc; padding: 10px; background-color: #f8f9fa; width: 50%;">English (英語)</th>
            <th style="border: 1px solid #ccc; padding: 10px; background-color: #f8f9fa; width: 50%;">Japanese (日本語)</th>
          </tr>
        `;
        table.appendChild(thead);

        // 表の中身（英・日の一覧）
        const tbody = document.createElement("tbody");
        words.forEach(word => {
          const tr = document.createElement("tr");
          tr.innerHTML = `
            <td style="border: 1px solid #ccc; padding: 10px; font-weight: bold;">${word.en}</td>
            <td style="border: 1px solid #ccc; padding: 10px;">${word.ja}</td>
          `;
          tbody.appendChild(tr);
        });
        table.appendChild(tbody);
        container.appendChild(table);

        // html2pdfのオプション設定
        const opt = {
          margin:       15,
          filename:     `${currentFileName}.pdf`,
          image:        { type: 'jpeg', quality: 0.98 },
          html2canvas:  { scale: 2 }, // 高画質化
          jsPDF:        { unit: 'mm', format: 'a4', orientation: 'portrait' }
        };

        // PDFを出力（完了後にボタンを元に戻す）
        html2pdf().set(opt).from(container).save().then(() => {
          pdfBtn.innerText = originalText;
          pdfBtn.disabled = false;
        }).catch(err => {
          alert("PDFの生成に失敗しました。");
          pdfBtn.innerText = originalText;
          pdfBtn.disabled = false;
        });
      }

      loadFileList();
    </script>
    </body>
    </html>
    """
    
    # iframeとして画面に埋め込む（スクロールバーが出ないように高さを少し大きめに確保）
    components.html(vocab_html, height=800, scrolling=True)
