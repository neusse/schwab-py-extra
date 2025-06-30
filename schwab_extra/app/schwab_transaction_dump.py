#!/usr/bin/env python3
"""
Schwab Transaction Dump
Dumps all transactions for all accounts using schwab-py API wrapper
"""

import schwab
from schwab import auth
import json
from datetime import datetime, timedelta
import pandas as pd
from typing import Dict, List, Optional
import os
from decimal import Decimal
import csv


class SchwabTransactionClient:
    """Main class for handling Schwab transaction API access"""
    
    def __init__(self, app_key: str, app_secret: str, callback_url: str, token_path: str):
        """Initialize with Schwab API credentials"""
        self.app_key = app_key
        self.app_secret = app_secret
        self.callback_url = callback_url
        self.token_path = token_path
        self.client = None
        
    def authenticate(self):
        """Authenticate with Schwab API"""
        try:
            # Always try to use existing token first if it exists
            if os.path.exists(self.token_path):
                try:
                    self.client = auth.client_from_token_file(
                        self.token_path, 
                        self.app_key, 
                        self.app_secret
                    )
                    print("✓ Successfully authenticated with existing token")
                    return True
                except Exception as token_error:
                    print(f"Existing token failed: {token_error}")
                    print("Creating new token...")
            
            # Create new token only if existing token doesn't work
            self.client = auth.client_from_login_flow(
                self.app_key,
                self.app_secret, 
                self.callback_url,
                self.token_path
            )
            print("✓ Successfully authenticated with new token")
            return True
        except Exception as e:
            print(f"✗ Authentication failed: {e}")
            return False


class AccountManagerWidget:
    """Widget for managing account information and operations"""
    
    def __init__(self, client):
        self.client = client
        self.accounts = []
    
    def fetch_accounts(self):
        """Fetch all account information"""
        try:
            response = self.client.get_account_numbers()
            if response.status_code == 200:
                self.accounts = response.json()
                return True
            else:
                print(f"Failed to fetch accounts: {response.status_code}")
                return False
        except Exception as e:
            print(f"Error fetching accounts: {e}")
            return False
    
    def display_accounts(self):
        """Display account information"""
        if not self.accounts:
            print("No accounts found")
            return
            
        print("\n" + "="*80)
        print("SCHWAB ACCOUNTS")
        print("="*80)
        
        for i, account in enumerate(self.accounts, 1):
            account_num = account.get('accountNumber', 'Unknown')
            account_hash = account.get('hashValue', 'Unknown')
            print(f"{i}. Account Number: {account_num}")
            print(f"   Account Hash: {account_hash}")
            print("-" * 60)
    
    def get_account_info(self, account_hash: str):
        """Get detailed account information"""
        try:
            response = self.client.get_account(account_hash, fields=['balances', 'positions'])
            if response.status_code == 200:
                return response.json()
            return None
        except Exception as e:
            print(f"Error getting account info: {e}")
            return None


class TransactionFetchWidget:
    """Widget for fetching transactions from Schwab API"""
    
    def __init__(self, client):
        self.client = client
        self.transactions = []
        self.account_info = {}
    
    def fetch_transactions(self, account_hash: str, account_number: str, days_back: int = 365):
        """Fetch transactions for specified account and time period"""
        try:
            # Store account info
            self.account_info = {
                'hash': account_hash,
                'number': account_number
            }
            
            # Calculate date range - Schwab API expects datetime.date objects
            end_date = datetime.now()
            start_date = end_date - timedelta(days=days_back)
            
            # Convert to date objects for API
            start_date_obj = start_date.date()
            end_date_obj = end_date.date()
            
            print(f"   Fetching transactions from {start_date_obj} to {end_date_obj}")
            
            response = self.client.get_transactions(
                account_hash,
                start_date=start_date_obj,
                end_date=end_date_obj
            )
            
            if response.status_code == 200:
                self.transactions = response.json()
                
                # Optional debug: Print structure of first transaction if any exist
                # Uncomment next 4 lines for debugging transaction structure
                # if self.transactions:
                #     print(f"   Debug: Sample transaction keys: {list(self.transactions[0].keys())}")
                #     print(f"   Debug: First transaction sample: {json.dumps(self.transactions[0], indent=2)[:500]}...")
                
                return True
            else:
                print(f"   Failed to fetch transactions: {response.status_code}")
                if response.status_code == 400:
                    print("   Note: This might be due to date format or account access issues")
                elif response.status_code == 401:
                    print("   Note: Authentication issue - token may have expired")
                elif response.status_code == 403:
                    print("   Note: Access forbidden - check account permissions")
                return False
        except Exception as e:
            print(f"   Error fetching transactions: {e}")
            return False
    
    def get_transaction_count(self):
        """Get count of transactions"""
        return len(self.transactions) if self.transactions else 0


