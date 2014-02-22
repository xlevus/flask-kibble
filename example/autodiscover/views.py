import flask_kibble as kibble

from .models import AutodiscoverTestModel

class AutodiscoverList(kibble.List):
    model = AutodiscoverTestModel


class AutodiscoverCreate(kibble.Create):
    model = AutodiscoverTestModel

