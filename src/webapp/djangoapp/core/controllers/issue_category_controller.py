from djangoapp.core.models import IssueCategory


class IssueCategoryController:
    @staticmethod
    def create(cleaned_data):
        return IssueCategory.objects.create(**cleaned_data)

    @staticmethod
    def update(issue_category, cleaned_data):
        for field, value in cleaned_data.items():
            setattr(issue_category, field, value)
        issue_category.save()
        return issue_category
