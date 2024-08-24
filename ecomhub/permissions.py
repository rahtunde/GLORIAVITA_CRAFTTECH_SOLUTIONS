from rest_framework import permissions

class IsSeller(permissions.BasePermission):
    def has_permission(self, request, view):
        return request.user.groups.filter(name="Seller").exists()
    

class IsSellerOrReadOnly(permissions.BasePermission):
    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return True
        return request.user.groups.filter(name="Seller").exists()
    

class IsSellerOrStaffOrReadOnly(permissions.BasePermission):
    """ Permission class allows read access to all users, but only allows write access to sellers and staff. """
    def has_permission(self, request, view):
        # Allow read-only methods fro all users
        if request.method in permissions.SAFE_METHODS:
            return True
        
        # Allow create and other write operations only for sellers and staff
        return request.user.is_staff or request.user.groups.filter(name="Seller").exists()   
    
    def has_object_permission(self, request, view, obj):
        # Allow read-only methods for all users
        if request.method in permissions.SAFE_METHODS:
            return True
        # Allow write operations only for sellers (who own the object) and staff
        return request.user.is_staff or (hasattr(obj, "seller") and obj.seller == request.user)
    
    
class IsStaffOrReadOnly(permissions.BasePermission):
    """
    Custom permission to only allow staff members to edit transactions.
    """
    def has_permission(self, request, view):
        # Read permissions are allowed to any request,
        # so we'll always allow GET, HEAD or OPTIONS requests.
        if request.method in permissions.SAFE_METHODS:
            return True

        # Write permissions are only allowed to staff members.
        return request.user and request.user.is_staff

    def has_object_permission(self, request, view, obj):
        # Read permissions are allowed to any request,
        # so we'll always allow GET, HEAD or OPTIONS requests.
        if request.method in permissions.SAFE_METHODS:
            return True

        # Write permissions are only allowed to staff members.
        return request.user and request.user.is_staff

