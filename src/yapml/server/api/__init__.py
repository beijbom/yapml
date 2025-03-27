from .admin_routes import router as admin_router
from .boundingbox_routes import list_boxes
from .boundingbox_routes import router as boundingbox_router
from .function_routes import list_functions
from .function_routes import router as function_router
from .label_routes import list_labels
from .label_routes import router as label_router
from .sample_routes import get_sample, list_samples
from .sample_routes import router as sample_router

__all__ = [
    "admin_router",
    "boundingbox_router",
    "label_router",
    "sample_router",
    "list_samples",
    "get_sample",
    "list_labels",
    "function_router",
    "list_boxes",
    "list_functions",
]
