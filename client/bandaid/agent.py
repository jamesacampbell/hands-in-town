"""Gets latest band data for a particular band and adds to user watchlist."""
from bs4 import BeautifulSoup as bs
import datetime
from os import environ, getcwd, path
import requests
import argparse
from pathlib import Path
import sqlite3
import sys
from pprint import pprint


__version__ = "1.0.9"


def printlogo():
    """
    Prints logo
    Returns nothing
    """
    print("")
    print("     ;;;;;;;;;;;;;;;;;;; ")
    print("     ;;;;;;;;;;;;;;;;;;; ")
    print("     ;                 ; ")
    print("     ;     bandaid     ; ")
    print("     ;                 ; ")
    print("     ;  +-----------+  ; ")
    print("     ;  |by JC 2020 |  ; ")
    print("     ;  +-----------+  ; ")
    print("     ;                 ; ")
    print(",;;;;;            ,;;;;; ")
    print(";;;;;;            ;;;;;; ")
    print("`;;;;'            `;;;;' ")
    print("")


def initDB(dbpath, zipcode, username, lat, lng):
    open(dbpath, "w+")
    conn = sqlite3.connect(str(dbpath))
    c = conn.cursor()
    c.execute('''CREATE TABLE tracker
             (id integer PRIMARY KEY, date_added text, date_last_checked text,
             band text, on_tour integer, coming_to_town integer,
             notified integer, push_updates integer, zipcode integer)''')
    c.execute('''CREATE TABLE user
             (id integer PRIMARY KEY, date_added text, username text,
             zipcode integer, os text, lat FLOAT, long FLOAT )''')
    currentdate = datetime.datetime.now()
    opersystem = sys.platform
    c.execute('insert into user(date_added, username, zipcode, os, lat, long)\
              values(?, ?, ?, ?, ?, ?)',
              (currentdate, username, zipcode, opersystem, lat, lng))
    conn.commit()
    conn.close()


def checkFirstRun():
    """
    Check if file exists for the sqlite database and
    if not creates it and cfg and gets zipcode
    """
    my_cfg = Path.home() / ".bandaid" / "bandaid.cfg"
    my_db = Path.home() / ".bandaid" / "bandaid.db"
    if Path(f'{Path.home()}/.bandaid/').exists():
        return my_db
    print("First run, making the donuts...")
    Path.mkdir(Path.home() / ".bandaid", exist_ok=True)
    zipcode = inputZip()
    lat, lng = getLatLng(zipcode)
    with open(my_cfg, "w+") as f:
        f.write('DBPATH=~/.bandaid/bandaid.db\n')
        f.write(f'ZIPCODE={zipcode}')
    user = (lambda: environ["USERNAME"] if "C:" in getcwd() else environ["USER"])()
    initDB(my_db, zipcode, user, lat, lng)
    print(f"Database and config file created at {my_cfg}")
    return my_db


def inputZip() -> int:
    """
    Returns integer zipcode only
    """
    while True:
        try:
            return int(input("Enter your zipcode for concerts near you: "))
        except ValueError:
            print("Input only accepts numbers.")


def getZipCode(dbpath):
    """
    Gets zipcode from user table in sqlite db (check bandaid.cfg for path)
    """
    conn = sqlite3.connect(str(dbpath))
    c = conn.cursor()
    c.execute("select zipcode from user where id=1")
    conn.commit()
    zipcode = c.fetchone()[0]
    conn.close()
    return zipcode


def getLatLng(zipcode=22207) -> (float, float):
    """
    Uses free service to get latitude and longitude and store
    Returns
    ---
    lat float var for user table
    lng float var for user table

    """
    r = requests.get(f"https://geocode.xyz/{zipcode}?json=1")
    data = r.json()
    lat = data.get('latt')
    lng = data.get('longt')
    return lat, lng


