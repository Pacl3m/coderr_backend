from rest_framework.permissions import BasePermission, IsAuthenticated, SAFE_METHODS
from rest_framework import exceptions
from rest_framework.response import Response
from rest_framework import status
from rest_framework.exceptions import APIException
from rest_framework.exceptions import PermissionDenied


# class IsAuthenticatedCustom(BasePermission):

#     def has_permission(self, request, view):
#         if not request.user.is_authenticated:
#             print('DSDADS')
#             return Response(
#                 {"message": "Benutzer ist nicht authentifiziert."},
#                 status=status.HTTP_401_UNAUTHORIZED
#             )
#         return True


# class CustomUnauthorizedException(APIException):
#     status_code = 401  # HTTP-Status anpassen
#     default_detail = {"message": "Benutzer ist nicht authentifiziert."}  # Eigene JSON-Daten
#     default_code = "unauthorized"

# class IsAuthenticatedCustom(BasePermission):
#     def has_permission(self, request, view):
#         if not request.user.is_authenticated:
#             raise CustomUnauthorizedException()
#         return True

class IsAuthenticatedCustom(BasePermission):
    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            # Raise APIException with custom message
            error = APIException("Benutzer ist nicht authentifiziert.")
            error.status_code = status.HTTP_401_UNAUTHORIZED  # Set status code here
            raise error
        return True

class IsOwnerOrAdmin(BasePermission):

    def has_object_permission(self, request, view, obj):
        if request.method in SAFE_METHODS:
            return True
        else:
            return bool((request.user == obj.user) or request.user.is_superuser)


class IsBusinessUser(BasePermission):

    def has_permission(self, request, view):
        if request.method in SAFE_METHODS:
            return True
        else:
            return bool(request.user.type == "business" or request.user.is_superuser)


class IsSuperUser(BasePermission):

    def has_permission(self, request, view):
        if request.method in SAFE_METHODS:
            return True
        else:
            return bool(request.user.is_superuser)


class IsOwnUserOrAdmin(BasePermission):

    def has_object_permission(self, request, view, obj):
        if request.method in SAFE_METHODS:
            return True
        else:
            return bool(request.user.pk == obj.pk or request.user.is_superuser)