class TransactionDisplayWidget:
    """Widget for displaying transactions in formatted output using pandas normalization"""
    
    def __init__(self):
        self.all_transactions = []
        self.normalized_df = None
    
    def add_account_transactions(self, transactions, account_number: str):
        """Add transactions from an account to the display list"""
        for transaction in transactions:
            # Add account info to each transaction for display
            transaction['_account_number'] = account_number
            self.all_transactions.append(transaction)
    
    def normalize_transactions(self):
        """Normalize all transactions using pandas with proper array handling"""
        if not self.all_transactions:
            return None
            
        try:
            # First, we need to flatten the transferItems arrays manually
            flattened_transactions = []
            
            for transaction in self.all_transactions:
                # Create a copy of the transaction
                flat_transaction = transaction.copy()
                
                # Handle transferItems array specifically
                transfer_items = transaction.get('transferItems', [])
                if transfer_items and isinstance(transfer_items, list):
                    # Remove the original transferItems
                    flat_transaction.pop('transferItems', None)
                    
                    # Add each transfer item as separate fields
                    for i, item in enumerate(transfer_items):
                        # Flatten each transfer item with index
                        for key, value in item.items():
                            if isinstance(value, dict):
                                # Flatten nested dictionaries (like instrument)
                                for nested_key, nested_value in value.items():
                                    flat_transaction[f'transferItems_{i}_{key}_{nested_key}'] = nested_value
                            else:
                                flat_transaction[f'transferItems_{i}_{key}'] = value
                
                # Handle any other array fields that might exist
                for key, value in list(flat_transaction.items()):
                    if isinstance(value, list) and value and isinstance(value[0], dict):
                        # Remove the original array field
                        flat_transaction.pop(key, None)
                        # Flatten each item in the array
                        for i, item in enumerate(value):
                            if isinstance(item, dict):
                                for item_key, item_value in item.items():
                                    flat_transaction[f'{key}_{i}_{item_key}'] = item_value
                            else:
                                flat_transaction[f'{key}_{i}'] = item
                
                flattened_transactions.append(flat_transaction)
            
            # Now use pandas to normalize the pre-flattened data
            self.normalized_df = pd.json_normalize(flattened_transactions, sep='_')
            
            # Clean up column names for better readability
            column_mapping = {}
            for col in self.normalized_df.columns:
                # Create more readable column names
                new_col = col.replace('transferItems_', 'transfer_').replace('instrument_', 'instr_')
                column_mapping[col] = new_col
            
            self.normalized_df = self.normalized_df.rename(columns=column_mapping)
            
            print(f"✓ Normalized {len(self.normalized_df)} transactions with {len(self.normalized_df.columns)} columns")
            
            return self.normalized_df
        except Exception as e:
            print(f"Error normalizing transactions: {e}")
            return None
    
    def display_transactions(self, limit: int = None):
        """Display transactions using normalized pandas DataFrame"""
        if not self.all_transactions:
            print("No transactions found")
            return
            
        # Normalize the data
        df = self.normalize_transactions()
        if df is None:
            print("Failed to normalize transaction data")
            return
            
        print("\n" + "="*160)
        print("ALL TRANSACTIONS (Normalized)")
        print("="*160)
        
        # Sort by trade date (newest first)
        if 'tradeDate' in df.columns:
            df = df.sort_values('tradeDate', ascending=False)
        
        # Apply limit if specified
        if limit:
            df_display = df.head(limit)
        else:
            df_display = df
        
        # Select key columns for display (customize based on what's most important)
        display_columns = []
        available_columns = df.columns.tolist()
        
        # Priority columns to show if available
        priority_cols = [
            'tradeDate', '_account_number', 'type', 'description', 'netAmount',
            'transfer_0_instr_symbol', 'transfer_0_amount', 'transfer_0_price',
            'transfer_1_instr_symbol', 'transfer_1_amount', 'transfer_1_price',
            'status', 'settlementDate'
        ]
        
        # Add columns that exist in the data
        for col in priority_cols:
            if col in available_columns:
                display_columns.append(col)
        
        # Display the selected columns
        if display_columns:
            # Format the display nicely
            pd.set_option('display.max_columns', None)
            pd.set_option('display.width', None)
            pd.set_option('display.max_colwidth', 30)
            
            print("\nKey Transaction Details:")
            print(df_display[display_columns].to_string(index=False))
            
            print(f"\nShowing {len(df_display)} of {len(df)} total transactions")
            print(f"Total columns in normalized data: {len(df.columns)}")
            
            # Show column names for reference
            print(f"\nAll available columns:")
            for i, col in enumerate(sorted(df.columns), 1):
                print(f"  {i:2d}. {col}")
                if i % 3 == 0:  # Print 3 columns per line
                    print()
        else:
            print("No suitable columns found for display")
    
    def export_to_csv(self, filename: str):
        """Export normalized transactions to CSV file"""
        if not self.all_transactions:
            print("No transactions to export")
            return False
            
        try:
            # Use the normalized DataFrame
            df = self.normalize_transactions()
            if df is None:
                print("Failed to normalize data for CSV export")
                return False
            
            # Export to CSV
            df.to_csv(filename, index=False)
            
            print(f"✓ Exported {len(df)} transactions with {len(df.columns)} columns to {filename}")
            print(f"  All nested fields have been flattened and included")
            return True
        except Exception as e:
            print(f"Error exporting to CSV: {e}")
            return False
    
    def get_summary_data(self):
        """Get summary data from normalized DataFrame"""
        if not self.normalized_df is None:
            return self.normalized_df
        return self.normalize_transactions()
    
    def show_data_structure(self):
        """Show the structure of the normalized data for analysis"""
        df = self.normalize_transactions()
        if df is None:
            return
            
        print("\n" + "="*80)
        print("NORMALIZED DATA STRUCTURE")
        print("="*80)
        
        print(f"Total Transactions: {len(df)}")
        print(f"Total Columns: {len(df.columns)}")
        
        print(f"\nData Types:")
        print(df.dtypes.value_counts())
        
        print(f"\nColumn Groups:")
        
        # Group columns by prefix
        column_groups = {}
        for col in df.columns:
            prefix = col.split('_')[0]
            if prefix not in column_groups:
                column_groups[prefix] = []
            column_groups[prefix].append(col)
        
        for group, cols in sorted(column_groups.items()):
            print(f"  {group}: {len(cols)} columns")
            if len(cols) <= 5:
                for col in cols:
                    print(f"    - {col}")
            else:
                print(f"    - {cols[0]}, {cols[1]}, ... (+{len(cols)-2} more)")
        
        print(f"\nSample of first few rows:")
        print(df.head(2).to_string())


