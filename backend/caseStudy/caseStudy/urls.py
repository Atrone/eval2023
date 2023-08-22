from django.views.generic import TemplateView
from myapp import views
from django.urls import path, re_path

urlpatterns = [
    path('send_bitcoin/', views.get_transaction_data, name='send_testnet_bitcoin'),
    path('broadcast_bitcoin/', views.broadcast_signed_transaction, name='broadcast_signed_transaction'),
    path('get_confirmations/', views.get_confirmations, name='get_confirmations'),
    path('path/to/get_addresses_endpoint/', views.get_addresses, name='get_books'),
    path('path/to/create_address_endpoint/', views.create_address, name='create_book'),
    path('api/path-to-details/<str:bookId>/', views.get_address_details, name='get_book_details'),
    re_path(r'^.*$', TemplateView.as_view(template_name="index.html")),
]
