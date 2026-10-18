"""Python 3.14 + Django 5.1 template Context copy workaround used by the test client."""


def patch_django_template_context_copy():
    from django.template.context import BaseContext

    if getattr(BaseContext.__copy__, '_cinereserve_patched', False):
        return

    def _basecontext_copy(self):
        duplicate = object.__new__(self.__class__)
        duplicate.__dict__.update(getattr(self, '__dict__', {}))
        duplicate.dicts = list(self.dicts)
        return duplicate

    _basecontext_copy._cinereserve_patched = True
    BaseContext.__copy__ = _basecontext_copy
