class SecondaryRouter:
    def db_for_read(self, model, **hints):
        if model._meta.app_label == 'prodigy'
            print(f"SecondaryRouter.db_for_read(), app_label = {model._meta.app_label}, model = {model.__name__}")
            return 'secondary'
        return 'default'

    def db_for_write(self, model, **hints):
        return self.db_for_read(model, **hints)
