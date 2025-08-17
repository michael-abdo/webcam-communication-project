"""Configuration management for the pipeline"""

import yaml
import os
import logging
import logging.config
from pathlib import Path
from typing import Dict, Any


class Config:
    """Manages configuration for the pipeline"""
    
    def __init__(self, config_path: str = None):
        """Initialize configuration from YAML file
        
        Args:
            config_path: Path to config file. Defaults to config/config.yaml
        """
        if config_path is None:
            # Get project root directory
            root_dir = Path(__file__).parent.parent.parent
            config_path = root_dir / "config" / "config.yaml"
        
        self.config_path = Path(config_path)
        self._config = self._load_config()
        
    def _load_config(self) -> Dict[str, Any]:
        """Load configuration from YAML file"""
        if not self.config_path.exists():
            raise FileNotFoundError(f"Configuration file not found: {self.config_path}")
            
        with open(self.config_path, 'r') as f:
            return yaml.safe_load(f)
    
    @property
    def api(self) -> Dict[str, Any]:
        """Get API configuration"""
        return self._config.get('api', {})
    
    # Processing configuration removed - now handled by shared processing system
    
    @property
    def timeouts(self) -> Dict[str, Any]:
        """Get timeout configuration"""
        return self._config.get('timeouts', {})
    
    @property
    def paths(self) -> Dict[str, str]:
        """Get path configuration"""
        return self._config.get('paths', {})
    
    def get_path(self, key: str) -> Path:
        """Get a path from configuration and ensure it exists
        
        Args:
            key: Path key (e.g., 'downloads', 'samples')
            
        Returns:
            Path object for the requested directory
        """
        path_str = self.paths.get(key)
        if not path_str:
            raise ValueError(f"Path not configured: {key}")
            
        # Make path relative to project root if not absolute
        if not os.path.isabs(path_str):
            root_dir = Path(__file__).parent.parent.parent
            path = root_dir / path_str
        else:
            path = Path(path_str)
            
        # Create directory if it doesn't exist
        path.mkdir(parents=True, exist_ok=True)
        
        return path


def setup_logging(log_level: str = "INFO") -> None:
    """Set up logging configuration
    
    Args:
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
    """
    # Get logs directory
    root_dir = Path(__file__).parent.parent.parent
    logs_dir = root_dir / "logs"
    logs_dir.mkdir(parents=True, exist_ok=True)
    
    # Logging configuration
    logging_config = {
        'version': 1,
        'disable_existing_loggers': False,
        'formatters': {
            'standard': {
                'format': '%(asctime)s [%(levelname)s] %(name)s: %(message)s',
                'datefmt': '%Y-%m-%d %H:%M:%S'
            },
            'detailed': {
                'format': '%(asctime)s [%(levelname)s] %(name)s - %(filename)s:%(lineno)d - %(message)s',
                'datefmt': '%Y-%m-%d %H:%M:%S'
            }
        },
        'handlers': {
            'console': {
                'class': 'logging.StreamHandler',
                'level': log_level,
                'formatter': 'standard',
                'stream': 'ext://sys.stdout'
            },
            'file': {
                'class': 'logging.FileHandler',
                'level': 'DEBUG',
                'formatter': 'detailed',
                'filename': logs_dir / 'pipeline.log',
                'mode': 'a'
            },
            'error_file': {
                'class': 'logging.FileHandler',
                'level': 'ERROR',
                'formatter': 'detailed',
                'filename': logs_dir / 'errors.log',
                'mode': 'a'
            }
        },
        'loggers': {
            'pipeline': {
                'level': 'DEBUG',
                'handlers': ['console', 'file', 'error_file'],
                'propagate': False
            },
            'api': {
                'level': 'DEBUG',
                'handlers': ['console', 'file', 'error_file'],
                'propagate': False
            }
        },
        'root': {
            'level': log_level,
            'handlers': ['console', 'file']
        }
    }
    
    logging.config.dictConfig(logging_config)
    
    # Log initialization
    logger = logging.getLogger('pipeline')
    logger.info("Logging initialized")