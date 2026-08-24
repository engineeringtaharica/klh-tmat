import requests

KLH_ENDPOINT = "https://gambutindonesia.kemenlh.go.id/backoffice-SPAgambut/api/v1/realtime_push"

def push_single_record(record):
    """Dispatches payload utilizing the row's specific customer company API key."""
    record_id, device_id, tmat, hujan, kelembapan, suhu, ph, baterai, klh_api_key = record
    
    headers = {'X-API-KEY': klh_api_key} # Unique API key per customer row
    
    payload = {
        'tmat_value': str(tmat),
        'hujan_value': str(hujan),
        'kelembapan_tanah': str(kelembapan),
        'suhu_value': str(suhu),
        'ph_value': str(ph),
        'baterai_value': str(baterai),
        'device_id_unik': device_id
    }
    
    try:
        response = requests.post(KLH_ENDPOINT, headers=headers, data=payload, timeout=15)
        print(f"[KLH GATEWAY] [RAW RESPONSE] Target Dev: {device_id} | Status: {response.status_code} | Body: {response.text}")
        
        if response.status_code == 201:
            resp_json = response.json()
            if resp_json.get('status') == True:
                # Return the critical audit trail parameters: insert_id and timestamp
                return (record_id, True, resp_json.get('insert_id'), resp_json.get('timestamp'))
            
        return (record_id, False, None, None)
    except Exception as e:
        print(f"[KLH GATEWAY] [ERROR] Physical connectivity exception on entry ID {record_id}: {e}")
        return (record_id, False, None, None)
