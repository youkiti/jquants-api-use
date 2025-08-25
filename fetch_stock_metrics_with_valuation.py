#!/usr/bin/env python3
"""
J-Quants API を使用して指定銘柄の株価とバリュエーション指標を取得
"""

import os
import requests
import pandas as pd
from dotenv import load_dotenv
import time
from datetime import datetime, timedelta

def get_latest_price_date_range():
    """最新株価取得のための動的日付範囲を生成"""
    today = datetime.now()
    
    # 日本市場を考慮した確実な日付範囲設定
    # 過去90日間（約3ヶ月）で確実にデータを取得
    start_date = (today - timedelta(days=90)).strftime('%Y%m%d')
    end_date = today.strftime('%Y%m%d')
    
    return start_date, end_date

def get_valid_float_value(values):
    """複数の値から有効な浮動小数点数を取得する"""
    for value in values:
        if value and str(value).strip():
            try:
                return float(value)
            except (ValueError, TypeError):
                continue
    return None

def select_best_financial_data(statements):
    """最適な財務データを選択する（実績EPSがある年次決算優先）"""
    from datetime import datetime
    
    if not statements:
        return None
    
    # 現在日付
    today = datetime.now().strftime('%Y-%m-%d')
    
    # 未来日付のデータを除外
    valid_statements = []
    for stmt in statements:
        period_end = stmt.get('CurrentPeriodEndDate', '')
        if period_end and period_end <= today:
            valid_statements.append(stmt)
        else:
            print(f"  未来日付データ除外: {period_end}")
    
    if not valid_statements:
        print("  有効な財務データなし（すべて未来日付）")
        return None
    
    # 年次決算（FY）を優先的に選択
    fy_statements = [s for s in valid_statements if s.get('TypeOfCurrentPeriod') == 'FY']
    quarterly_statements = [s for s in valid_statements if s.get('TypeOfCurrentPeriod') in ['1Q', '2Q', '3Q', '4Q']]
    
    # 優先順位: 1) 実績EPSがある最新の年次決算 2) 実績EPSがある最新の四半期決算
    if fy_statements:
        # 年次決算を日付順でソート
        fy_sorted = sorted(fy_statements, 
                          key=lambda x: (x.get('CurrentPeriodEndDate', ''), 
                                       x.get('DisclosedDate', '')), 
                          reverse=True)
        
        # 実績EPSが存在する最新の年次決算を探す
        for stmt in fy_sorted:
            eps = get_valid_float_value([
                stmt.get('EarningsPerShare'),
                stmt.get('NonConsolidatedEarningsPerShare')
            ])
            if eps and eps != 0:
                print(f"  年次決算データ選択（実績EPSあり）: {stmt.get('CurrentPeriodEndDate')} (FY) EPS={eps}")
                return stmt
        
        # 実績EPSがない場合でも最新のFYを返す（BPS等の他指標用）
        selected = fy_sorted[0]
        print(f"  年次決算データ選択（実績EPSなし）: {selected.get('CurrentPeriodEndDate')} (FY)")
        
        # ただし実績EPSがない場合は前期のFYも探索
        if len(fy_sorted) > 1:
            for prev_stmt in fy_sorted[1:]:
                prev_eps = get_valid_float_value([
                    prev_stmt.get('EarningsPerShare'),
                    prev_stmt.get('NonConsolidatedEarningsPerShare')
                ])
                if prev_eps and prev_eps != 0:
                    print(f"  → 前期年次決算からEPS取得: {prev_stmt.get('CurrentPeriodEndDate')} EPS={prev_eps}")
                    # 最新FYの他の情報と前期EPSを組み合わせる
                    selected['FallbackEarningsPerShare'] = str(prev_eps)
                    selected['FallbackEPSPeriod'] = prev_stmt.get('CurrentPeriodEndDate')
                    break
        
        return selected
    
    elif quarterly_statements:
        # 四半期決算を日付順でソート  
        q_sorted = sorted(quarterly_statements,
                         key=lambda x: (x.get('CurrentPeriodEndDate', ''),
                                      x.get('DisclosedDate', '')),
                         reverse=True)
        
        # 実績EPSがある最新の四半期決算を探す
        for stmt in q_sorted:
            eps = get_valid_float_value([
                stmt.get('EarningsPerShare'),
                stmt.get('NonConsolidatedEarningsPerShare')
            ])
            if eps and eps != 0:
                # 四半期EPSを年換算
                period_type = stmt.get('TypeOfCurrentPeriod', '')
                if period_type in ['1Q', '2Q', '3Q']:
                    annualized_eps = eps * 4  # 簡易的に4倍（より正確には期間に応じた係数を使用）
                    stmt['AnnualizedEarningsPerShare'] = str(annualized_eps)
                    print(f"  四半期データ選択: {stmt.get('CurrentPeriodEndDate')} ({period_type}) EPS={eps}→年換算{annualized_eps:.2f}")
                else:
                    print(f"  四半期データ選択: {stmt.get('CurrentPeriodEndDate')} ({period_type}) EPS={eps}")
                return stmt
        
        # 実績EPSがない場合
        selected = q_sorted[0]
        print(f"  四半期データ選択（実績EPSなし）: {selected.get('CurrentPeriodEndDate')} ({selected.get('TypeOfCurrentPeriod')})")
        return selected
    
    else:
        print("  財務データ選択失敗: 有効なデータなし")
        return None

