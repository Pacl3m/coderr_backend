from rest_framework.permissions import BasePermission, IsAuthenticated, SAFE_METHODS


class IsOwnerOrAdmin(BasePermission):

    # def has_permission(self, request, view):
    #     if request.method in SAFE_METHODS:
    #         print('1')
    #         return True

    def has_object_permission(self, request, view, obj):
        if request.method in SAFE_METHODS:
            print('1')
            return True
        else:
            print('3')
            return bool((request.user == obj.user) or request.user.is_superuser)


class IsBusinessUser(BasePermission):

    def has_permission(self, request, view):
        print(request.method)
        if request.method in SAFE_METHODS:
            print('4')
            return True
        else:
            print('6')
            return bool(request.user.type == "business" or request.user.is_superuser)


class IsSuperUser(BasePermission):

    def has_permission(self, request, view):
        # if request.method in SAFE_METHODS:
        #     return True
        if request.user.is_superuser:
            return True
