"""Context navigation for SupportSession"""

from ...application.support_session import SupportSession


class Context:
    @classmethod
    def get_parent(cls, command_context_object: SupportSession) -> None:
        """SupportSession is the root context, no parent"""
        return None
