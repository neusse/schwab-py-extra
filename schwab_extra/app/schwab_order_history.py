#!/usr/bin/env python3
"""
Schwab Order History Display
Displays account information, order history, and summaries using schwab-py API wrapper
"""

import schwab
from schwab import auth
import json
from datetime import datetime, timedelta
import pandas as pd
from typing import Dict, List, Optional
import os
from decimal import Decimal


class SchwabOrderDisplay:
    """Main class for handling Schwab order history display"""
    
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
            #self.client = auth.client_from_login_flow(
            self.client = auth.easy_client(
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


class AccountInfoWidget:
    """Widget for displaying account information"""
    
    def __init__(self, client):
        self.client = client
        self.accounts = []
    
    def fetch_accounts(self):
        """Fetch account information"""
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
            
        print("\n" + "="*60)
        print("ACCOUNT INFORMATION")
        print("="*60)
        
        for account in self.accounts:
            account_num = account.get('accountNumber', 'Unknown')
            account_hash = account.get('hashValue', 'Unknown')
            print(f"Account Number: {account_num}")
            print(f"Account Hash: {account_hash}")
            print("-" * 40)


class OrderHistoryWidget:
    """Widget for fetching and displaying order history"""
    
    def __init__(self, client):
        self.client = client
        self.orders = []
        self.account_info = {}
    
    def fetch_orders(self, account_hash: str, account_number: str, days_back: int = 30):
        """Fetch orders for specified account and time period"""
        try:
            # Store account info for display
            self.account_info = {
                'hash': account_hash,
                'number': account_number
            }
            
            # Calculate date range
            end_date = datetime.now()
            start_date = end_date - timedelta(days=days_back)
            
            response = self.client.get_orders_for_account(
                account_hash,
                from_entered_datetime=start_date,
                to_entered_datetime=end_date
            )
            
            if response.status_code == 200:
                self.orders = response.json()
                return True
            else:
                print(f"Failed to fetch orders: {response.status_code}")
                return False
        except Exception as e:
            print(f"Error fetching orders: {e}")
            return False
    
    def display_orders(self):
        """Display order history in formatted table"""
        if not self.orders:
            print("No orders found for the specified period")
            return
            
        print("\n" + "="*140)
        print(f"ORDER HISTORY - Account: {self.account_info.get('number', 'Unknown')}")
        print("="*140)
        
        # Headers with account column and total
        headers = ["Date", "Account", "Symbol", "Side", "Quantity", "Price", "Total", "Status", "Order Type"]
        print(f"{headers[0]:<12} {headers[1]:<12} {headers[2]:<8} {headers[3]:<4} {headers[4]:<8} {headers[5]:<10} {headers[6]:<12} {headers[7]:<10} {headers[8]:<12}")
        print("-" * 140)
        
        for order in self.orders:
            try:
                # Extract order details
                date_str = order.get('enteredTime', '')[:10] if order.get('enteredTime') else 'N/A'
                status = order.get('status', 'N/A')
                order_type = order.get('orderType', 'N/A')
                account_display = self.account_info.get('number', 'Unknown')
                
                # Get instrument details
                legs = order.get('orderLegCollection', [])
                
                for leg in legs:
                    instrument = leg.get('instrument', {})
                    symbol = instrument.get('symbol', 'N/A')
                    quantity = float(leg.get('quantity', 0))
                    instruction = leg.get('instruction', 'N/A')
                    price = order.get('price', 'MARKET')
                    
                    # Calculate total value
                    if isinstance(price, (int, float)) and price != 'MARKET':
                        total = f"${price * quantity:.2f}"
                    elif price != 'MARKET':
                        try:
                            price_float = float(price)
                            total = f"${price_float * quantity:.2f}"
                        except (ValueError, TypeError):
                            total = "N/A"
                    else:
                        total = "MARKET"
                    
                    print(f"{date_str:<12} {account_display:<12} {symbol:<8} {instruction:<4} {quantity:<8.0f} {price:<10} {total:<12} {status:<10} {order_type:<12}")
                    
            except Exception as e:
                print(f"Error parsing order: {e}")
                continue


class OrderSummaryWidget:
    """Widget for calculating and displaying order summaries"""
    
    def __init__(self, orders):
        self.orders = orders
    
    def calculate_summary(self):
        """Calculate summary statistics"""
        if not self.orders:
            return {}
            
        summary = {
            'total_orders': len(self.orders),
            'buy_orders': 0,
            'sell_orders': 0,
            'filled_orders': 0,
            'cancelled_orders': 0,
            'pending_orders': 0,
            'symbols_traded': set(),
            'total_quantity_bought': 0,
            'total_quantity_sold': 0
        }
        
        for order in self.orders:
            try:
                status = order.get('status', '').upper()
                
                # Count by status
                if 'FILLED' in status:
                    summary['filled_orders'] += 1
                elif 'CANCELLED' in status:
                    summary['cancelled_orders'] += 1
                elif 'PENDING' in status or 'WORKING' in status:
                    summary['pending_orders'] += 1
                
                # Process order legs
                legs = order.get('orderLegCollection', [])
                for leg in legs:
                    instrument = leg.get('instrument', {})
                    symbol = instrument.get('symbol', '')
                    quantity = float(leg.get('quantity', 0))
                    instruction = leg.get('instruction', '').upper()
                    
                    if symbol:
                        summary['symbols_traded'].add(symbol)
                    
                    if 'BUY' in instruction:
                        summary['buy_orders'] += 1
                        summary['total_quantity_bought'] += quantity
                    elif 'SELL' in instruction:
                        summary['sell_orders'] += 1
                        summary['total_quantity_sold'] += quantity
                        
            except Exception as e:
                print(f"Error processing order for summary: {e}")
                continue
        
        summary['unique_symbols'] = len(summary['symbols_traded'])
        return summary
    
    def display_summary(self):
        """Display summary statistics"""
        summary = self.calculate_summary()
        
        if not summary:
            print("No data available for summary")
            return
            
        print("\n" + "="*60)
        print("ORDER SUMMARY")
        print("="*60)
        
        print(f"Total Orders: {summary['total_orders']}")
        print(f"Buy Orders: {summary['buy_orders']}")
        print(f"Sell Orders: {summary['sell_orders']}")
        print("")
        print(f"Filled Orders: {summary['filled_orders']}")
        print(f"Cancelled Orders: {summary['cancelled_orders']}")
        print(f"Pending Orders: {summary['pending_orders']}")
        print("")
        print(f"Unique Symbols Traded: {summary['unique_symbols']}")
        print(f"Total Shares Bought: {summary['total_quantity_bought']:.0f}")
        print(f"Total Shares Sold: {summary['total_quantity_sold']:.0f}")
        
        if summary['symbols_traded']:
            print(f"\nSymbols: {', '.join(sorted(summary['symbols_traded']))}")


class SchwabOrderHistoryApp:
    """Main application class that assembles all widgets"""
    
    def __init__(self, app_key: str, app_secret: str, callback_url: str, token_path: str):
        self.schwab_client = SchwabOrderDisplay(app_key, app_secret, callback_url, token_path)
        self.account_widget = None
        self.order_widget = None
        self.summary_widget = None
    
    def initialize(self):
        """Initialize the application"""
        print("Initializing Schwab Order History Display...")
        
        if not self.schwab_client.authenticate():
            return False
            
        self.account_widget = AccountInfoWidget(self.schwab_client.client)
        self.order_widget = OrderHistoryWidget(self.schwab_client.client)
        
        return True
    
    def run(self, days_back: int = 30):
        """Run the complete application"""
        if not self.initialize():
            print("Failed to initialize application")
            return
        
        # Fetch and display accounts
        if self.account_widget.fetch_accounts():
            self.account_widget.display_accounts()
            
            # Process orders for each account
            if self.account_widget.accounts:
                all_orders = []
                
                for account in self.account_widget.accounts:
                    account_hash = account.get('hashValue')
                    account_number = account.get('accountNumber')
                    
                    if account_hash and account_number:
                        print(f"\nFetching orders for account {account_number} (last {days_back} days)...")
                        
                        # Fetch and display orders for this account
                        if self.order_widget.fetch_orders(account_hash, account_number, days_back):
                            self.order_widget.display_orders()
                            all_orders.extend(self.order_widget.orders)
                        else:
                            print(f"Failed to fetch order history for account {account_number}")
                    else:
                        print(f"Missing account information for account")
                
                # Create and display overall summary
                if all_orders:
                    print(f"\n{'='*60}")
                    print("OVERALL SUMMARY (All Accounts)")
                    print("="*60)
                    self.summary_widget = OrderSummaryWidget(all_orders)
                    self.summary_widget.display_summary()
            else:
                print("No accounts found")
        else:
            print("Failed to fetch account information")


def main():
    """Main function to run the application"""
    
    # Configuration - pulled from environment variables
    APP_KEY = os.environ.get('SCHWAB_API_KEY')
    APP_SECRET = os.environ.get('SCHWAB_APP_SECRET') 
    CALLBACK_URL = "https://127.0.0.1:8182/"  # Your registered callback URL
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
    app = SchwabOrderHistoryApp(APP_KEY, APP_SECRET, CALLBACK_URL, token_path)
    
    try:
        # Run for last 30 days (adjust as needed)
        app.run(days_back=365)
    except KeyboardInterrupt:
        print("\nApplication interrupted by user")
    except Exception as e:
        print(f"Application error: {e}")


if __name__ == "__main__":
    main()
