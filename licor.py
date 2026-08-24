import requests

LICOR_API_URL = "https://api.licor.cloud/v1/data"

def fetch_single_logger(logger_config, start_date_str, end_date_str):
    licor_sn = logger_config['licor_sn']
    licor_token = logger_config['licor_token']
    klh_device_id = logger_config['klh_device_id_unik']
    customer = logger_config['customer_name']
    
    headers = {'accept': 'application/json', 'Authorization': f'Bearer {licor_token}'}
    params = {'loggers': licor_sn, 'start_date_time': start_date_str, 'end_date_time': end_date_str}

    try:
        response = requests.get(LICOR_API_URL, headers=headers, params=params, timeout=30)
        if response.status_code == 200:
            raw_data = response.json().get('data', [])
            grouped_data = {}
            
            for item in raw_data:
                ts = item['timestamp']
                if not ts.endswith("00:00Z"):
                    continue

                meas_type = item['sensor_measurement_type']
                val = item['value']
                
                if ts not in grouped_data:
                    grouped_data[ts] = {
                        "device_id_unik": klh_device_id,
                        "timestamp": ts,
                        "tmat_value": 0.0,
                        "suhu_value": 0.0,
                        "ph_value": 0.0,
                        "kelembapan_tanah": 0.0,
                        "hujan_value": 0.0,
                        "baterai_value": 0.0
                    }
                
                if meas_type == "Water Level":
                    grouped_data[ts]["tmat_value"] = val*100
                elif meas_type == "Water Temperature":
                    grouped_data[ts]["suhu_value"] = val
                elif meas_type == "Water Content":
                    grouped_data[ts]["kelembapan_tanah"] = val
                elif meas_type == "Accumulated Rain":
                    grouped_data[ts]["hujan_value"] = val
                elif meas_type == "Battery":
                    grouped_data[ts]["baterai_value"] = val
            
            return list(grouped_data.values())
        return []
    except Exception as e:
        print(f"[LICOR CLOUD] [ERROR] [{customer}] Network exception: {e}")
        return []