class TransactionSummaryWidget:
    """Widget for calculating and displaying transaction summaries using normalized data"""
    
    def __init__(self, display_widget):
        self.display_widget = display_widget
        self.df = None
    
    def calculate_summary(self):
        """Calculate comprehensive transaction summary from normalized DataFrame"""
        self.df = self.display_widget.get_summary_data()
        
        if self.df is None or self.df.empty:
            return {}
        
        summary = {
            'total_transactions': len(self.df),
            'transaction_types': {},
            'accounts': set(),
            'symbols_traded': set(),
            'date_range': {'earliest': None, 'latest': None},
            'total_amount': 0,
            'amount_by_type': {}
        }
        
        # Count transaction types
        if 'type' in self.df.columns:
            summary['transaction_types'] = self.df['type'].value_counts().to_dict()
        
        # Track accounts
        if '_account_number' in self.df.columns:
            summary['accounts'] = set(self.df['_account_number'].dropna().unique())
        
        # Track symbols from all transfer item columns
        for col in self.df.columns:
            if 'instr_symbol' in col:
                symbols = self.df[col].dropna().unique()
                for symbol in symbols:
                    if symbol and not str(symbol).startswith('CURRENCY_') and symbol != 'CURRENCY_USD':
                        summary['symbols_traded'].add(symbol)
        
        # Date range
        if 'tradeDate' in self.df.columns:
            dates = self.df['tradeDate'].dropna()
            if not dates.empty:
                summary['date_range']['earliest'] = str(dates.min())
                summary['date_range']['latest'] = str(dates.max())
        
        # Financial summary
        if 'netAmount' in self.df.columns:
            summary['total_amount'] = self.df['netAmount'].sum()
            
            # Amount by transaction type
            if 'type' in self.df.columns:
                summary['amount_by_type'] = self.df.groupby('type')['netAmount'].sum().to_dict()
        
        summary['unique_accounts'] = len(summary['accounts'])
        summary['unique_symbols'] = len(summary['symbols_traded'])
        
        return summary
    
    def display_summary(self):
        """Display comprehensive summary"""
        summary = self.calculate_summary()
        
        if not summary:
            print("No transaction data available for summary")
            return
        
        print("\n" + "="*80)
        print("TRANSACTION SUMMARY (From Normalized Data)")
        print("="*80)
        
        print(f"Total Transactions: {summary['total_transactions']:,}")
        print(f"Accounts Processed: {summary['unique_accounts']}")
        print(f"Unique Symbols: {summary['unique_symbols']}")
        
        if summary['date_range']['earliest'] and summary['date_range']['latest']:
            print(f"Date Range: {summary['date_range']['earliest'][:10]} to {summary['date_range']['latest'][:10]}")
        
        print(f"\nFinancial Summary:")
        print(f"  Total Net Amount: ${summary['total_amount']:,.2f}")
        
        print(f"\nAmount by Transaction Type:")
        for trans_type, amount in sorted(summary['amount_by_type'].items()):
            print(f"  {trans_type}: ${amount:,.2f}")
        
        print(f"\nTransaction Type Counts:")
        for trans_type, count in sorted(summary['transaction_types'].items()):
            print(f"  {trans_type}: {count:,}")
        
        if summary['symbols_traded'] and len(summary['symbols_traded']) <= 20:
            print(f"\nSymbols Traded: {', '.join(sorted(summary['symbols_traded']))}")
        elif summary['symbols_traded']:
            symbols_list = sorted(list(summary['symbols_traded']))
            print(f"\nTop 20 Symbols: {', '.join(symbols_list[:20])}")
            if len(symbols_list) > 20:
                print(f"  ... and {len(symbols_list) - 20} more")
    
    def show_detailed_analysis(self):
        """Show detailed analysis of the normalized data"""
        if self.df is None:
            self.df = self.display_widget.get_summary_data()
        
        if self.df is None or self.df.empty:
            print("No data available for detailed analysis")
            return
        
        print("\n" + "="*80)
        print("DETAILED TRANSACTION ANALYSIS")
        print("="*80)
        
        # Transaction patterns by date
        if 'tradeDate' in self.df.columns:
            self.df['trade_date_only'] = pd.to_datetime(self.df['tradeDate']).dt.date
            daily_counts = self.df.groupby('trade_date_only').size()
            print(f"\nMost Active Trading Days:")
            print(daily_counts.sort_values(ascending=False).head(5))
        
        # Amount distributions
        if 'netAmount' in self.df.columns:
            print(f"\nAmount Statistics:")
            print(f"  Mean: ${self.df['netAmount'].mean():.2f}")
            print(f"  Median: ${self.df['netAmount'].median():.2f}")
            print(f"  Std Dev: ${self.df['netAmount'].std():.2f}")
            print(f"  Min: ${self.df['netAmount'].min():.2f}")
            print(f"  Max: ${self.df['netAmount'].max():.2f}")
        
        # Top symbols by transaction frequency
        symbol_cols = [col for col in self.df.columns if 'instr_symbol' in col]
        if symbol_cols:
            all_symbols = []
            for col in symbol_cols:
                symbols = self.df[col].dropna()
                all_symbols.extend(symbols.tolist())
            
            symbol_series = pd.Series(all_symbols)
            symbol_counts = symbol_series[~symbol_series.str.startswith('CURRENCY_', na=False)].value_counts()
            
            if not symbol_counts.empty:
                print(f"\nMost Frequently Traded Symbols:")
                print(symbol_counts.head(10))