def get_comprehensive_financial_data(code, headers, api_url):
    """包括的な財務データを取得（ページネーション対応、過去3年分）"""
    all_statements = []
    pagination_key = None
    
    try:
        # まずデフォルトのパラメータで取得を試行
        while True:
            params = {'code': code}
            if pagination_key:
                params['pagination_key'] = pagination_key
            
            res = requests.get(f"{api_url}/fins/statements", params=params, headers=headers)
            if res.status_code != 200:
                print(f"  財務API呼び出し失敗: {res.status_code}")
                break
                
            data = res.json()
            statements = data.get('statements', [])
            
            if not statements:
                break
            
            all_statements.extend(statements)
            
            pagination_key = data.get('pagination_key')
            if not pagination_key:
                break
                
            # レート制限対策
            time.sleep(0.1)
        
        # 過去3年分のデータにフィルタ
        today = datetime.now()
        start_date = (today - timedelta(days=3*365)).strftime('%Y-%m-%d')
        
        filtered_statements = [
            s for s in all_statements 
            if s.get('CurrentPeriodEndDate', '') >= start_date
        ]
            
        print(f"  財務データ取得完了: {len(filtered_statements)}件 (全{len(all_statements)}件中、期間: {start_date}〜)")
        return filtered_statements
        
    except Exception as e:
        print(f"  包括的財務データ取得エラー: {e}")
        return []

