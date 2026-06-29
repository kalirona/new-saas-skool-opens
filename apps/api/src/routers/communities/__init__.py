from src.routers.communities.communities import router as communities_router
from src.routers.communities.discussions import router as discussions_router
from src.routers.communities.spaces import router as spaces_router
from src.routers.communities.membership import router as membership_router
from src.routers.communities.plan_assignments import router as plan_assignments_router

__all__ = [
    "communities_router",
    "discussions_router",
    "spaces_router",
    "membership_router",
    "plan_assignments_router",
]
