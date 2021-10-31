def todo_on_save(sender, instance, **kwargs):
    return True


def todo_on_delete(sender, instance, **kwargs):
    return True


actions = {"tests://ToDo": {"on_save": todo_on_save, "on_delete": todo_on_delete}}
