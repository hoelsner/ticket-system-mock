from djangoapp.core.models import WorkflowStateAutoAssignmentRule


class WorkflowStateAutoAssignmentRuleController:
    @staticmethod
    def create(cleaned_data):
        return WorkflowStateAutoAssignmentRule.objects.create(**cleaned_data)

    @staticmethod
    def update(rule, cleaned_data):
        for field, value in cleaned_data.items():
            setattr(rule, field, value)

        rule.save()
        return rule

    @staticmethod
    def delete(rule):
        rule.delete()
