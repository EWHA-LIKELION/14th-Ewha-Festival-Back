from typing import Literal
from django.http import HttpRequest
from django.shortcuts import get_object_or_404
from booths.models import Booth
from shows.models import Show

class PermissionService:
    def __init__(self, request:HttpRequest, pk:int|None=None):
        self.request = request
        self.pk = pk

    def validate(self, kind:Literal["booth","show"], password:str)->bool:
        if kind == "booth":
            model_cls = Booth
        elif kind == "show":
            model_cls =Show

        obj = get_object_or_404(model_cls, pk=self.pk)
        return obj.check_admincode(password), obj

    def add_permission(self, kind:Literal["booth","show"], obj:Booth|Show):
        user_permission_field = getattr(self.request.user, f"permission_{kind}")
        user_permission_field.add(obj)
