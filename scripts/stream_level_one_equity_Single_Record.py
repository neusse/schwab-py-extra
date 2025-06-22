import asyncio
import pprint
import my_schwab_lib as mylib
from schwab.streaming import StreamClient
import sqlite3
import json
import pandas as pd

STREAMING_DB = "streaming_data.db"


class MyStreamConsumer:
    """
    We use a class to enforce good code organization practices
    """

    def __init__(
        self,
        queue_size=0,
    ):
        """
        We're storing the configuration variables within the class for easy
        access later in the code!
        """
        self.account_id = None
        self.account_hash = None

        self.schwab_client = None
        self.stream_client = None

        self.symbols = [
            "NVDA",
            "QQQ",
            "MSFT",
            "VOO",
            "VIG",
            "FTSM",
            "QYLD",
            "JSCP",
            "VEU",
            "JEPQ",
            "SPLG",
            "PVAL",
            "RDVI",
            "SPYV",
            "QQQY",
            "NVDY",
            "AMZN",
            "AMZY",
            "NFLX",
            "NFLY",
            "TQQQ,"
        ]

        # Create a queue so we can queue up work gathered from the client
        self.queue = asyncio.Queue(queue_size)

    def initialize(self):
        """
        Create the clients and log in. Token should be previously generated using client_from_manual_flow()

        TODO: update to easy_client() when client_from_login_flow() works,
        or when easy_client() can redirect to client_from_manual_flow()
        """
        # this is a normal client that is returned from
        # client = client_from_token_file( api_key=api_key, app_secret=app_secret, token_path=token_path)
        self.schwab_client = mylib.authenticate()

        account_info = self.schwab_client.get_account_numbers().json()

        self.account_id = int(account_info[0]["accountNumber"])
        self.account_hash = account_info[0]["hashValue"]

        self.stream_client = StreamClient(
            self.schwab_client, account_id=self.account_id
        )

        # The streaming client wants you to add a handler for every service type
        self.stream_client.add_level_one_equity_handler(self.handle_level_one_equity)

    async def stream(self):
        await self.stream_client.login()  # Log into the streaming service

        # TODO: QOS is currently not working as the command formatting has changed. Update & re-enable after docs are released
        # await self.stream_client.quality_of_service(StreamClient.QOSLevel.EXPRESS)

        await self.stream_client.level_one_equity_subs(self.symbols)

        # Kick off our handle_queue function as an independent coroutine
        asyncio.ensure_future(self.handle_queue())

        # Continuously handle inbound messages
        while True:
            await self.stream_client.handle_message()

    async def handle_level_one_equity(self, msg):
        """
        This is where we take msgs from the streaming client and put them on a
        queue for later consumption. We use a queue to prevent us from wasting
        resources processing old data, and falling behind.
        """
        # if the queue is full, make room
        if self.queue.full():  # This won't happen if the queue doesn't have a max size
            print(
                "Handler queue is full. Awaiting to make room... Some messages might be dropped"
            )
            await self.queue.get()
        await self.queue.put(msg)

    async def handle_queue(self):
        """
        Here we pull messages off the queue and process them.
        """
        while True:
            msg = await self.queue.get()
            pprint.pprint(msg)
            write_to_db(msg)


