from rest_framework import serializers
from django.contrib.auth.models import User
from .models import Device
from .models import DevInterface
from .models import Vlan
from .models import Ip
from .models import Log
from .models import Net

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['username']

class DeviceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Device
        exclude = ['created_at']

class DevInterfaceSerializer(serializers.ModelSerializer):
    Owner = UserSerializer()
    Device = DeviceSerializer()

    class Meta:
        model = DevInterface
        fields = ['Name', 'Description', 'Owner', 'Device']

class VlanSerializer(serializers.ModelSerializer):
    Owner = UserSerializer()
    class Meta:
        model = Vlan
        exclude = ['created_at']

class NetSerializer(serializers.ModelSerializer):
    Vlan = VlanSerializer()
    Device_interface = DevInterfaceSerializer()
    Owner = UserSerializer()
    class Meta:
        model = Net
        exclude = ['created_at', 'IntNet']

class IpSerializer(serializers.ModelSerializer):
    Network = NetSerializer()
    Device_interface = DevInterfaceSerializer()
    Owner = UserSerializer()
    class Meta:
        model = Ip
        exclude = ['created_at', 'IntIp']

class LogSerializer(serializers.ModelSerializer):
    class Meta:
        model = Log
        exclude = ['created_at']

