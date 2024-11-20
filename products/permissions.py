from rest_framework import permissions
    

class IsSellerOrReadOnly(permissions.BasePermission):
    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return True
        
        # Check if user is authenticated
        if not request.user.is_authenticated:
            return False
        
        return request.user.is_seller()
    

class IsSellerOrStaffOrReadOnly(permissions.BasePermission):
    """ Permission class allows read access to all users, but only allows write access to sellers and staff. """
    def has_permission(self, request, view):
        # Allow read-only methods for all users
        if request.method in permissions.SAFE_METHODS:
            return True
        
        # Check if user is authenticated
        if not request.user.is_authenticated:
            return False
        
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
        
        # Check if user is authenticated
        if not request.user.is_authenticated:
            return False
        
        # Allow write operations only for sellers (who own the object) and staff
        return request.user.is_staff or obj.seller == request.user
    
