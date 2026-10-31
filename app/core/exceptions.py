class KnowledgeError(Exception):
    """Erro controlado ao carregar ou consultar as bases locais."""


class ProviderError(Exception):
    """Falha segura de comunicação ou resposta do provedor de IA."""


class InsufficientEvidence(Exception):
    """Sinaliza que a base não contém evidência suficiente para responder."""
