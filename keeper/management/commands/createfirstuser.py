import os
from django.conf import settings
from django.core.management.base import BaseCommand
from django.contrib.auth.models import User

class Command(BaseCommand):

    def handle(self, *args, **options):
        if User.objects.count() == 0:

            IP_VLAN_KEEPER_ADMIN_NAME = os.environ.get('IP_VLAN_KEEPER_ADMIN_NAME', 'admin')
            IP_VLAN_KEEPER_ADMIN_EMAIL = os.environ.get('IP_VLAN_KEEPER_ADMIN_EMAIL', 'ad@m.in')
            IP_VLAN_KEEPER_ADMIN_PASSWORD = os.environ.get('IP_VLAN_KEEPER_ADMIN_PASSWORD', 'admin')
            
            superuser = User.objects.create_superuser(
                username=IP_VLAN_KEEPER_ADMIN_NAME,
                email=IP_VLAN_KEEPER_ADMIN_EMAIL,
                password=IP_VLAN_KEEPER_ADMIN_PASSWORD)

            superuser.save()
        else:
            print('Admin accounts can only be initialized if no Accounts exist')
