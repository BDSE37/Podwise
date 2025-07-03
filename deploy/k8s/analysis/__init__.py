import os
import logging
from dotenv import load_dotenv
from omegaconf import OmegaConf

# Load environment variables from .env file
load_dotenv()

# Mapping of environment variable values to logging levels
LOG_LEVEL_MAP = {
    "DEBUG": logging.DEBUG,
    "INFO": logging.INFO,
    "WARNING": logging.WARNING,
    "ERROR": logging.ERROR,
    "CRITICAL": logging.CRITICAL
}

log_level = LOG_LEVEL_MAP.get(
    os.environ.get("LOG_LEVEL", "INFO"),
    logging.INFO
)


# Configure the root logger
logging.basicConfig(
    level=log_level, 
    format="[%(asctime)s] [%(levelname)s] [%(name)s] - %(message)s"
)

logger = logging.getLogger(__name__)

def load_config() -> dict:
    """
    Load configuration settings from a YAML file located in the same directory as the script.

    Returns:
        dict: A nested python dictionary representing the configuration settings.
        
    Raises:
        FileNotFoundError: If the config.yaml file is not found in the directory.
        OmegaConf.ConfigKeyError: If there is an error parsing the YAML file.
    """
    root_dir = os.path.dirname(os.path.abspath(__file__))
    config_path = os.path.join(root_dir, 'config.yaml')

    try:
        config = OmegaConf.load(config_path)
        config_dict = OmegaConf.to_container(config)
        # logger.info(f"Load analysis config from the path: {config_path}.\n{config_dict}")
        return config_dict

    except FileNotFoundError:
        raise FileNotFoundError(f"Config file '{config_path}' not found.")
        
    except OmegaConf.ConfigKeyError as e:
        raise OmegaConf.ConfigKeyError(f"Error parsing config file '{config_path}': {e}")