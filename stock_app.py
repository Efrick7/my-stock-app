import streamlit as st
import yfinance as yf
import pandas as pd
from datetime import datetime

# 1. 設定網頁標題與手機版面配置
st.set_page_config(page_title="台股波段提示模型", layout="centered")
st.title("📈 台股 10MA+60MA+布林通道提示模型")

# 2. 做出讓手機可以輸入與選擇的介面
stock_id = st.text_input("請輸入台股代號（例如: 3189, 2330）", "3189")
formatted_id = f"{stock_id}.TW"

# 3. 執行按鈕
if st.button("開始分析最新盤勢"):
    try:
        today_date = datetime.now().strftime('%Y-%m-%d')
        
        # 抓取資料
        df = yf.download(formatted_id, start="2025-01-01", end=today_date)
        
        if len(df) == 0:
            st.error("找不到該股票資料，請檢查代號是否正確。")
        else:
            # 【鋼鐵防禦層】強力拍扁欄位
            if isinstance(df.columns, pd.MultiIndex):
                df.columns = [col[1] if isinstance(col, tuple) else col for col in df.columns]
            else:
                df.columns = [col if isinstance(col, str) else str(col) for col in df.columns]
            
            for col in df.columns:
                if 'Close' in col:
                    df = df.rename(columns={col: 'Close'})
            
            # 確保資料格式被壓扁成正確的一維數據
            close_series = df['Close'].squeeze()
            
            # 【純數學方法計算指標】
            df['SMA10'] = close_series.rolling(window=10).mean()
            df['SMA60'] = close_series.rolling(window=60).mean()
            
            # 計算布林通道
            df['Middle'] = close_series.rolling(window=20).mean()
            std20 = close_series.rolling(window=20).std()
            df['Upper'] = df['Middle'] + (2 * std20)
            df['Lower'] = df['Middle'] - (2 * std20)
            
            # 買賣訊號邏輯
            df['Signal'] = 0
            buy_condition = (close_series > df['Upper']) & (df['SMA10'] > df['SMA60'])
            sell_condition = (close_series < df['Middle'])
            
            df.loc[buy_condition, 'Signal'] = 1
            df.loc[sell_condition, 'Signal'] = -1
            df['Position'] = df['Signal'].diff()
            
            # 獲取最新一天的狀態
            latest_row = df.iloc[-1]
            latest_price = float(latest_row['Close'])
            
            valid_positions = df[df['Position'] != 0]
            latest_signal = valid_positions.iloc[-1]['Position'] if len(valid_positions) > 0 else 0
            
            # 在畫面上秀出最新提示
            st.metric(label=f"最新收盤價 ({today_date})", value=f"{latest_price:.2f} 元")
            
            if latest_signal == 1:
                st.success("🔥 最新模型提示：觸發【買進訊號】！突破布林上軌且多頭排列。")
            elif latest_signal == -1:
                st.error("🚨 最新模型提示：觸發【賣出訊號】！跌破布林中軌，短線轉弱。")
            else:
                st.info("💎 最新模型提示：目前訊號無變化，請依前次訊號操作。")
                
            # ==========================================
            # 【全新升級】使用 Streamlit 原生高效能網頁圖表
            # ==========================================
            st.subheader("📊 互動式 K 線與指標走勢圖")
            
            # 準備要畫圖的表格，只留下需要的線條
            chart_data = df[['Close', 'SMA10', 'SMA60', 'Upper', 'Middle', 'Lower']]
            
            # 一行代碼，直接畫出高畫質、可手指縮放的動態圖表！
            st.line_chart(chart_data)
            # ==========================================
            
    except Exception as e:
        st.error(f"執行時發生錯誤: {e}\n請確認代號是否輸入正確。")
