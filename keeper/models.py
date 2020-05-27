from django.db import models
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
import ipaddress
import socket
import struct

class Device(models.Model): 
    Name = models.CharField(max_length=100, primary_key=True)
    Description = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
       return self.Name

class DevInterface(models.Model):
    Name = models.CharField(max_length=100, unique=True)
    Description = models.TextField()
    Owner = models.ForeignKey(User, on_delete=models.CASCADE)
    Device = models.ForeignKey(Device, on_delete=models.CASCADE, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def save(self):
        if ('::' not in self.Name):
            self.Name = "{} :: {}".format(self.Name, self.Device.Name)
        super(DevInterface, self).save()

    def __str__(self):
       return "{} :: {}".format(self.Name, self.Device.Name)

class Vlan(models.Model):
    Name = models.PositiveIntegerField(default=0, primary_key=True)
    Description = models.TextField()
    Owner = models.ForeignKey(User, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
       return '{} {}'.format(self.Name, self.Description)

class Net(models.Model):
    Name = models.CharField(max_length=100, primary_key=True)
    Gateway = models.CharField(max_length=100)
    Broadcast = models.CharField(max_length=100)
    Vlan = models.ForeignKey(Vlan, on_delete=models.CASCADE)
    Device_interface = models.ForeignKey(DevInterface, on_delete=models.CASCADE)
    Description = models.TextField()
    Owner = models.ForeignKey(User, on_delete=models.CASCADE)
    IntNet =  models.CharField(max_length=100)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def save(self):
        net_addr = '{}'.format(ipaddress.ip_network(self.Name).network_address)
        self.IntNet = '{}'.format( struct.unpack("!I", socket.inet_aton(net_addr))[0])
        super(Net, self).save()

    def __str__(self):
       return '{}'.format(self.Name)

class Ip(models.Model): 
    Name = models.CharField(max_length=100, primary_key=True)
    Network = models.ForeignKey(Net, on_delete=models.CASCADE)
    Device_interface = models.ForeignKey(DevInterface, on_delete=models.CASCADE)
    Description = models.TextField()
    IntIp =  models.CharField(max_length=100)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def save(self):
        self.IntIp = '{}'.format( struct.unpack("!I", socket.inet_aton(self.Name))[0])
        super(Ip, self).save()

    def __str__(self):
       return self.Name + self.Description

class Log(models.Model):
    Name = models.CharField(max_length=100)
    Description = models.TextField()
    Owner = models.ForeignKey(User, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)