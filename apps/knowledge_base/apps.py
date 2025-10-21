from django.apps import AppConfig


class KnowledgeBaseConfig(AppConfig):
    """Configuration for knowledge base app."""
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.knowledge_base"
    verbose_name = "Knowledge Base"