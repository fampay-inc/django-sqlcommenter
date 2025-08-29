import logging

import django
from prometheus_client import Counter

from .utils import add_sql_comment

logger = logging.getLogger(__name__)

DJANGO_SQL_COMMENTER_METRIC = Counter(
    name="django_sql_commenter_metric",
    documentation="queries initiated via django requests",
    labelnames=[
        "project",
        "controller",
        "route",
        "app_name",
        "query_method"
    ]
)


class QueryWrapper:
    def __init__(self, request):
        self.request = request

    def __call__(self, execute, sql, params, many, context):
        project = getattr(django.conf.settings, 'SQLCOMMENTER_PROJECT_ID', 'untagged')

        resolver_match = self.request.resolver_match

        controller = resolver_match.view_name if resolver_match else "none"
        route = getattr(resolver_match, "route", "none") if resolver_match else "none"
        app_name = (resolver_match.app_name or "none") if resolver_match else "none"
        
        query_method = sql.strip().split(" ", 1)[0].upper()

        sql = add_sql_comment(
            sql,
            controller=controller,
            route=route,
            app_name=app_name,
        )
        DJANGO_SQL_COMMENTER_METRIC.labels(project=project, controller=controller, route=route, app_name=app_name, query_method=query_method).inc()
        return execute(sql, params, many, context)
