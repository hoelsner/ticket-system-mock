from djangoapp.core.models import Collection


class CollectionController:
    @staticmethod
    def create(cleaned_data):
        return Collection.objects.create(**cleaned_data)

    @staticmethod
    def update(collection, cleaned_data):
        for field, value in cleaned_data.items():
            setattr(collection, field, value)
        collection.save()
        return collection
