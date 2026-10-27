from datetime import datetime

rate_limit_store = {}
_last_rate_limit_cleanup = 0

def check_rate_limit(ip, limit=50, window=3600):
    global _last_rate_limit_cleanup
    now = datetime.utcnow().timestamp()
    if now - _last_rate_limit_cleanup > 300 or len(rate_limit_store) > 5000:
        for key, timestamps in list(rate_limit_store.items()):
            recent = [stamp for stamp in timestamps if now - stamp < window]
            if recent:
                rate_limit_store[key] = recent
            else:
                rate_limit_store.pop(key, None)
        _last_rate_limit_cleanup = now
    timestamps = [stamp for stamp in rate_limit_store.get(ip, []) if now - stamp < window]
    if len(timestamps) >= limit:
        rate_limit_store[ip] = timestamps
        return False
    timestamps.append(now)
    rate_limit_store[ip] = timestamps
    return True

