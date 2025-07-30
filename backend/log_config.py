# log_config.py
import logging

logging.basicConfig(
    filename="autotaskr.log",
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)
        
        