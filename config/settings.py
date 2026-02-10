PAGE_CONFIG = {
    "page_title": "SMT防错比对系统",
    "page_icon": "🛡️",
    "layout": "wide",
    "initial_sidebar_state": "collapsed"
}
SPLIT_PATTERN = r'[、,，/ ;；\n\t\-]+'
SPEC_PATTERNS = {
    "PKG": r'\b(01005|0201|0402|0603|0805|1206|1210|2010|2512)\b',
    "VOLT": r'\b(\d+(?:\.\d+)?V)\b'
}
CACHE_TTL = 3600