def search_forecast_eps_in_statements(statements):
    """複数の財務データから予想EPSを探索する"""
    if not statements:
        return None, None
    
    today = datetime.now().strftime('%Y-%m-%d')
    
    # 有効なデータのみをフィルタ
    valid_statements = [s for s in statements 
                       if s.get('CurrentPeriodEndDate', '') <= today]
    
    # 日付順でソート（最新順）
    sorted_statements = sorted(valid_statements,
                             key=lambda x: (x.get('CurrentPeriodEndDate', ''),
                                          x.get('DisclosedDate', '')),
                             reverse=True)
    
    # すべての決算期データから予想EPSを探索
    for stmt in sorted_statements:
        # 連結予想EPS
        forecast_eps = get_valid_float_value([
            stmt.get('ForecastEarningsPerShare'),
            stmt.get('ForecastNonConsolidatedEarningsPerShare')
        ])
        
        if forecast_eps and forecast_eps > 0:
            period_type = stmt.get('TypeOfCurrentPeriod', 'N/A')
            period_end = stmt.get('CurrentPeriodEndDate', 'N/A')
            print(f"  予想EPS発見: {forecast_eps}円 ({period_end} {period_type})")
            return forecast_eps, stmt
    
    print("  予想EPS未発見: 全決算期データで空")
    return None, None

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
        '最新株価日付': None,
        '分析実行日': None,
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
    
    # 株価を取得（最新データ）
    latest_price = None
    try:
        # まずデフォルト（パラメータなし）で試行
        params = {'code': code}
        res = requests.get(f"{api_url}/prices/daily_quotes", params=params, headers=headers)
        
        if res.status_code == 200:
            data = res.json()
            if 'daily_quotes' in data and data['daily_quotes']:
                latest = data['daily_quotes'][-1]
                latest_price = latest.get('Close')
                result['最新株価'] = latest_price
                result['最新株価日付'] = latest.get('Date')
                result['分析実行日'] = datetime.now().strftime('%Y-%m-%d')
                print(f"  株価取得成功: {latest_price}円 ({result['最新株価日付']}) [分析日: {result['分析実行日']}]")
            else:
                print(f"  株価データなし（デフォルト取得）")
        else:
            # デフォルトで失敗した場合、日付範囲指定で再試行
            print(f"  デフォルト取得失敗({res.status_code})、日付範囲で再試行...")
            start_date, end_date = get_latest_price_date_range()
            params = {
                'code': code,
                'from': start_date,
                'to': end_date
            }
            
            res = requests.get(f"{api_url}/prices/daily_quotes", params=params, headers=headers)
            if res.status_code == 200:
                data = res.json()
                if 'daily_quotes' in data and data['daily_quotes']:
                    latest = data['daily_quotes'][-1]
                    latest_price = latest.get('Close')
                    result['最新株価'] = latest_price
                    result['最新株価日付'] = latest.get('Date')
                    result['分析実行日'] = datetime.now().strftime('%Y-%m-%d')
                    print(f"  株価取得成功: {latest_price}円 ({result['最新株価日付']}) [分析日: {result['分析実行日']}]")
                else:
                    print(f"  株価データなし (期間: {start_date}-{end_date})")
            else:
                print(f"  株価API呼び出し失敗: {res.status_code}")
    except Exception as e:
        print(f"  株価取得エラー: {e}")
    
    # 財務情報を取得してPER/PBRを計算（包括的データ取得）
    if latest_price:
        # 包括的な財務データを取得（ページネーション対応、過去3年分）
        statements = get_comprehensive_financial_data(code, headers, api_url)
        
        if statements:
            # 最適な財務データを選択（年次決算優先、未来日付除外）
            stmt = select_best_financial_data(statements)
            
            if not stmt:
                print("  財務データ選択失敗")
            else:
                # PER計算（実績EPS）
                eps_raw = stmt.get('EarningsPerShare')
                eps_nc_raw = stmt.get('NonConsolidatedEarningsPerShare')
                eps = get_valid_float_value([eps_raw, eps_nc_raw])
                
                # フォールバックEPSチェック（前期年次決算から）
                if not eps or eps == 0:
                    fallback_eps = get_valid_float_value([stmt.get('FallbackEarningsPerShare')])
                    if fallback_eps and fallback_eps > 0:
                        eps = fallback_eps
                        print(f"  前期EPS使用: {eps}円 (期間: {stmt.get('FallbackEPSPeriod', 'N/A')})")
                
                # 年換算EPSチェック（四半期データの場合）
                if not eps or eps == 0:
                    annualized_eps = get_valid_float_value([stmt.get('AnnualizedEarningsPerShare')])
                    if annualized_eps and annualized_eps > 0:
                        eps = annualized_eps
                        print(f"  年換算EPS使用: {eps}円")
                
                if eps and eps > 0:
                    result['PER(最新)'] = round(latest_price / eps, 2)
                    print(f"  EPS: {eps}円 → PER: {result['PER(最新)']}")
                else:
                    print(f"  EPS未取得 (連結: {eps_raw}, 非連結: {eps_nc_raw})")
                
                # PER計算（予想EPS） - 最初に選択されたデータから試行
                forecast_eps_raw = stmt.get('ForecastEarningsPerShare')
                forecast_eps_nc_raw = stmt.get('ForecastNonConsolidatedEarningsPerShare')
                forecast_eps = get_valid_float_value([forecast_eps_raw, forecast_eps_nc_raw])
                
                if forecast_eps and forecast_eps > 0:
                    result['PER(予想)'] = round(latest_price / forecast_eps, 2)
                    print(f"  予想EPS: {forecast_eps}円 → 予想PER: {result['PER(予想)']}")
                else:
                    # 選択されたデータで予想EPSが無い場合、全決算期データから探索
                    print(f"  選択データで予想EPS未取得 (連結: {forecast_eps_raw}, 非連結: {forecast_eps_nc_raw})")
                    print("  全決算期データから予想EPS探索中...")
                    
                    search_forecast_eps, search_stmt = search_forecast_eps_in_statements(statements)
                    if search_forecast_eps and search_forecast_eps > 0:
                        result['PER(予想)'] = round(latest_price / search_forecast_eps, 2)
                    else:
                        print("  予想EPS取得失敗: 全決算期で未開示")
                
                # PBR計算
                bps_raw = stmt.get('BookValuePerShare')
                bps_nc_raw = stmt.get('NonConsolidatedBookValuePerShare')
                bps = get_valid_float_value([bps_raw, bps_nc_raw])
                
                if bps and bps > 0:
                    result['PBR(最新)'] = round(latest_price / bps, 2)
                    print(f"  BPS: {bps}円 → PBR: {result['PBR(最新)']}")
                else:
                    print(f"  BPS未取得 (連結: {bps_raw}, 非連結: {bps_nc_raw})")
                    # 手動でBPS計算を試行
                    equity = get_valid_float_value([
                        stmt.get('Equity'),
                        stmt.get('NonConsolidatedEquity')
                    ])
                    shares = get_valid_float_value([
                        stmt.get('NumberOfIssuedAndOutstandingSharesAtTheEndOfFiscalYearIncludingTreasuryStock'),
                        stmt.get('AverageNumberOfShares')
                    ])
                    treasury = get_valid_float_value([stmt.get('NumberOfTreasuryStockAtTheEndOfFiscalYear')]) or 0
                    
                    if equity and shares:
                        # 純資産を発行済株式数で割ってBPSを計算（自己株式を考慮）
                        effective_shares = shares - treasury
                        if effective_shares > 0:
                            # 単位判定: 千円単位と円単位の両方を試してPBR妥当性で判断
                            calculated_bps_raw = equity / effective_shares
                            
                            # パターン1: 千円単位→円単位に変換
                            bps_from_thousand = calculated_bps_raw * 1000
                            pbr_from_thousand = latest_price / bps_from_thousand if bps_from_thousand > 0 else float('inf')
                            
                            # パターン2: 既に円単位として使用
                            bps_direct = calculated_bps_raw
                            pbr_direct = latest_price / bps_direct if bps_direct > 0 else float('inf')
                            
                            # PBR妥当性チェック（0.05-20.0の範囲で判定）
                            calculated_bps = None
                            if 0.05 <= pbr_from_thousand <= 20.0:
                                calculated_bps = bps_from_thousand
                                print(f"  純資産: {equity}千円→BPS: {calculated_bps:.2f}円 (PBR: {pbr_from_thousand:.2f})")
                            elif 0.05 <= pbr_direct <= 20.0:
                                calculated_bps = bps_direct
                                print(f"  純資産: {equity}円→BPS: {calculated_bps:.2f}円 (PBR: {pbr_direct:.2f})")
                            else:
                                print(f"  BPS計算結果異常: 千円基準PBR={pbr_from_thousand:.2f}, 円基準PBR={pbr_direct:.2f} (範囲外)")
                            
                            if calculated_bps and calculated_bps > 0:
                                result['PBR(最新)'] = round(latest_price / calculated_bps, 2)
                                print(f"  BPS手動計算採用: {calculated_bps:.2f}円 → PBR: {result['PBR(最新)']}")
                        else:
                            print(f"  BPS計算失敗: 有効株式数が無効")
                    else:
                        print(f"  BPS手動計算不可: 純資産={equity}, 株式数={shares}")
        else:
            print(f"  財務データ取得失敗")
    else:
        print(f"  株価未取得のため財務計算スキップ")
    
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