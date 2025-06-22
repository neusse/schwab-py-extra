import asyncio
import pprint
import my_schwab_lib as mylib
from schwab.streaming import StreamClient
import sqlite3
import json


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
        """
        self.symbols = [
            "NVDA",
            "QQQ",
            "MSFT",
            "VOO",
            "VIG",
            "FTSM",
            "GOVT",
            "BND",
            "QYLD",
            "PPA",
            "JSCP",
            "CGIE",
            "CGGR",
            "ICOW",
            "VEU",
            "STXE",
            "JEPQ",
            "SPLG",
            "BOND",
            "BITB",
            "CALF",
            "COWG",
            "COWZ",
            "PVAL",
            "RDVI",
            "SPSM",
            "SPYV",
            "TOUS",
        ]
        """
        self.symbols = [
            "NVDA",
            "QQQ",
            "MSFT",
            "VOO",
            "IVV",
            "VIS",
            "QQQM",
            "AMZN",
            "QYLD",
            "AAPL",
            "VDE",
            "FVD",
            "AUGM",
            "JULM",
            "SEPM",
            "SNSXX",
        ]
        # Create a queue so we can queue up work gathered from the client
        self.queue = asyncio.Queue(queue_size)

    def initialize(self):
        """
        Create the clients and log in. Token should be previously generated using client_from_manual_flow()

        TODO: update to easy_client() when client_from_login_flow() works,
        or when easy_client() can redirect to client_from_manual_flow()
        """
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
            #write_to_db(msg)
            write_to_db_unique_records(msg)


# check for SQLite database
def check_db():
    # Connect to SQLite database (or create it if it doesn't exist)
    conn = sqlite3.connect("streaming_data.db")
    cursor = conn.cursor()

