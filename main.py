import os
from datetime import datetime, timedelta, timezone
from concurrent.futures import ThreadPoolExecutor, as_completed

import db
import licor
import klh

def process_sync():
    wib_tz = timezone(timedelta(hours=7)) # Asia/Jakarta (WIB)
    now_wib = datetime.now(wib_tz)
    
    print(f"[MAIN PROGRAM] Running Multi-Tenant Sync Loop at {now_wib.strftime('%Y-%m-%d %H:%M:%S')} WIB")
    
    # 1. Sync configuration file entries
    db.sync_config_from_csv()
    
    active_loggers = db.get_active_loggers()
    if not active_loggers:
        print("[MAIN PROGRAM] [WARNING] No customer devices found in data storage. Loop paused.")
        return

    # Calculate current UTC limits
    end_utc = now_wib.astimezone(timezone.utc)
    end_date_str = end_utc.strftime('%Y-%m-%d %H:%M:%S')

    all_fetched_data = []

    # 2. Threaded Fetch with DYNAMIC lookback calculations per individual logger
    print(f"[MAIN PROGRAM] Spawning dynamic ingestion loops for {len(active_loggers)} loggers...")
    with ThreadPoolExecutor(max_workers=5) as executor:
        future_to_logger = {}
        
        for logger in active_loggers:
            gov_id = logger['klh_device_id_unik']
            customer = logger['customer_name']
            
            # Look up the last known timestamp in our local DB
            last_recorded_ts = db.get_last_timestamp(gov_id)
            
            if last_recorded_ts:
                # Format in DB is "2026-06-26 03:00:00Z". Strip "Z" to match Li-Cor input rule
                start_date_str = last_recorded_ts.replace("Z", "")
                print(f"[MAIN PROGRAM] [{customer}] Catch-Up Mode: Requesting data since last save point: {start_date_str} UTC")
            else:
                # Fallback if brand new system with no historical rows: Default to 24-hour window
                start_utc = end_utc - timedelta(hours=24)
                start_date_str = start_utc.strftime('%Y-%m-%d %H:%M:%S')
                print(f"[MAIN PROGRAM] [{customer}] Initialization Mode: Seeding historical 24-hour window.")

            # Submit the personalized time boundary query into the thread pipeline
            task = executor.submit(licor.fetch_single_logger, logger, start_date_str, end_date_str)
            future_to_logger[task] = logger

        for future in as_completed(future_to_logger):
            all_fetched_data.extend(future.result())

    # 3. Write items to queue (SQLite UNIQUE rule drops overlapping items instantly)
    db.save_to_queue(all_fetched_data)

    # 4. Threaded Government Push Execution
    unsent_records = db.fetch_unsent_records()
    if not unsent_records:
        print("[MAIN PROGRAM] Queue clear. No new records or backlogs found to sync. Exiting gracefully.")
        return

    print(f"[MAIN PROGRAM] Found {len(unsent_records)} backlogged items in queue. Syncing to government...")
    audit_records = []
    with ThreadPoolExecutor(max_workers=10) as executor:
        future_to_record = {
            executor.submit(klh.push_single_record, record): record 
            for record in unsent_records
        }
        for future in as_completed(future_to_record):
            record_id, success, insert_id, timestamp = future.result()
            if success:
                audit_records.append((insert_id, timestamp, record_id))

    # Log successful receipts
    if audit_records:
        db.mark_as_sent_with_audit(audit_records)
        print(f"[MAIN PROGRAM] Successfully synchronized and audited {len(audit_records)} records to KLH.")

if __name__ == "__main__":
    db.init_db()
    process_sync()
