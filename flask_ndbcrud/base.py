import flask
from flask.views import View


class CrudView(View):
    action = None
    model = None

    url_patterns = [
        ("/{kind}/{action}/", {}),
    ]

    @classmethod
    def view_name(cls):
        return "%s_%s" % (cls.model.kind().lower(), cls.action)

    @property
    def templates(self):
        return [
            'crud/%s.html' % self.action,
            'crud/%s_%s.html' % (self.model.kind().lower(), self.action)
        ]


class List(CrudView):
    action = 'list'
    url_patterns = [
        ("/{kind}/", {})
    ]

