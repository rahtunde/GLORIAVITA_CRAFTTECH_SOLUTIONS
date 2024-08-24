from rest_framework import permissions

# Not used: Delete
class IsSeller(permissions.BasePermission):
    def has_permission(self, request, view):
        return request.user.groups.filter(name="Seller").exists()
    
# Check through your permissions; for user that needs to be authenticated add 
# `request.user.is_authenticated and ...`, so that you do not perform a filter on a non-authenticated user
class IsSellerOrReadOnly(permissions.BasePermission):
    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return True
        return request.user.is_seller()
    

class IsSellerOrStaffOrReadOnly(permissions.BasePermission):
    """ Permission class allows read access to all users, but only allows write access to sellers and staff. """
    def has_permission(self, request, view):
        # Allow read-only methods fro all users
        if request.method in permissions.SAFE_METHODS:
            return True
        
        # Allow create and other write operations only for sellers and staff
        return request.user.is_staff or request.user.is_seller()
    
    def has_object_permission(self, request, view, obj):
        """
        Check object permission of product
        
        Args:
            request: HTTP Request
            view: ...
            obj (Product): the product instance we would check permission against
        """
        # Allow read-only methods for all users
        if request.method in permissions.SAFE_METHODS:
            return True
        return request.user.is_staff or obj.seller == request.user
    
    
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
        return request.user.is_authenticated and request.user.is_staff

    # Remove this has this does not check any obj constraints or permission
    def has_object_permission(self, request, view, obj):
        # Read permissions are allowed to any request,
        # so we'll always allow GET, HEAD or OPTIONS requests.
        if request.method in permissions.SAFE_METHODS:
            return True

        # Write permissions are only allowed to staff members.
        return request.user and request.user.is_staff

