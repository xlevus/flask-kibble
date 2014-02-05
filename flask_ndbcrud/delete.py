from .operation import Operation


class Delete(Operation):
    action = 'delete'
    past_tense = 'deleted'

    button_icon = 'trash'
    button_class = 'btn-danger'

    def run(self, instance):
        instance.key.delete()
        return True

