class SecondaryRouter:
    def db_for_read(self, model, **hints):
        print(f"SecondaryRouter.db_for_read(), app_label = {model._meta.app_label}, model = {model.__name__}")
        if model._meta.app_label == 'my_secondary_app':
            return 'secondary'
        return 'default'

    def db_for_write(self, model, **hints):
        return self.db_for_read(model, **hints)