# check for SQLite database
def check_db():
    # Connect to SQLite database (or create it if it doesn't exist)
    conn = sqlite3.connect(STREAMING_DB)
    cursor = conn.cursor()

    # Create table if it doesn't exist
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS streaming_data (
            command TEXT,
            service TEXT,
            timestamp INTEGER,
            key TEXT,
            ASK_ID TEXT,
            ASK_MIC_ID TEXT,
            ASK_PRICE REAL,
            ASK_SIZE INTEGER,
            ASK_TIME_MILLIS INTEGER,
            BID_ID TEXT,
            BID_MIC_ID TEXT,
            BID_PRICE REAL,
            BID_SIZE INTEGER,
            BID_TIME_MILLIS INTEGER,
            CLOSE_PRICE REAL,
            DESCRIPTION TEXT,
            DIVIDEND_AMOUNT REAL,
            DIVIDEND_DATE TEXT,
            DIVIDEND_YIELD REAL,
            EXCHANGE_ID TEXT,
            EXCHANGE_NAME TEXT,
            HARD_TO_BORROW INTEGER,
            HIGH_PRICE REAL,
            HIGH_PRICE_52_WEEK REAL,
            HTB_QUALITY INTEGER,
            HTB_RATE REAL,
            IS_SHORTABLE INTEGER,
            LAST_ID TEXT,
            LAST_MIC_ID TEXT,
            LAST_PRICE REAL,
            LAST_SIZE INTEGER,
            LOW_PRICE REAL,
            LOW_PRICE_52_WEEK REAL,
            MARGINABLE INTEGER,
            MARK REAL,
            MARK_CHANGE REAL,
            MARK_CHANGE_PERCENT REAL,
            NAV INTEGER,
            NET_CHANGE REAL,
            NET_CHANGE_PERCENT REAL,
            OPEN_PRICE REAL,
            PE_RATIO REAL,
            POST_MARKET_NET_CHANGE REAL,
            POST_MARKET_NET_CHANGE_PERCENT REAL,
            QUOTE_TIME_MILLIS INTEGER,
            REGULAR_MARKET_CHANGE_PERCENT REAL,
            REGULAR_MARKET_LAST_PRICE REAL,
            REGULAR_MARKET_LAST_SIZE INTEGER,
            REGULAR_MARKET_NET_CHANGE REAL,
            REGULAR_MARKET_QUOTE INTEGER,
            REGULAR_MARKET_TRADE INTEGER,
            REGULAR_MARKET_TRADE_MILLIS INTEGER,
            SECURITY_STATUS TEXT,
            TOTAL_VOLUME INTEGER,
            TRADE_TIME_MILLIS INTEGER,
            assetMainType TEXT,
            assetSubType TEXT,
            cusip TEXT,
            delayed INTEGER
            SQLtimestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """
    )
    conn.commit()
    conn.close()


def write_to_db(stream_data):
    # Connect to SQLite database (or create it if it doesn't exist)
    conn = sqlite3.connect(STREAMING_DB)
    cursor = conn.cursor()

    # Parse JSON data
    data = json.loads(json.dumps(stream_data))

    for content in data["content"]:
        # First, fetch existing record
        cursor.execute(
            "SELECT * FROM streaming_data WHERE key = ?", (content.get("key"),)
        )
        existing_record = cursor.fetchone()

        # Prepare updated values
        updated_values = {
            "command": data.get("command"),
            "service": data.get("service"),
            "timestamp": data.get("timestamp"),
            "key": content.get("key"),
            "ASK_ID": content.get("ASK_ID"),
            "ASK_MIC_ID": content.get("ASK_MIC_ID"),
            "ASK_PRICE": content.get("ASK_PRICE"),
            "ASK_SIZE": content.get("ASK_SIZE"),
            "ASK_TIME_MILLIS": content.get("ASK_TIME_MILLIS"),
            "BID_ID": content.get("BID_ID"),
            "BID_MIC_ID": content.get("BID_MIC_ID"),
            "BID_PRICE": content.get("BID_PRICE"),
            "BID_SIZE": content.get("BID_SIZE"),
            "BID_TIME_MILLIS": content.get("BID_TIME_MILLIS"),
            "CLOSE_PRICE": content.get("CLOSE_PRICE"),
            "DESCRIPTION": content.get("DESCRIPTION"),
            "DIVIDEND_AMOUNT": content.get("DIVIDEND_AMOUNT"),
            "DIVIDEND_DATE": content.get("DIVIDEND_DATE"),
            "DIVIDEND_YIELD": content.get("DIVIDEND_YIELD"),
            "EXCHANGE_ID": content.get("EXCHANGE_ID"),
            "EXCHANGE_NAME": content.get("EXCHANGE_NAME"),
            "HARD_TO_BORROW": content.get("HARD_TO_BORROW"),
            "HIGH_PRICE": content.get("HIGH_PRICE"),
            "HIGH_PRICE_52_WEEK": content.get("HIGH_PRICE_52_WEEK"),
            "HTB_QUALITY": content.get("HTB_QUALITY"),
            "HTB_RATE": content.get("HTB_RATE"),
            "IS_SHORTABLE": content.get("IS_SHORTABLE"),
            "LAST_ID": content.get("LAST_ID"),
            "LAST_MIC_ID": content.get("LAST_MIC_ID"),
            "LAST_PRICE": content.get("LAST_PRICE"),
            "LAST_SIZE": content.get("LAST_SIZE"),
            "LOW_PRICE": content.get("LOW_PRICE"),
            "LOW_PRICE_52_WEEK": content.get("LOW_PRICE_52_WEEK"),
            "MARGINABLE": content.get("MARGINABLE"),
            "MARK": content.get("MARK"),
            "MARK_CHANGE": content.get("MARK_CHANGE"),
            "MARK_CHANGE_PERCENT": content.get("MARK_CHANGE_PERCENT"),
            "NAV": content.get("NAV"),
            "NET_CHANGE": content.get("NET_CHANGE"),
            "NET_CHANGE_PERCENT": content.get("NET_CHANGE_PERCENT"),
            "OPEN_PRICE": content.get("OPEN_PRICE"),
            "PE_RATIO": content.get("PE_RATIO"),
            "POST_MARKET_NET_CHANGE": content.get("POST_MARKET_NET_CHANGE"),
            "POST_MARKET_NET_CHANGE_PERCENT": content.get(
                "POST_MARKET_NET_CHANGE_PERCENT"
            ),
            "QUOTE_TIME_MILLIS": content.get("QUOTE_TIME_MILLIS"),
            "REGULAR_MARKET_CHANGE_PERCENT": content.get(
                "REGULAR_MARKET_CHANGE_PERCENT"
            ),
            "REGULAR_MARKET_LAST_PRICE": content.get("REGULAR_MARKET_LAST_PRICE"),
            "REGULAR_MARKET_LAST_SIZE": content.get("REGULAR_MARKET_LAST_SIZE"),
            "REGULAR_MARKET_NET_CHANGE": content.get("REGULAR_MARKET_NET_CHANGE"),
            "REGULAR_MARKET_QUOTE": content.get("REGULAR_MARKET_QUOTE"),
            "REGULAR_MARKET_TRADE": content.get("REGULAR_MARKET_TRADE"),
            "REGULAR_MARKET_TRADE_MILLIS": content.get("REGULAR_MARKET_TRADE_MILLIS"),
            "SECURITY_STATUS": content.get("SECURITY_STATUS"),
            "TOTAL_VOLUME": content.get("TOTAL_VOLUME"),
            "TRADE_TIME_MILLIS": content.get("TRADE_TIME_MILLIS"),
            "assetMainType": content.get("assetMainType"),
            "assetSubType": content.get("assetSubType"),
            "cusip": content.get("cusip"),
            "delayed": content.get("delayed"),
        }

        # Update only non-null fields
        if existing_record:
            for i, key in enumerate(updated_values.keys()):
                if updated_values[key] is None:
                    updated_values[key] = existing_record[i]

        # Insert or replace the record
        cursor.execute(
            """
            INSERT OR REPLACE INTO streaming_data (
                command, service, timestamp, key, ASK_ID, ASK_MIC_ID, ASK_PRICE, ASK_SIZE,
                ASK_TIME_MILLIS, BID_ID, BID_MIC_ID, BID_PRICE, BID_SIZE, BID_TIME_MILLIS,
                CLOSE_PRICE, DESCRIPTION, DIVIDEND_AMOUNT, DIVIDEND_DATE, DIVIDEND_YIELD,
                EXCHANGE_ID, EXCHANGE_NAME, HARD_TO_BORROW, HIGH_PRICE, HIGH_PRICE_52_WEEK,
                HTB_QUALITY, HTB_RATE, IS_SHORTABLE, LAST_ID, LAST_MIC_ID, LAST_PRICE,
                LAST_SIZE, LOW_PRICE, LOW_PRICE_52_WEEK, MARGINABLE, MARK, MARK_CHANGE,
                MARK_CHANGE_PERCENT, NAV, NET_CHANGE, NET_CHANGE_PERCENT, OPEN_PRICE,
                PE_RATIO, POST_MARKET_NET_CHANGE, POST_MARKET_NET_CHANGE_PERCENT, QUOTE_TIME_MILLIS,
                REGULAR_MARKET_CHANGE_PERCENT, REGULAR_MARKET_LAST_PRICE, REGULAR_MARKET_LAST_SIZE,
                REGULAR_MARKET_NET_CHANGE, REGULAR_MARKET_QUOTE, REGULAR_MARKET_TRADE, REGULAR_MARKET_TRADE_MILLIS,
                SECURITY_STATUS, TOTAL_VOLUME, TRADE_TIME_MILLIS, assetMainType, assetSubType,
                cusip, delayed
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            tuple(updated_values.values()),
        )

    # Commit changes and close connection
    conn.commit()
    conn.close()


async def main():
    """
    Create and instantiate the consumer, and start the stream
    """

    check_db()  # make sure the database exists.

    consumer = MyStreamConsumer(
        # api_key=API_KEY, client_secret=CLIENT_SECRET, callback_url=CALLBACK_URL
    )

    consumer.initialize()
    await consumer.stream()


if __name__ == "__main__":
    asyncio.run(main())


# This SQL retrieves the most recent streaming quote for all streamed tickers.


class streaming_quotes:
    def __init__(self, sqlite_db=STREAMING_DB):
        """
        We're storing the configuration variables within the class for easy
        access later in the code!
        """
        self.db = sqlite_db

    def get_all_current_single_quote(self, ticker_name):
        # Connect to SQLite database (or create it if it doesn't exist)
        conn = sqlite3.connect(self.db)
        cursor = conn.cursor()

        # Define the query with the specific ticker name
        query = """
        SELECT 
            sd.command,
            sd.service,
            datetime(sd.timestamp / 1000, 'unixepoch', '-7 hours') AS timestamp,
            sd.key,
            sd.CLOSE_PRICE,
            sd.DESCRIPTION,
            sd.EXCHANGE_ID,
            sd.EXCHANGE_NAME,
            sd.HIGH_PRICE,
            sd.HIGH_PRICE_52_WEEK,
            sd.LAST_PRICE,
            sd.LOW_PRICE,
            sd.LOW_PRICE_52_WEEK,
            sd.OPEN_PRICE,
            datetime(sd.QUOTE_TIME_MILLIS / 1000, 'unixepoch', '-7 hours') AS QUOTE_TIME,
            sd.REGULAR_MARKET_LAST_PRICE,
            sd.REGULAR_MARKET_QUOTE,
            sd.TOTAL_VOLUME,
            datetime(sd.TRADE_TIME_MILLIS / 1000, 'unixepoch', '-7 hours') AS TRADE_TIME,
            sd.assetMainType,
            sd.assetSubType,
            sd.cusip,
            sd.delayed
        FROM streaming_data sd
        INNER JOIN (
            SELECT 
                key, 
                MAX(timestamp) AS max_timestamp
            FROM streaming_data
            WHERE key = ?
            GROUP BY key
        ) AS grouped_sd
        ON sd.key = grouped_sd.key AND sd.timestamp = grouped_sd.max_timestamp;
        """

        # Execute the query
        cursor.execute(query, (ticker_name,))
        result = cursor.fetchone()

        # Get column names
        column_names = [description[0] for description in cursor.description]

        # Convert the result to a dictionary
        if result:
            data = dict(zip(column_names, result))
        else:
            data = None

        # Close the connection
        conn.close()

        return data

    def get_all_current_streaming_quotes(self):
        # Connect to SQLite database (or create it if it doesn't exist)
        conn = sqlite3.connect(self.db)

        # Define the query with the specific ticker name
        query = f"""
        SELECT 
            sd.command,
            sd.service,
            datetime(sd.timestamp / 1000, 'unixepoch', '-7 hours') AS timestamp,
            sd.key,
            sd.CLOSE_PRICE,
            sd.DESCRIPTION,
            sd.EXCHANGE_ID,
            sd.EXCHANGE_NAME,
            sd.HIGH_PRICE,
            sd.HIGH_PRICE_52_WEEK,
            sd.LAST_PRICE,
            sd.LOW_PRICE,
            sd.LOW_PRICE_52_WEEK,
            sd.OPEN_PRICE,
            datetime(sd.QUOTE_TIME_MILLIS / 1000, 'unixepoch', '-7 hours') AS QUOTE_TIME,
            sd.REGULAR_MARKET_LAST_PRICE,
            sd.REGULAR_MARKET_QUOTE,
            sd.TOTAL_VOLUME,
            datetime(sd.TRADE_TIME_MILLIS / 1000, 'unixepoch', '-7 hours') AS TRADE_TIME,
            sd.assetMainType,
            sd.assetSubType,
            sd.cusip,
            sd.delayed
        FROM streaming_data sd
        INNER JOIN (
        SELECT 
            key, 
            MAX(timestamp) AS max_timestamp
        FROM streaming_data
        GROUP BY key
            ) AS grouped_sd
            ON sd.key = grouped_sd.key AND sd.timestamp = grouped_sd.max_timestamp;
        """

        # Execute the query and load the results into a DataFrame
        df = pd.read_sql_query(query, conn)

        # Close the connection
        conn.close()

        return df


        #      "BID_PRICE": content.get("BID_PRICE"),
        #     "BID_SIZE": content.get("BID_SIZE"),
        #    "ASK_PRICE": content.get("ASK_PRICE"),
        #     "ASK_SIZE": content.get("ASK_SIZE"),
        #     "DIVIDEND_AMOUNT": content.get("DIVIDEND_AMOUNT"),
        #     "DIVIDEND_YIELD": content.get("DIVIDEND_YIELD"),
        #     "PE_RATIO": content.get("PE_RATIO"),
        #       "LOW_PRICE_52_WEEK": content.get("LOW_PRICE_52_WEEK"),


    def get_all_current_streaming_quotes_short_list(self):
            # Connect to SQLite database (or create it if it doesn't exist)
            conn = sqlite3.connect(self.db)

            # Define the query with the specific ticker name
            query_old = f"""
            SELECT 
                sd.DESCRIPTION,
                sd.key,
                sd.REGULAR_MARKET_LAST_PRICE as LastPrice,
                sd.BID_PRICE,
                sd.BID_SIZE,
                sd.ASK_PRICE,
                sd.ASK_SIZE,
                sd.TOTAL_VOLUME as Volume,
                sd.NET_CHANGE_PERCENT as ChgPerc,
                sd.PE_RATIO as PE,
                sd.CLOSE_PRICE,
                sd.HIGH_PRICE_52_WEEK as High52Wk,
                sd.LOW_PRICE_52_WEEK as Low52Wk,
                sd.delayed
            FROM streaming_data sd
            INNER JOIN (
            SELECT 
                key, 
                MAX(timestamp) AS max_timestamp
            FROM streaming_data
            GROUP BY key
                ) AS grouped_sd
                ON sd.key = grouped_sd.key AND sd.timestamp = grouped_sd.max_timestamp
            ORDER BY sd.key ASC;
            """

            query = """
            SELECT 
            sd1.key,
            (SELECT DESCRIPTION FROM streaming_data sd2 
            WHERE sd2.key = sd1.key AND sd2.DESCRIPTION IS NOT NULL 
            ORDER BY sd2.timestamp DESC LIMIT 1) as DESCRIPTION,
            
            (SELECT REGULAR_MARKET_LAST_PRICE FROM streaming_data sd2 
            WHERE sd2.key = sd1.key AND sd2.REGULAR_MARKET_LAST_PRICE IS NOT NULL 
            ORDER BY sd2.timestamp DESC LIMIT 1) as LastPrice,
            
            (SELECT BID_PRICE FROM streaming_data sd2 
            WHERE sd2.key = sd1.key AND sd2.BID_PRICE IS NOT NULL 
            ORDER BY sd2.timestamp DESC LIMIT 1) as BID_PRICE,
            
            (SELECT BID_SIZE FROM streaming_data sd2 
            WHERE sd2.key = sd1.key AND sd2.BID_SIZE IS NOT NULL 
            ORDER BY sd2.timestamp DESC LIMIT 1) as BID_SIZE,
            
            (SELECT ASK_PRICE FROM streaming_data sd2 
            WHERE sd2.key = sd1.key AND sd2.ASK_PRICE IS NOT NULL 
            ORDER BY sd2.timestamp DESC LIMIT 1) as ASK_PRICE,
            
            (SELECT ASK_SIZE FROM streaming_data sd2 
            WHERE sd2.key = sd1.key AND sd2.ASK_SIZE IS NOT NULL 
            ORDER BY sd2.timestamp DESC LIMIT 1) as ASK_SIZE,
            
            (SELECT TOTAL_VOLUME FROM streaming_data sd2 
            WHERE sd2.key = sd1.key AND sd2.TOTAL_VOLUME IS NOT NULL 
            ORDER BY sd2.timestamp DESC LIMIT 1) as Volume,
            
            (SELECT NET_CHANGE_PERCENT FROM streaming_data sd2 
            WHERE sd2.key = sd1.key AND sd2.NET_CHANGE_PERCENT IS NOT NULL 
            ORDER BY sd2.timestamp DESC LIMIT 1) as ChgPerc,
            
            (SELECT PE_RATIO FROM streaming_data sd2 
            WHERE sd2.key = sd1.key AND sd2.PE_RATIO IS NOT NULL 
            ORDER BY sd2.timestamp DESC LIMIT 1) as PE,
            
            (SELECT CLOSE_PRICE FROM streaming_data sd2 
            WHERE sd2.key = sd1.key AND sd2.CLOSE_PRICE IS NOT NULL 
            ORDER BY sd2.timestamp DESC LIMIT 1) as CLOSE_PRICE,
            
            (SELECT HIGH_PRICE_52_WEEK FROM streaming_data sd2 
            WHERE sd2.key = sd1.key AND sd2.HIGH_PRICE_52_WEEK IS NOT NULL 
            ORDER BY sd2.timestamp DESC LIMIT 1) as High52Wk,
            
            (SELECT LOW_PRICE_52_WEEK FROM streaming_data sd2 
            WHERE sd2.key = sd1.key AND sd2.LOW_PRICE_52_WEEK IS NOT NULL 
            ORDER BY sd2.timestamp DESC LIMIT 1) as Low52Wk,
            
            (SELECT delayed FROM streaming_data sd2 
            WHERE sd2.key = sd1.key AND sd2.delayed IS NOT NULL 
            ORDER BY sd2.timestamp DESC LIMIT 1) as delayed

            FROM (SELECT DISTINCT key FROM streaming_data) sd1
            ORDER BY sd1.key ASC;

            """



            # Execute the query and load the results into a DataFrame
            df = pd.read_sql_query(query, conn)

            # Close the connection
            conn.close()

            return df



# Example usage
# ticker_name = "AAPL"  # Replace with the ticker name you want to query
# df = get_all_current_stream_quotes(ticker_name)
# print(df)
