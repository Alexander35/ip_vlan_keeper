from django.contrib import admin

# Register your models here.

from keeper.models import Ip
from keeper.models import Device
from keeper.models import DevInterface
from keeper.models import Vlan
from keeper.models import Log
from keeper.models import Net
from keeper.models import Ip_pool

admin.site.register(Ip)
admin.site.register(Device)
admin.site.register(DevInterface)
admin.site.register(Vlan)
admin.site.register(Log)
admin.site.register(Net)
admin.site.register(Ip_pool)