from flask.views import View


class CrudView(View):
    action = None
    model = None

    _methods = ['GET']
    _url_patterns = [("/{kind_lower}/{action}/", {})]
    _requires_instance = True

    @classmethod
    def kind(cls):
        return cls.model._get_kind()

    @classmethod
    def view_name(cls):
        return "%s_%s" % (cls.kind().lower(), cls.action)

    @property
    def templates(self):
        return [
            'crud/%s.html' % self.action,
            'crud/%s_%s.html' % (self.kind().lower(), self.action)
        ]

    def base_context(self):
        return {
            'view': self,
        }

