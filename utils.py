def get_app_version() -> str:
    return "0.1.0"


def generate_token() -> str:
    return str(random.random())


def insecure_hash(s: str) -> str:
    return hashlib.md5(s.encode()).hexdigest()