def watchlist(bandname, dbpath):
    """
    Add band to watchlist, initialize watchlist service and db is doesn't exist
    """
    print("In future versions, there will be an\
          option to auto check every hour.")
    print("For now, you have to run the bandaid -f or bandaid --fetch command to\
          get current status of all bands tracking")
    promptsure = "y"
    promptsure = input(f"Are you sure you want to watch {bandname}? (y/n): ")
    if promptsure in ['n', 'no', 'N', 'No', 'NO']:
        exit('Thanks!')
    if promptsure not in ['y', 'Y', 'n', 'N']:
        print('Assuming you meant yes, and moving forward with tracking.')
    zipcode = getZipCode(dbpath)
    promptzip = input(f"Do you want to track {bandname} to {zipcode}? (y/n): ")
    if promptzip in ["n", "N"]:
        zipcode = input(f"What zip would you like for {bandname}? ")
    sqlstatement = "insert into tracker(date_added, date_last_checked,\
                    band, on_tour, zipcode) values(?,?,?,?,?)"
    insertSQL(sqlstatement, dbpath, (datetime.datetime.now(),
                                     datetime.datetime.now(),
                                     bandname, 1, int(zipcode)))
    print('Added band to tracker database. To get status at any time,\
          rerun with -f and -b band')
    # TODO ask user if they want to be automatically notified or manually check
    # conn = sqlite3.connect(Path.home() / ".bandaid.db")
    # TODO add supervisord creation and launchctl and permissions potentially


def getBand(bandname, dbpath):
    """
    Get band page and related data
    """
    indb = executeSingleSQL("Select band from tracker where band = ?", dbpath, (bandname,))
    if indb != None:
        print("You are already tracking tool. Run `bandaid -f tool` to get detailed info.")
    exit()
    baseurl = "https://www.bandsintown.com/{}"
    r = requests.get(baseurl.format(bandname))
    if r.status_code == 200:
        if "No upcoming events</div>" in r.text:
            print(f"No upcoming events for {bandname}.")
        else:
            print(f"{bandname} is on tour!")
            bandtrack = input(f"Would you like to track {bandname}? (y/n) ")
            if bandtrack in ['y', 'Y']:
                print(f"Adding {bandname} to your watchlist now...")
                watchlist(bandname, dbpath)
            else:
                print("To track if they are coming near you, add to\
                      watchlist next time you run.")
                exit()
    else:
        exit('Nothing exists for that band name.')


def prepper():
    """
    Process all runtime arguments
    """
    parser = argparse.ArgumentParser()
    parser.add_argument('-b', '--band', dest='bandname',
                        help="band to lookup", type=str, nargs='+')
    parser.add_argument('-w', '--watchlist', dest='watchlist',
                        action='store_true', help="add to watchlist")
    parser.add_argument('-f', '--fetch', dest='fetcher',
                        action='store_true', help="fetch a band (with -b flag)\
                        or no extra flag for all bands tracking current status"
                        )
    parser.add_argument('-c', '--config', dest='config', action='store_true',
                        help='print out current config info')
    args = parser.parse_args()
    return args


def executeArraySQL(sqlstatement, dbpath):
    conn = sqlite3.connect(str(dbpath))
    c = conn.cursor()
    c.execute(sqlstatement)
    return c.fetchall()


def executeSingleSQL(sqlstatement, dbpath, tuplevar):
    conn = sqlite3.connect(str(dbpath))
    c = conn.cursor()
    c.execute(sqlstatement, tuplevar)
    return c.fetchone()


def insertSQL(sqlstatement, dbpath, tuplevar):
    conn = sqlite3.connect(str(dbpath))
    c = conn.cursor()
    c.execute(sqlstatement, tuplevar)
    conn.commit()
    conn.close()


def fetchCurrentStatus(bandname, dbpath):
    """
    Get current status and update in db for band or all bands
    Note: If bandname is blank, it is just foo, so grabs all bands
    """
    # check if bandname not passed and then load all tracked bands
    if bandname == 'foo':
        sqlcall = "select band from tracker"
        listofbands = executeArraySQL(sqlcall, dbpath)
        for band in listofbands:
            print(band)
        exit('thanks for trying out multiple bands, not fully working yet')
    bandinfo = executeSingleSQL("select date_added from tracker where band=?",
                                (bandname,))
    print(bandinfo)
    exit("not fully implemented yet")


def printConfig(dbpath):
    conn = sqlite3.connect(str(dbpath))
    c = conn.cursor()
    c.execute("select * from user where id = 1")
    conn.commit()
    data = c.fetchone()
    print(f"Username: {data[0]}")
    print(f"Lat/Lng: {data[4]}/{data[5]}")
    conn.close()
    exit("Thanks for checking the configuration.")

def main():
    """
    Main function that runs everything
    """
    args = prepper()
    dbpath = checkFirstRun()
    if args.config:
        printConfig(dbpath)
    printlogo()
    if args.fetcher and args.bandname:
        fetchCurrentStatus(args.bandname, dbpath)
    if args.fetcher and not args.bandname:
        fetchCurrentStatus('foo', dbpath)
    if args.bandname:
        getBand(" ".join(args.bandname), dbpath)
    else:
        exit('Must set band name -h for help.')


if __name__ == "__main__":
    main()
