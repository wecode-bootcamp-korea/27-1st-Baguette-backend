import json

from decimal                        import Decimal
from django.core.checks             import messages
from django.core.exceptions         import ValidationError
from django.db.models               import Sum
from django.http                    import JsonResponse
from django.views                   import View

from shops.models                   import Cart, Option
from packages.models                import Package
from users.models                   import User
from core.utils.decorator           import decorator


class CartView(View):
    @decorator
    def post(self, request):
        try:
            data            = json.loads(request.body)
            user            = request.user
            quantity        = data["quantity"]
            price           = data["price"]
            package_id      = data["package_id"] 
            shipping_option = data["shipping_option"]
            option          = Option.objects.get(shipping_option=shipping_option).id 
            
            if int(quantity) < 1 :
                return JsonResponse({'message':'DESELECTED_QUANTITY'}, status=400)
            
            cart, created = Cart.objects.get_or_create(
                    user            = user,
                    package_id      = package_id,
                    defaults={
                            'quantity': quantity,
                            'price'   : price,
                            'shipping_option_id':option}
                    )

            cart.quantity += quantity
            cart.price    += price
            cart.save()
                
            return JsonResponse({'result':'ADD_CART'}, status = 201)
        
        except ValidationError as e:
            return JsonResponse({'message':e.message}, status = 400)

        except KeyError:
            return JsonResponse({'message':'KEY_ERROR'}, status=400)
    
    @decorator
    def get(self, request):
        try:
            user        = request.user
            carts       = Cart.objects.filter(user = user.id)
            total       = carts.values('price')
            total_price = total.aggregate(total_price=Sum('price'))
            
            result=[{
                'total_price' : total_price,
                'cart'        :[{
                    'id'        : cart.id,
                    'image'     : cart.package.thumbnail_image, 
                    'name'      : cart.package.name, 
                    'price'     : cart.price,
                    'quantity'  : cart.quantity,
                    'option'    : cart.shipping_option.shipping_option 
                    } for cart in carts],
                }]
            return JsonResponse({'result':result}, status = 200)

        except ValidationError as e:
            return JsonResponse({'message':e.message}, status = 401)

    @decorator
    def delete(self, request):
        try:
            data      = json.loads(request.body)
            cart_list = data['id']
            carts     = Cart.objects.filter(id__in=cart_list)

            carts.delete()

            return JsonResponse({'result':'DELETE_CART'}, status = 200)
        
        except ValidationError as e:
            return JsonResponse({'message':e.message}, status = 401)

    @decorator
    def patch(self, request): 
        try:
            data        = json.loads(request.body)
            quantity    = data['quantity']
            id          = data['id']
            
            if int(quantity) < 1:
                return JsonResponse({'messages':'DESELECTED_QUANTITY'}, status = 400)

            cart          = Cart.objects.get(id=id)
            price         = cart.package.price
            
            cart.quantity = quantity
            cart.price    = Decimal(int(cart.quantity) * int(price))
            cart.save()    
                
            return JsonResponse({'result':'QUANTITY_IN_CART'}, status = 200)
        
        except ValidationError as e:
            return JsonResponse({'message':e.message}, status = 401)
           