class SchwabTransactionDumpApp:
    """Main application class that orchestrates the transaction dump"""
    
    def __init__(self, app_key: str, app_secret: str, callback_url: str, token_path: str):
        self.client = SchwabTransactionClient(app_key, app_secret, callback_url, token_path)
        self.account_manager = None
        self.transaction_fetcher = None
        self.transaction_display = TransactionDisplayWidget()
        self.summary_widget = None
    
    def initialize(self):
        """Initialize the application"""
        print("Initializing Schwab Transaction Dump...")
        
        if not self.client.authenticate():
            return False
            
        self.account_manager = AccountManagerWidget(self.client.client)
        self.transaction_fetcher = TransactionFetchWidget(self.client.client)
        
        return True
    
    def run(self, days_back: int = 365, export_csv: bool = True, display_limit: int = 100):
        """Run the complete transaction dump"""
        if not self.initialize():
            print("Failed to initialize application")
            return
        
        # Fetch and display accounts
        if not self.account_manager.fetch_accounts():
            print("Failed to fetch account information")
            return
            
        self.account_manager.display_accounts()
        
        if not self.account_manager.accounts:
            print("No accounts found")
            return
        
        print(f"\nFetching transactions for all accounts (last {days_back} days)...")
        total_transactions = 0
        
        # Fetch transactions for each account
        for i, account in enumerate(self.account_manager.accounts, 1):
            account_hash = account.get('hashValue')
            account_number = account.get('accountNumber')
            
            if not account_hash or not account_number:
                print(f"Skipping account {i}: Missing account information")
                continue
            
            print(f"\n[{i}/{len(self.account_manager.accounts)}] Processing account {account_number}...")
            
            if self.transaction_fetcher.fetch_transactions(account_hash, account_number, days_back):
                transaction_count = self.transaction_fetcher.get_transaction_count()
                print(f"   Found {transaction_count:,} transactions")
                
                if transaction_count > 0:
                    self.transaction_display.add_account_transactions(
                        self.transaction_fetcher.transactions, 
                        account_number
                    )
                    total_transactions += transaction_count
            else:
                print(f"   Failed to fetch transactions for account {account_number}")
        
        print(f"\n✓ Total transactions collected: {total_transactions:,}")
        
        if total_transactions > 0:
            # Show data structure for analysis
            print(f"\n" + "="*60)
            print("DATA STRUCTURE ANALYSIS")
            print("="*60)
            self.transaction_display.show_data_structure()
            
            # Display transactions (limited for readability)
            print(f"\nDisplaying most recent {min(display_limit, total_transactions)} transactions:")
            self.transaction_display.display_transactions(limit=display_limit)
            
            # Generate summary using normalized data
            self.summary_widget = TransactionSummaryWidget(self.transaction_display)
            self.summary_widget.display_summary()
            
            # Show detailed analysis
            self.summary_widget.show_detailed_analysis()
            
            # Export to CSV if requested
            if export_csv:
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                csv_filename = f"schwab_transactions_normalized_{timestamp}.csv"
                print(f"\nExporting all normalized transactions to CSV...")
                self.transaction_display.export_to_csv(csv_filename)
        else:
            print("No transactions found for the specified time period")


