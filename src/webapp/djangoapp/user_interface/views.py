from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import TemplateView


class AuthenticatedTemplateView(LoginRequiredMixin, TemplateView):
    pass


class HomeView(AuthenticatedTemplateView):
    template_name = "core/home.html"