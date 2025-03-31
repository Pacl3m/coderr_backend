from rest_framework.permissions import BasePermission, IsAuthenticated, SAFE_METHODS
from rest_framework import status
from rest_framework.exceptions import APIException


class IsAuthenticatedCustom(BasePermission):
    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            error = APIException("Benutzer ist nicht authentifiziert.")
            error.status_code = status.HTTP_401_UNAUTHORIZED
            raise error
        return True


class IsAuthenticatedOrRealOnlyCustom(BasePermission):
    def has_permission(self, request, view):
        if request.method in SAFE_METHODS:
            return True
        elif not request.user.is_authenticated:
            error = APIException("Benutzer ist nicht authentifiziert.")
            error.status_code = status.HTTP_401_UNAUTHORIZED
            raise error
        return True


class IsOwnerOrAdmin(BasePermission):

    def has_object_permission(self, request, view, obj):
        if request.method in SAFE_METHODS:
            return True
        # else:
        #     print('IsOwnerOrAdmin', bool((request.user == obj.user) or request.user.is_superuser))
        #     return bool((request.user == obj.user) or request.user.is_superuser)
        elif ((request.user != obj.user) or request.user.is_superuser):
            error = APIException(
                {'details': "Authentifizierter Benutzer ist nicht der Eigentümer des Angebots."})
            error.status_code = status.HTTP_403_FORBIDDEN
            raise error
        else:
            return bool((request.user == obj.user) or request.user.is_superuser)


class IsBusinessUser(BasePermission):

    def has_permission(self, request, view):
        if request.method in SAFE_METHODS:
            return True
        elif (request.user.type != "business" or request.user.is_superuser):
            error = APIException(
                {'details': "Authentifizierter Benutzer ist kein 'business' Profil."})
            error.status_code = status.HTTP_403_FORBIDDEN
            raise error
        else:
            return bool(request.user.type == "business" or request.user.is_superuser)


class IsCustomerUser(BasePermission):

    def has_permission(self, request, view):
        if request.method in SAFE_METHODS:
            return True
        elif (request.user.is_superuser):
            return True
        elif (request.user.type != "customer"):
            error = APIException(
                "Authentifizierter Benutzer ist kein 'customer' Profil.")
            error.status_code = status.HTTP_403_FORBIDDEN
            raise error
        else:
            return bool(request.user.type == "customer" or request.user.is_superuser)


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