def main():
    """Main function to run the transaction dump"""
    
    # Configuration - pulled from environment variables
    APP_KEY = os.environ.get('SCHWAB_API_KEY')
    APP_SECRET = os.environ.get('SCHWAB_APP_SECRET') 
    CALLBACK_URL = "https://127.0.0.1:8182/"
    token_path = os.environ.get("SCHWAB_TOKEN_PATH")
    
    # Check if credentials are set
    if not APP_KEY or not APP_SECRET or not token_path:
        print("Please set the following environment variables:")
        print("- SCHWAB_API_KEY: Your Schwab API App Key")
        print("- SCHWAB_APP_SECRET: Your Schwab API App Secret")
        print("- SCHWAB_TOKEN_PATH: Path where token file should be stored")
        print("\nTo get API credentials:")
        print("1. Register for a Schwab Developer account at https://developer.schwab.com/")
        print("2. Create a new app and get your App Key and App Secret")
        print("3. Set your callback URL to https://127.0.0.1:8182/")
        return
    
    # Create and run the application
    app = SchwabTransactionDumpApp(APP_KEY, APP_SECRET, CALLBACK_URL, token_path)
    
    try:
        # Run for last 365 days (adjust as needed)
        # Set export_csv=True to export to CSV, display_limit controls console output
        app.run(days_back=365, export_csv=True, display_limit=50)
        
    except KeyboardInterrupt:
        print("\nApplication interrupted by user")
    except Exception as e:
        print(f"Application error: {e}")


if __name__ == "__main__":
    main()
