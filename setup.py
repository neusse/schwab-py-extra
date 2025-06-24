
from setuptools import setup, find_packages

with open('README.md', 'r') as f:
    long_description = f.read()

with open('schwab_extra/version.py', 'r') as f:
    version = [s.strip() for s in f.read().strip().split('=')][1]
    version = version[1:-1]

setup(
    name='schwab-py-extra',
    version=version,
    author='George Neusse',
    author_email='george2neusse.com',
    description='Unofficial extension for the Schwab-py',
    long_description=long_description,
    long_description_content_type='text/x-rst',
    url='https://github.com/neusse/schwab-py-extra',
    classifiers=[
        'Programming Language :: Python :: 3',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
        'Intended Audience :: Developers',
        'Development Status :: 1 - Planning',
        'Natural Language :: English',
        'Operating System :: OS Independent',
        'Topic :: Office/Business :: Financial :: Investment',
    ],
    python_requires='>=3.10',
    install_requires=[
        'alpaca-py',
        'alpaca',
        'backtesting',
        'beautifulsoup4',
        'httpx',
        'matplotlib',
        'mplfinance',
        'numpy',
        'packaging',
        'pandas',
        'pandas_ta',
        'Requests',
        'rich',
        'schwab_py',
        'scipy',
        'setuptools',
        'tabulate',
        'yfinance',
        'certifi',
        'pandas_market_calendars',
    ],
    # extras_require={
    #     'dev': [
    #         'callee',
    #         'colorama',
    #         'coverage',
    #         'nose',
    #         'pytest',
    #         'pytz',
    #         'setuptools',
    #         'sphinx_rtd_theme',
    #         'twine',
    #         'wheel',
    #     ]
    # },
    packages=find_packages(),            # ← this auto-includes schwab and schwab.scripts
    include_package_data=True,
    entry_points={
        'console_scripts': [
            'alpaca-setup-env = schwab_extra.alpaca_setup_env:main',
            'schwab-dividend-calender = schwab_extra.schwab_dividend_calender:main',
            'schwab-fetch-new-token = schwab_extra.schwab_fetch_new_token:main',
            'schwab-list = schwab_extra.schwab_list:main',
            'schwab-package-checker = schwab_extra.schwab_package_checker:main', 
            'schwab-portfolio-analyzer = schwab_extra.schwab_portfolio_analyzer:main', 
            'schwab-positions-monitor = schwab_extra.schwab_positions_monitor:main',
            'schwab-py-analysis = schwab_extra.schwab_py_analysis:main',
            'schwab-refresh-token = schwab_extra.schwab_refresh_token:main',
            'schwab-setup-env = schwab_extra.schwab_setup_env:main',
            'yf-dividend-screener = schwab_extra.yf_dividend_screener:main',
            'yf-gapper-screener = schwab_extra.yf_gapper_screener:main',
        ],
    },
    keywords='finance trading equities bonds options research extras',
    # project_urls={
    #     'Source': 'https://github.com/neusse/schwab-py-extra',
    #     'Tracker': 'https://github.com/neusse/schwab-py-extra/issues',
    # },
    license='MIT',

#    scripts=[
#        'bin/pass.py',
#        'bin/pass.py',
#    ],

)

