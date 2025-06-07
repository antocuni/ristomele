#!/usr/bin/env python2
import sqlite3
import argparse
from datetime import datetime, timedelta
import sys

# ANSI color codes
RED = '\033[91m'
RESET = '\033[0m'

def parse_args():
    parser = argparse.ArgumentParser(description='Adjust order dates in SQLite DB.')
    parser.add_argument('dbpath', help='Path to the SQLite database file')

    parser.add_argument('--from', dest='date_from',
                        help='Start of the date range (inclusive), format: "YYYY-MM-DD HH:MM"')
    parser.add_argument('--to', dest='date_to',
                        help='End of the date range (inclusive), format: "YYYY-MM-DD HH:MM"')
    parser.add_argument('--ref', dest='dateref',
                        help='Reference datetime, format: "YYYY-MM-DD HH:MM"')
    parser.add_argument('--write', action='store_true',
                        help='Apply changes (otherwise dry run)')
    parser.add_argument('--list', action='store_true',
                        help='List all orders (ID and date), detect big time gaps')
    return parser.parse_args()

def try_parse_datetime(date_str):
    formats = [
        '%Y-%m-%d %H:%M',
        '%Y-%m-%d %H:%M:%S',
        '%Y-%m-%d %H:%M:%S.%f'
    ]
    for fmt in formats:
        try:
            return datetime.strptime(date_str, fmt)
        except ValueError:
            continue
    # Try to normalize malformed seconds like "23:50:0"
    if date_str.count(':') == 2 and date_str[-1] == '0':
        try:
            return datetime.strptime(date_str + '0', '%Y-%m-%d %H:%M:%S')
        except ValueError:
            pass
    return None

def parse_datetime_input(date_str):
    res = try_parse_datetime(date_str)
    if res is None:
        print("Error: could not parse datetime '{}'".format(date_str))
        sys.exit(1)
    return res


def list_orders(dbpath):
    conn = sqlite3.connect(dbpath)
    cursor = conn.cursor()
    cursor.execute("SELECT id, date FROM 'order' WHERE date IS NOT NULL ORDER BY datetime(date)")
    rows = cursor.fetchall()
    prev_dt = None

    for row in rows:
        order_id, date_str = row
        dt = try_parse_datetime(date_str)
        if not dt:
            print("Invalid date format for order #{}: {}".format(order_id, date_str))
            continue

        line = "{}, {}".format(order_id, date_str)
        if prev_dt:
            delta = abs(dt - prev_dt)
            if delta > timedelta(hours=24):
                line = RED + line + '    ' + str(delta) + RESET
            print line
        prev_dt = dt

    conn.close()


def adjust_dates(dbpath, date_from, date_to, dateref, write):
    fmt = '%Y-%m-%d %H:%M'

    from_dt = parse_datetime_input(date_from)
    to_dt = parse_datetime_input(date_to)
    ref_dt = parse_datetime_input(dateref)
    delta = ref_dt - from_dt

    conn = sqlite3.connect(dbpath)
    cursor = conn.cursor()

    query = "SELECT id, date FROM 'order' WHERE datetime(date) BETWEEN ? AND ?"
    cursor.execute(query, (date_from, date_to))
    rows = cursor.fetchall()

    for row in rows:
        order_id, old_date_str = row
        try:
            #old_date = datetime.strptime(old_date_str, fmt)
            old_date = try_parse_datetime(old_date_str)
        except ValueError:
            print("Skipping order #{} with invalid date format: {}".format(order_id, old_date_str))
            continue
        new_date = old_date + delta
        print("Order #{}, {} -> {}".format(order_id, old_date_str, new_date.strftime(fmt)))

        if write:
            update_query = "UPDATE 'order' SET date = ? WHERE id = ?"
            cursor.execute(update_query, (new_date.strftime(fmt), order_id))

    if write:
        conn.commit()
        print("Changes have been written to the database.")
    else:
        print("Dry run mode: no changes made.")

    conn.close()

if __name__ == '__main__':
    args = parse_args()

    if args.list:
        list_orders(args.dbpath)
        sys.exit(0)

    if not (args.date_from and args.date_to and args.dateref):
        print("Error: --from, --to, and --ref are required unless using --list")
        sys.exit(1)

    adjust_dates(args.dbpath, args.date_from, args.date_to, args.dateref, args.write)
