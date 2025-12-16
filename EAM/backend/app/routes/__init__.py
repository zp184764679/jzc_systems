# backend/app/routes/__init__.py
from . import machines
from . import integration
from . import base_data
from . import maintenance
from . import capacity

__all__ = ['machines', 'integration', 'base_data', 'maintenance', 'capacity']