# do this to change over to using one record that unique firlds are updated rather than recording the stream 
#ALTER TABLE streaming_data ADD CONSTRAINT unique_key UNIQUE(key);


    # Create table if it doesn't exist
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS streaming_data (
            command TEXT,
            service TEXT,
            timestamp,
            key TEXT PRIMARY KEY,
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
        )
    """
    )

def write_to_db_unique_records(stream_data):
    # Connect to SQLite database (or create it if it doesn't exist)
    conn = sqlite3.connect("streaming_data.db")
    cursor = conn.cursor()

    # Parse JSON data
    data = json.loads(json.dumps(stream_data))

    for content in data["content"]:
        # Insert data into the table
        cursor.execute("""
            INSERT INTO streaming_data (
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
            ON CONFLICT(key) DO UPDATE SET
                command = COALESCE(excluded.command, streaming_data.command),
                service = COALESCE(excluded.service, streaming_data.service),
                timestamp = excluded.timestamp,
                ASK_ID = COALESCE(excluded.ASK_ID, streaming_data.ASK_ID),
                ASK_MIC_ID = COALESCE(excluded.ASK_MIC_ID, streaming_data.ASK_MIC_ID),
                ASK_PRICE = COALESCE(excluded.ASK_PRICE, streaming_data.ASK_PRICE),
                ASK_SIZE = COALESCE(excluded.ASK_SIZE, streaming_data.ASK_SIZE),
                ASK_TIME_MILLIS = COALESCE(excluded.ASK_TIME_MILLIS, streaming_data.ASK_TIME_MILLIS),
                BID_ID = COALESCE(excluded.BID_ID, streaming_data.BID_ID),
                BID_MIC_ID = COALESCE(excluded.BID_MIC_ID, streaming_data.BID_MIC_ID),
                BID_PRICE = COALESCE(excluded.BID_PRICE, streaming_data.BID_PRICE),
                BID_SIZE = COALESCE(excluded.BID_SIZE, streaming_data.BID_SIZE),
                BID_TIME_MILLIS = COALESCE(excluded.BID_TIME_MILLIS, streaming_data.BID_TIME_MILLIS),
                CLOSE_PRICE = COALESCE(excluded.CLOSE_PRICE, streaming_data.CLOSE_PRICE),
                DESCRIPTION = COALESCE(excluded.DESCRIPTION, streaming_data.DESCRIPTION),
                DIVIDEND_AMOUNT = COALESCE(excluded.DIVIDEND_AMOUNT, streaming_data.DIVIDEND_AMOUNT),
                DIVIDEND_DATE = COALESCE(excluded.DIVIDEND_DATE, streaming_data.DIVIDEND_DATE),
                DIVIDEND_YIELD = COALESCE(excluded.DIVIDEND_YIELD, streaming_data.DIVIDEND_YIELD),
                EXCHANGE_ID = COALESCE(excluded.EXCHANGE_ID, streaming_data.EXCHANGE_ID),
                EXCHANGE_NAME = COALESCE(excluded.EXCHANGE_NAME, streaming_data.EXCHANGE_NAME),
                HARD_TO_BORROW = COALESCE(excluded.HARD_TO_BORROW, streaming_data.HARD_TO_BORROW),
                HIGH_PRICE = COALESCE(excluded.HIGH_PRICE, streaming_data.HIGH_PRICE),
                HIGH_PRICE_52_WEEK = COALESCE(excluded.HIGH_PRICE_52_WEEK, streaming_data.HIGH_PRICE_52_WEEK),
                HTB_QUALITY = COALESCE(excluded.HTB_QUALITY, streaming_data.HTB_QUALITY),
                HTB_RATE = COALESCE(excluded.HTB_RATE, streaming_data.HTB_RATE),
                IS_SHORTABLE = COALESCE(excluded.IS_SHORTABLE, streaming_data.IS_SHORTABLE),
                LAST_ID = COALESCE(excluded.LAST_ID, streaming_data.LAST_ID),
                LAST_MIC_ID = COALESCE(excluded.LAST_MIC_ID, streaming_data.LAST_MIC_ID),
                LAST_PRICE = COALESCE(excluded.LAST_PRICE, streaming_data.LAST_PRICE),
                LAST_SIZE = COALESCE(excluded.LAST_SIZE, streaming_data.LAST_SIZE),
                LOW_PRICE = COALESCE(excluded.LOW_PRICE, streaming_data.LOW_PRICE),
                LOW_PRICE_52_WEEK = COALESCE(excluded.LOW_PRICE_52_WEEK, streaming_data.LOW_PRICE_52_WEEK),
                MARGINABLE = COALESCE(excluded.MARGINABLE, streaming_data.MARGINABLE),
                MARK = COALESCE(excluded.MARK, streaming_data.MARK),
                MARK_CHANGE = COALESCE(excluded.MARK_CHANGE, streaming_data.MARK_CHANGE),
                MARK_CHANGE_PERCENT = COALESCE(excluded.MARK_CHANGE_PERCENT, streaming_data.MARK_CHANGE_PERCENT),
                NAV = COALESCE(excluded.NAV, streaming_data.NAV),
                NET_CHANGE = COALESCE(excluded.NET_CHANGE, streaming_data.NET_CHANGE),
                NET_CHANGE_PERCENT = COALESCE(excluded.NET_CHANGE_PERCENT, streaming_data.NET_CHANGE_PERCENT),
                OPEN_PRICE = COALESCE(excluded.OPEN_PRICE, streaming_data.OPEN_PRICE),
                PE_RATIO = COALESCE(excluded.PE_RATIO, streaming_data.PE_RATIO),
                POST_MARKET_NET_CHANGE = COALESCE(excluded.POST_MARKET_NET_CHANGE, streaming_data.POST_MARKET_NET_CHANGE),
                POST_MARKET_NET_CHANGE_PERCENT = COALESCE(excluded.POST_MARKET_NET_CHANGE_PERCENT, streaming_data.POST_MARKET_NET_CHANGE_PERCENT),
                QUOTE_TIME_MILLIS = COALESCE(excluded.QUOTE_TIME_MILLIS, streaming_data.QUOTE_TIME_MILLIS),
                REGULAR_MARKET_CHANGE_PERCENT = COALESCE(excluded.REGULAR_MARKET_CHANGE_PERCENT, streaming_data.REGULAR_MARKET_CHANGE_PERCENT),
                REGULAR_MARKET_LAST_PRICE = COALESCE(excluded.REGULAR_MARKET_LAST_PRICE, streaming_data.REGULAR_MARKET_LAST_PRICE),
                REGULAR_MARKET_LAST_SIZE = COALESCE(excluded.REGULAR_MARKET_LAST_SIZE, streaming_data.REGULAR_MARKET_LAST_SIZE),
                REGULAR_MARKET_NET_CHANGE = COALESCE(excluded.REGULAR_MARKET_NET_CHANGE, streaming_data.REGULAR_MARKET_NET_CHANGE),
                REGULAR_MARKET_QUOTE = COALESCE(excluded.REGULAR_MARKET_QUOTE, streaming_data.REGULAR_MARKET_QUOTE),
                REGULAR_MARKET_TRADE = COALESCE(excluded.REGULAR_MARKET_TRADE, streaming_data.REGULAR_MARKET_TRADE),
                REGULAR_MARKET_TRADE_MILLIS = COALESCE(excluded.REGULAR_MARKET_TRADE_MILLIS, streaming_data.REGULAR_MARKET_TRADE_MILLIS),
                SECURITY_STATUS = COALESCE(excluded.SECURITY_STATUS, streaming_data.SECURITY_STATUS),
                TOTAL_VOLUME = COALESCE(excluded.TOTAL_VOLUME, streaming_data.TOTAL_VOLUME),
                TRADE_TIME_MILLIS = COALESCE(excluded.TRADE_TIME_MILLIS, streaming_data.TRADE_TIME_MILLIS),
                assetMainType = COALESCE(excluded.assetMainType, streaming_data.assetMainType),
                assetSubType = COALESCE(excluded.assetSubType, streaming_data.assetSubType),
                cusip = COALESCE(excluded.cusip, streaming_data.cusip),
                delayed = COALESCE(excluded.delayed, streaming_data.delayed)
        """,
            (
                data.get("command"),
                data.get("service"),
                data.get("timestamp"),
                content.get("key"),
                content.get("ASK_ID"),
                content.get("ASK_MIC_ID"),
                content.get("ASK_PRICE"),
                content.get("ASK_SIZE"),
                content.get("ASK_TIME_MILLIS"),
                content.get("BID_ID"),
                content.get("BID_MIC_ID"),
                content.get("BID_PRICE"),
                content.get("BID_SIZE"),
                content.get("BID_TIME_MILLIS"),
                content.get("CLOSE_PRICE"),
                content.get("DESCRIPTION"),
                content.get("DIVIDEND_AMOUNT"),
                content.get("DIVIDEND_DATE"),
                content.get("DIVIDEND_YIELD"),
                content.get("EXCHANGE_ID"),
                content.get("EXCHANGE_NAME"),
                content.get("HARD_TO_BORROW"),
                content.get("HIGH_PRICE"),
                content.get("HIGH_PRICE_52_WEEK"),
                content.get("HTB_QUALITY"),
                content.get("HTB_RATE"),
                content.get("IS_SHORTABLE"),
                content.get("LAST_ID"),
                content.get("LAST_MIC_ID"),
                content.get("LAST_PRICE"),
                content.get("LAST_SIZE"),
                content.get("LOW_PRICE"),
                content.get("LOW_PRICE_52_WEEK"),
                content.get("MARGINABLE"),
                content.get("MARK"),
                content.get("MARK_CHANGE"),
                content.get("MARK_CHANGE_PERCENT"),
                content.get("NAV"),
                content.get("NET_CHANGE"),
                content.get("NET_CHANGE_PERCENT"),
                content.get("OPEN_PRICE"),
                content.get("PE_RATIO"),
                content.get("POST_MARKET_NET_CHANGE"),
                content.get("POST_MARKET_NET_CHANGE_PERCENT"),
                content.get("QUOTE_TIME_MILLIS"),
                content.get("REGULAR_MARKET_CHANGE_PERCENT"),
                content.get("REGULAR_MARKET_LAST_PRICE"),
                content.get("REGULAR_MARKET_LAST_SIZE"),
                content.get("REGULAR_MARKET_NET_CHANGE"),
                content.get("REGULAR_MARKET_QUOTE"),
                content.get("REGULAR_MARKET_TRADE"),
                content.get("REGULAR_MARKET_TRADE_MILLIS"),
                content.get("SECURITY_STATUS"),
                content.get("TOTAL_VOLUME"),
                content.get("TRADE_TIME_MILLIS"),
                content.get("assetMainType"),
                content.get("assetSubType"),
                content.get("cusip"),
                content.get("delayed"),
            ),
        )

    # Commit changes and close connection
    conn.commit()
    conn.close()



def write_to_db(stream_data):
    # Connect to SQLite database (or create it if it doesn't exist)
    conn = sqlite3.connect("streaming_data.db")
    cursor = conn.cursor()

    # Parse JSON data
    data = json.loads(json.dumps(stream_data))

    for content in data["content"]:
        # Insert data into the table

        cursor.execute(
            """
            INSERT INTO streaming_data (
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
            (
                data.get("command"),
                data.get("service"),
                data.get("timestamp"),
                content.get("key"),
                content.get("ASK_ID"),
                content.get("ASK_MIC_ID"),
                content.get("ASK_PRICE"),
                content.get("ASK_SIZE"),
                content.get("ASK_TIME_MILLIS"),
                content.get("BID_ID"),
                content.get("BID_MIC_ID"),
                content.get("BID_PRICE"),
                content.get("BID_SIZE"),
                content.get("BID_TIME_MILLIS"),
                content.get("CLOSE_PRICE"),
                content.get("DESCRIPTION"),
                content.get("DIVIDEND_AMOUNT"),
                content.get("DIVIDEND_DATE"),
                content.get("DIVIDEND_YIELD"),
                content.get("EXCHANGE_ID"),
                content.get("EXCHANGE_NAME"),
                content.get("HARD_TO_BORROW"),
                content.get("HIGH_PRICE"),
                content.get("HIGH_PRICE_52_WEEK"),
                content.get("HTB_QUALITY"),
                content.get("HTB_RATE"),
                content.get("IS_SHORTABLE"),
                content.get("LAST_ID"),
                content.get("LAST_MIC_ID"),
                content.get("LAST_PRICE"),
                content.get("LAST_SIZE"),
                content.get("LOW_PRICE"),
                content.get("LOW_PRICE_52_WEEK"),
                content.get("MARGINABLE"),
                content.get("MARK"),
                content.get("MARK_CHANGE"),
                content.get("MARK_CHANGE_PERCENT"),
                content.get("NAV"),
                content.get("NET_CHANGE"),
                content.get("NET_CHANGE_PERCENT"),
                content.get("OPEN_PRICE"),
                content.get("PE_RATIO"),
                content.get("POST_MARKET_NET_CHANGE"),
                content.get("POST_MARKET_NET_CHANGE_PERCENT"),
                content.get("QUOTE_TIME_MILLIS"),
                content.get("REGULAR_MARKET_CHANGE_PERCENT"),
                content.get("REGULAR_MARKET_LAST_PRICE"),
                content.get("REGULAR_MARKET_LAST_SIZE"),
                content.get("REGULAR_MARKET_NET_CHANGE"),
                content.get("REGULAR_MARKET_QUOTE"),
                content.get("REGULAR_MARKET_TRADE"),
                content.get("REGULAR_MARKET_TRADE_MILLIS"),
                content.get("SECURITY_STATUS"),
                content.get("TOTAL_VOLUME"),
                content.get("TRADE_TIME_MILLIS"),
                content.get("assetMainType"),
                content.get("assetSubType"),
                content.get("cusip"),
                content.get("delayed"),
            ),
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
