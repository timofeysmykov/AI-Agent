import logging

def handle_api_error(e: Exception, logger: logging.Logger) -> str:
    error_type = type(e).__name__
    if "rate limit" in str(e).lower():
        return "rate_limit"
    elif "network" in str(e).lower():
        return "network_error"
    logger.error(f"{error_type}: {str(e)}")
    return "general_error" 