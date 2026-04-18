import logging

from uvicorn.logging import AccessFormatter


async def init_logging():
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    )

    handler = logging.StreamHandler()
    handler.setFormatter(
        AccessFormatter('%(asctime)s - %(name)s - %(levelname)s - %(client_addr)s - "%(request_line)s" %(status_code)s')
    )
    access_logger = logging.getLogger('uvicorn.access')
    access_logger.handlers = [handler]
    access_logger.propagate = False
