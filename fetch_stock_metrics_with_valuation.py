#!/usr/bin/env python3
"""
J-Quants API を使用して指定銘柄の株価とバリュエーション指標を取得
"""

import os
import requests
import pandas as pd
from dotenv import load_dotenv
import time
from datetime import datetime

# 環境変数を読み込み
load_dotenv()

def authenticate():
    """認証してヘッダーを返す"""
    api_url = 'https://api.jquants.com/v1'
    refresh_token = os.getenv('REFRESH_TOKEN') or os.getenv('JQUANTS_REFRESH_TOKEN')
    
    if not refresh_token:
        raise ValueError("REFRESH_TOKEN が .env ファイルに設定されていません")
    
    res = requests.post(f"{api_url}/token/auth_refresh?refreshtoken={refresh_token}")
    res.raise_for_status()
    id_token = res.json()['idToken']
    return {'Authorization': f'Bearer {id_token}'}, api_url

def get_stock_data(code, headers, api_url):
    """1銘柄のデータを取得"""
    result = {
        'コード': code,
        '銘柄名': '',
        '最新株価': None,
        '基準日': None,
        'PER(最新)': None,
        'PER(予想)': None,
        'PBR(最新)': None
    }
    
    # 銘柄情報を取得
    try:
        res = requests.get(f"{api_url}/listed/info", params={'code': code}, headers=headers)
        if res.status_code == 200:
            data = res.json()
            if 'info' in data and data['info']:
                result['銘柄名'] = data['info'][0].get('CompanyName', '')
    except:
        pass
    
    # 株価を取得
    latest_price = None
    try:
        params = {
            'code': code,
            'from': '20241201',
            'to': '20241231'
        }
        res = requests.get(f"{api_url}/prices/daily_quotes", params=params, headers=headers)
        if res.status_code == 200:
            data = res.json()
            if 'daily_quotes' in data and data['daily_quotes']:
                latest = data['daily_quotes'][-1]
                latest_price = latest.get('Close')
                result['最新株価'] = latest_price
                result['基準日'] = latest.get('Date')
    except Exception as e:
        print(f"  株価取得エラー: {e}")
    
    # 財務情報を取得してPER/PBRを計算
    if latest_price:
        try:
            res = requests.get(f"{api_url}/fins/statements", params={'code': code}, headers=headers)
            if res.status_code == 200:
                data = res.json()
                if 'statements' in data and data['statements']:
                    # 最新の財務データを取得
                    stmt = data['statements'][0]
                    
                    # PER計算（実績EPS）
                    if stmt.get('EarningsPerShare'):
                        try:
                            eps = float(stmt['EarningsPerShare'])
                            if eps > 0:
                                result['PER(最新)'] = round(latest_price / eps, 2)
                        except:
                            pass
                    
                    # PER計算（予想EPS）
                    if stmt.get('ForecastEarningsPerShare'):
                        try:
                            forecast_eps = float(stmt['ForecastEarningsPerShare'])
                            if forecast_eps > 0:
                                result['PER(予想)'] = round(latest_price / forecast_eps, 2)
                        except:
                            pass
                    
                    # PBR計算
                    if stmt.get('BookValuePerShare'):
                        try:
                            bps = float(stmt['BookValuePerShare'])
                            if bps > 0:
                                result['PBR(最新)'] = round(latest_price / bps, 2)
                        except:
                            pass
        except Exception as e:
            print(f"  財務情報取得エラー: {e}")
    
    return result

def main():
    print("J-Quants API 株価・バリュエーション指標取得")
    print("=" * 50)
    
    # 認証
    try:
        headers, api_url = authenticate()
        print("認証成功")
    except Exception as e:
        print(f"認証失敗: {e}")
        return
    
    # 銘柄コード読み込み
    codes = []
    with open('quants-codes.txt', 'r') as f:
        for line in f:
            line = line.strip()
            if line and line != 'コード' and line.isdigit():
                codes.append(line)
    
    print(f"{len(codes)}銘柄のデータを取得します")
    print("-" * 50)
    
    # データ取得
    results = []
    for i, code in enumerate(codes):
        print(f"処理中: {code} ({i+1}/{len(codes)})")
        if i > 0:
            time.sleep(0.3)  # レート制限対策
        result = get_stock_data(code, headers, api_url)
        results.append(result)
    
    # 結果表示
    df = pd.DataFrame(results)
    
    # 表示設定
    pd.set_option('display.max_columns', None)
    pd.set_option('display.width', None)
    pd.set_option('display.max_colwidth', 20)
    
    print("\n" + "=" * 50)
    print("取得結果")
    print("=" * 50)
    print(df.to_string(index=False))
    
    # CSV保存（日付付きファイル名で出力フォルダに保存）
    import os
    os.makedirs('output', exist_ok=True)
    output_file = f"output/stock_metrics_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
    df.to_csv(output_file, index=False, encoding='utf-8-sig')
    print(f"\n結果を保存しました: {output_file}")

if __name__ == "__main__":
    main()