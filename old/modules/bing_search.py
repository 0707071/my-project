import requests
import time
from typing import List, Dict

class RateLimiter:
    def __init__(self, max_calls, period):
        self.max_calls = max_calls
        self.period = period
        self.calls = []

    def __call__(self, func):
        def wrapper(*args, **kwargs):
            now = time.time()
            
            # Удаляем старые вызовы
            self.calls = [call for call in self.calls if now - call < self.period]
            
            if len(self.calls) >= self.max_calls:
                sleep_time = self.period - (now - self.calls[0])
                if sleep_time > 0:
                    time.sleep(sleep_time)
            
            self.calls.append(time.time())
            return func(*args, **kwargs)
        return wrapper

@RateLimiter(max_calls=3, period=1)
def bing_search(query: str, api_key: str, endpoint: str, count: int = 10) -> List[Dict[str, str]]:
    headers = {"Ocp-Apim-Subscription-Key": api_key}
    params = {"q": query, "count": count, "textDecorations": True, "textFormat": "HTML"}

    try:
        response = requests.get(endpoint, headers=headers, params=params)
        response.raise_for_status()
        search_results = response.json()

        results = []
        for result in search_results.get("webPages", {}).get("value", []):
            results.append({
                "title": result.get("name", ""),
                "link": result.get("url", ""),
                "description": result.get("snippet", "")
            })

        return results
    except requests.exceptions.RequestException as e:
        print(f"Ошибка при выполнении запроса к Bing API: {e}")
        return []

def get_bing_search_results(query: str, config: dict) -> List[Dict[str, str]]:
    api_keys = config['api_keys']
    endpoint = config['endpoint']
    count = config.get('num_results', 10)

    for api_key in api_keys:
        try:
            results = bing_search(query, api_key, endpoint, count)
            if results:
                return results
        except Exception as e:
            print(f"Ошибка при использовании ключа API: {e}")
    
    print("Не удалось получить результаты ни с одним из ключей API")
    return []