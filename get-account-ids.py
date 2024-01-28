#!/usr/bin/env python3
"""
Search for a Mastodon account and return account IDs for each result.
"""
import argparse
import logging
import csv
import sys
from rich.table import Table
from rich.console import Console
from mastodon import Mastodon
from credentials import access_token, api_base_url

def parse_arguments():
    parser = argparse.ArgumentParser(description='Search for a Mastodon account.')
    parser.add_argument('account', help='The account to search for (eg @andypiper@macaw.social).')
    parser.add_argument('-f', '--format', choices=['csv', 'table'], default='table', help='The output format (default: table).')

    return parser.parse_args()

def initialise_mastodon():
    if not access_token or not api_base_url:
        logging.error('Mastodon credentials are not set. Please check your credentials file.')
        exit(1)
    return Mastodon(
        access_token = access_token,
        api_base_url = api_base_url
    )

def output_results_csv(results_list):
    writer = csv.writer(sys.stdout)
    for user in results_list:
        writer.writerow([ user['acct'],str(user['id']) ])

def output_results_table(results_list):
    console = Console()
    table = Table(show_header=True, header_style="bold magenta")
    table.add_column("Account", width=40)
    table.add_column("ID", width=25)

    for user in results_list:
        table.add_row(user['acct'], str(user['id']))

    console.print(table)

def search_account(mastodon, account_to_search, output_format):
    try:
        results_list = mastodon.account_search(account_to_search, limit=None, following=False)
        if not results_list:
            logging.info('No results found for account: %s', account_to_search)
        else:
            if output_format == 'csv':
                output_results_csv(results_list)
            else:
                output_results_table(results_list)
    except Exception as e:
        logging.error('Failed to search for account: %s', e)


def main():
    args = parse_arguments()
    mastodon = initialise_mastodon()
    search_account(mastodon, args.account, args.format)

if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO,format='%(message)s')
    main()
