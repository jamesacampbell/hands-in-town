# hands-in-town

Bands-in-town command line interface tool to track bands you want to see.

## Server

The server is made up of the following components:

1. Watchman (Watchlist manager)
    - Mark bands that you want to watch for and know when on tour and if coming to town
2. SiS (Stay in Sync)
    - Sync all bands data to the extent possible to database
3. GoldRecords
    - Store all the things
4. WillCall
    - Queue Management / Orchestration

## Client

1. CLI to provide all interactive functionality
    - Use case is "Show me Aerosmith" and it will mark as watching and also whether on tour or now
2. Modules to integrate into other code (`from hands-in-town import blah`)
