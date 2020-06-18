from django.contrib.auth.models import User
from django.contrib.auth import authenticate
from .models import Device
from .models import DevInterface
from .models import Vlan
from .models import Ip
from .models import Log
from .models import Net
from .models import Ip_pool
from rest_framework import viewsets
from rest_framework.response import Response
from rest_framework.decorators import api_view, permission_classes
from .serializers import UserSerializer
from .serializers import DeviceSerializer
from .serializers import DevInterfaceSerializer
from .serializers import VlanSerializer
from .serializers import IpSerializer
from .serializers import LogSerializer
from .serializers import NetSerializer
from .serializers import Ip_poolSerializer
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.authtoken.models import Token
import ipaddress
from django.views.decorators.csrf import csrf_exempt
from rest_framework.permissions import AllowAny
import socket
import struct
import datetime

def ip_included_in_net(ip, network):
    return ipaddress.ip_address(ip) in ipaddress.ip_network(network)

def network_intercections_ckeck(network, networks):
    for net in networks:
        try:
            net = ipaddress.ip_network(net)
            network = ipaddress.ip_network(network)
            if net.overlaps(network) is True:
                return net
        except Exception as e:
            print("e {}".format(e))
            # TODO write it to Log as Notice

    return True

# @csrf_exempt
@api_view(["POST"])
@permission_classes((AllowAny,))
def login(request):
    username = request.data.get("username")
    password = request.data.get("password")
    if username is None or password is None:
        return Response({'error': 'Please provide both username and password'},
                        status=status.HTTP_400_BAD_REQUEST)
    user = authenticate(username=username, password=password)
    if not user:
        return Response({'error': 'Invalid Credentials'},
                        status=status.HTTP_404_NOT_FOUND)
    token, _ = Token.objects.get_or_create(user=user)
    return Response({'token': token.key },
                    status=status.HTTP_200_OK)

class GetAllNamesViewSet(viewsets.ViewSet):
    queryset =  {
        "Pool": Ip_pool.objects.values_list('Name', flat=True).order_by('IntNet'),
        "Network": Net.objects.values_list('Name', flat=True).order_by('IntNet'),
        "Device": Device.objects.values_list('Name', flat=True).order_by('Name'),
        "Device_interface": DevInterface.objects.values_list('Name', flat=False).order_by('Name'),
        "Vlan": Vlan.objects.values_list('Name', flat=True).order_by('Name'),
        "Owner": User.objects.values_list('username', flat=True).order_by('username')
    }

    def list(self, request):
        self.queryset =  {
            "Pool": Ip_pool.objects.values_list('Name', flat=True).order_by('IntNet'),
            "Network": Net.objects.values_list('Name', flat=True).order_by('IntNet'),
            "Device": Device.objects.values_list('Name', flat=True).order_by('Name'),
            "Device_interface": DevInterface.objects.values_list('Name', flat=False).order_by('Name'),
            "Vlan": Vlan.objects.values_list('Name', flat=True).order_by('Name'),
            "Owner": User.objects.values_list('username', flat=True).order_by('username')
        }
        return Response(self.queryset)

class UserViewSet(viewsets.ModelViewSet):
    serializer_class = UserSerializer
    queryset = User.objects.all().order_by('-date_joined')
    lookup_field = 'username'

    def list(self, request):
        serializer = self.get_serializer(self.queryset, many=True)
        return Response(serializer.data)

    def retrieve(self, request, username=None):
        self.queryset = User.objects.get(username=username)
        serializer = self.get_serializer([self.queryset], many=True)
        return Response(serializer.data)

class DeviceViewSet(viewsets.ModelViewSet):
    queryset = Device.objects.all().order_by('Name')
    serializer_class = DeviceSerializer
    lookup_field = 'Name'

    def list(self, request):
        self.queryset = Device.objects.all().order_by('Name')
        serializer = self.get_serializer(self.queryset, many=True)
        return Response(serializer.data)

    def create(self, request):
        try:
            device = Device(Name=request.data['Name'], Description=request.data.get('Description',""))
            device.save()

            serializer = self.get_serializer(device, many=False)
            return Response(serializer.data)
        except Exception as e:
            return Response({"Device is not created" : '{}'.format(e)},
                    status=status.HTTP_412_PRECONDITION_FAILED)          

    def retrieve(self, request, Name=None):
        try:
            Name = request.data.get('Name', Name)
            self.queryset = Device.objects.get(Name=Name)
            serializer = self.get_serializer([self.queryset], many=True)
            return Response(serializer.data)
        except Exception as e:
            return Response("An error occured when retrieve Device info: {}".format(e))

    def partial_update(self, request, Name=None):
        try:
            Name = request.data.get('Name', Name)
            device = Device.objects.filter(Name=Name).first()
            device.Name = request.data.get('NewName', Name)
            device.Description = request.data.get('Description', device.Description)
            device.save()

            serializer = self.get_serializer(device, many=False)
            return Response(serializer.data)
        except Exception as e:
            return Response({"Device is not updated" : '{}'.format(e)},
                    status=status.HTTP_412_PRECONDITION_FAILED)

    def destroy(self, request, Name=None):
        try:
            Name = request.data.get('Name', Name)
            Device.objects.filter(Name=Name).delete()
            response = self.list(request)
            return response
        except Exception as e:
            return Response({"Device is not deleted" : '{}'.format(e)},
                    status=status.HTTP_412_PRECONDITION_FAILED)

    def put(self, request, Name=None):
        response = self.update(request, Name)
        return response

    def patch(self, request, Name=None):
        response = self.partial_update(request, Name)
        return response

    def delete(self, request, Name=None):
        response = self.destroy(request, Name)
        return response

class Ip_poolViewSet(viewsets.ModelViewSet):
    queryset = Ip_pool.objects.all().order_by('IntNet')
    serializer_class = Ip_poolSerializer
    lookup_field = 'Name'

    def list(self, request):
        self.queryset = Ip_pool.objects.all().order_by('IntNet')
        serializer = self.get_serializer(self.queryset, many=True)
        return Response(serializer.data)

    def create(self, request):
        self.queryset = Ip_pool.objects.all().order_by('IntNet')
        Name = request.data['Name']
        not_overlapped = network_intercections_ckeck(request.data['Name'], self.queryset)

        if (not_overlapped is True):
            try:
                Owner = User.objects.get(username=request.data.get('Owner'))
                ip_pool = Ip_pool(Name=Name, Description=request.data.get('Description',""), Owner=Owner)
                ip_pool.save()

                ips = Ip.objects.all().order_by('IntIp')
                for ip in ips:
                    if(ip_included_in_net(ip.Name, Name) is True):
                        Ip.objects.filter(Name=ip.Name).update(Pool=ip_pool)

                serializer = self.get_serializer(ip_pool, many=False)
                return Response(serializer.data)
            except Exception as e:
                return Response({"Ip pool is not created" : '{}'.format(e)},
                        status=status.HTTP_412_PRECONDITION_FAILED)
        else:
            return Response({"ip pool is not created " : 'ip pool {} overlaps {}'.format(not_overlapped, Name)},
                    status=status.HTTP_412_PRECONDITION_FAILED)

    def retrieve(self, request, Name=None):
        try:
            Name = request.data.get('Name', Name)
            Name = str.replace(Name, "_", ".")
            Name = str.replace(Name, "|", "/")
            self.queryset = Ip_pool.objects.get(Name=Name)
            serializer = self.get_serializer([self.queryset], many=True)
            return Response(serializer.data)
        except Exception as e:
            return Response("An error occured when retrieve ip pool info: {}".format(e))

    def partial_update(self, request, Name=None):
        try:
            Name = request.data.get('Name', Name)
            ip_pool = Ip_pool.objects.filter(Name=Name).first()
            Owner = User.objects.get(username=request.data.get('Owner', ip_pool.Owner.username))
            ip_pool.Name = request.data.get('NewName', Name)
            ip_pool.Description = request.data.get('Description', ip_pool.Description)
            ip_pool.Owner = Owner

            ip_pool.save()
            serializer = self.get_serializer(ip_pool, many=False)
            return Response(serializer.data)
        except Exception as e:
            return Response({"Ip pool is not updated" : '{}'.format(e)},
                    status=status.HTTP_412_PRECONDITION_FAILED)

    def destroy(self, request, Name=None):
        try:
            Name = request.data.get('Name', Name)
            Ip_pool.objects.filter(Name=Name).delete()
            response = self.list(request)
            return response
        except Exception as e:
            return Response({"Ip pool is not deleted" : '{}'.format(e)},
                    status=status.HTTP_412_PRECONDITION_FAILED)

    def put(self, request, Name=None):
        response = self.update(request, Name)
        return response

    def patch(self, request, Name=None):
        response = self.partial_update(request, Name)
        return response

    def delete(self, request, Name=None):
        response = self.destroy(request, Name)
        return response

class NetViewSet(viewsets.ModelViewSet):
    queryset = Net.objects.all().order_by('IntNet')
    serializer_class = NetSerializer
    lookup_field = 'Name'

    @action(detail=True, methods=['get'])
    def free_addresses(self, request, Name=None):
        free_addrs =[]

        def get_free(addr, reserved):
            if (addr not in reserved):
                free_addrs.append(addr)

        try:
            Name = request.data.get("Name", Name)
            Name = str.replace(Name, "_", ".")
            Name = str.replace(Name, "|", "/")

            network = ipaddress.IPv4Network(Name)
            network_address = '{}'.format(network.network_address)

            if(network.netmask != ipaddress.IPv4Network('1.1.1.0/32').netmask):

                ips = Ip.objects.filter(Network=Name).values_list('Name', flat=True).order_by('IntIp')

                all_addresses = ['{}'.format(addr) for addr in network]

                [ get_free(addr, ips) for addr in all_addresses]

                if(len(free_addrs) >= 100):
                    free_addrs = free_addrs[:200]

            return Response({'free_ips': free_addrs})

        except Exception as e:
            return Response({"An error occured when retrieving free ips" : '{}'.format(e)},
                    status=status.HTTP_412_PRECONDITION_FAILED)

    def list(self, request):
        self.queryset = Net.objects.all().order_by('IntNet')
        serializer = self.get_serializer(self.queryset, many=True)
        return Response(serializer.data)

    def create(self, request):
        self.queryset = Net.objects.all().order_by('IntNet')
        Name = request.data['Name']
        Gateway = request.data.get('Gateway', "")
        not_overlapped = network_intercections_ckeck(request.data['Name'], self.queryset)
        
        try:
            gateway_included = ip_included_in_net(Gateway, Name)
        except Exception as e:
            return Response({"Gateway format failed" : '{}'.format(e)},
                    status=status.HTTP_412_PRECONDITION_FAILED)

        if (not_overlapped is True):
            if (gateway_included is True) :
                try:
                    Device_interface = DevInterface.objects.filter(Name=request.data.get('Device_interface')).first()
                    Owner = User.objects.get(username=request.data.get('Owner'))
                    Vlan_id = Vlan.objects.get(Name=int(request.data.get('Vlan')))
                    # gw_description = '/32'
                    net = Net(Name=Name, Gateway=Gateway,
                                Broadcast='[None]', Description=request.data.get('Description',""),
                                Vlan=Vlan_id, Device_interface=Device_interface, Owner=Owner)
                    net.save()
                    
                    if(ipaddress.ip_network(Name).netmask != ipaddress.ip_network('1.1.1.1/32').netmask):
                        Broadcast = '{}'.format(ipaddress.ip_network(Name).broadcast_address)
                        net.Broadcast = Broadcast
                        net.save()
                        bc = Ip(Name=Broadcast, Description='Broadcast', 
                                    Network=net, Device_interface=Device_interface)
                        bc.save()
                        
                        gw_description = 'Gateway'

                        gw = Ip(Name=net.Gateway, Description=gw_description, 
                                    Network=net, Device_interface=Device_interface)
                        gw.save()

                    na = Ip(Name='{}'.format(ipaddress.ip_network(Name).network_address),
                                Description='Network', Network=net,
                                Device_interface=Device_interface)
                    na.save()                    
     
                    serializer = self.get_serializer(net, many=False)
                    return Response(serializer.data)
                except Exception as e:
                    return Response({"Network is not created" : '{}'.format(e)},
                            status=status.HTTP_412_PRECONDITION_FAILED)

            else:
                return Response({"Gateway addres is not included in the Network "},
                    status=status.HTTP_412_PRECONDITION_FAILED)  

        else:
            return Response({"Network is not created " : 'Network {} overlaps {}'.format(not_overlapped, Name)},
                    status=status.HTTP_412_PRECONDITION_FAILED)            

    def retrieve(self, request, Name=None):
        try:
            Name = request.data.get('Name', Name)
            Name = str.replace(Name, "_", ".")
            Name = str.replace(Name, "|", "/")
            self.queryset = Net.objects.get(Name=Name)
            serializer = self.get_serializer([self.queryset], many=True)
            return Response(serializer.data)
        except Exception as e:
            return Response("An error occured when retrieve Net info: {}".format(e))

    def partial_update(self, request, Name=None):
        try:
            Name = request.data.get('Name', Name)
            net = Net.objects.filter(Name=Name).first()
            Device_interface = DevInterface.objects.filter(Name=request.data.get('Device_interface', net.Device_interface.Name)).first()
            Owner = User.objects.get(username=request.data.get('Owner', net.Owner.username))
            Vlan_id = Vlan.objects.get(Name=int(request.data.get('Vlan', net.Vlan.Name)))

            net.Name = request.data.get('NewName', Name)

            net.Description = request.data.get('Description', net.Description)
            net.Vlan = Vlan_id
            net.Device_interface = Device_interface
            net.Owner = Owner

            net.save()
            serializer = self.get_serializer(net, many=False)
            return Response(serializer.data)
        except Exception as e:
            return Response({"Network is not updated" : '{}'.format(e)},
                    status=status.HTTP_412_PRECONDITION_FAILED)

    def destroy(self, request, Name=None):
        try:
            Name = request.data.get('Name', Name)
            Net.objects.filter(Name=Name).delete()
            response = self.list(request)
            # Net.save()
            return response
        except Exception as e:
            return Response({"Network is not deleted" : '{}'.format(e)},
                    status=status.HTTP_412_PRECONDITION_FAILED)

    def put(self, request, Name=None):
        response = self.update(request, Name)
        return response

    def patch(self, request, Name=None):
        response = self.partial_update(request, Name)
        return response

    def delete(self, request, Name=None):
        response = self.destroy(request, Name)
        return response

class DevInterfaceViewSet(viewsets.ModelViewSet):
    queryset = DevInterface.objects.all().order_by('Name')
    serializer_class = DevInterfaceSerializer
    lookup_field = 'Name'

    def list(self, request):
        self.queryset = DevInterface.objects.all().order_by('Name')
        serializer = self.get_serializer(self.queryset, many=True)
        return Response(serializer.data)

    def create(self, request):
        try:
            Device_id = Device.objects.get(Name=request.data.get('Device'))
            Owner = User.objects.get(username=request.data.get('Owner'))

            device_interface = DevInterface(Name=request.data['Name'],
                        Description=request.data.get('Description',""), Device=Device_id, Owner=Owner)
            device_interface.save()

            serializer = self.get_serializer(device_interface, many=False)
            return Response(serializer.data)
        except Exception as e:
            return Response({"device_interface is not created" : '{}'.format(e)},
                    status=status.HTTP_412_PRECONDITION_FAILED)

    def retrieve(self, request, Name=None):
        try:
            Name = request.data.get('Name', Name)
            Name = str.replace(Name, "|", "/")
            Name = str.replace(Name, "_", "/")
            self.queryset = DevInterface.objects.get(Name=Name)
            serializer = self.get_serializer([self.queryset], many=True)
            return Response(serializer.data)
        except Exception as e:
            return Response("An error occured when retrieve DeviceInterface info: {}".format(e))

    def partial_update(self, request, Name=None):
        try:
            Name = request.data.get('Name', Name)
            Name = str.replace(Name, "|", "/")
            Name = str.replace(Name, "_", "/")
            device_interface = DevInterface.objects.filter(Name=Name).first()
            Device_id = Device.objects.get(Name=request.data.get('Device', device_interface.Device.Name))
            Owner = User.objects.get(username=request.data.get('Owner', device_interface.Owner.username))
            device_interface.Name = request.data.get('NewName', Name)
            device_interface.Description = request.data.get('Description', device_interface.Description)
            device_interface.Device = Device_id
            device_interface.Owner = Owner

            device_interface.save()

            serializer = self.get_serializer(device_interface, many=False)
            return Response(serializer.data)
        except Exception as e:
            return Response({"device_interface is not updated" : '{}'.format(e)},
                    status=status.HTTP_412_PRECONDITION_FAILED)

    def destroy(self, request, Name=None):
        try:
            Name = request.data.get('Name', Name)
            Name = str.replace(Name, "|", "/")
            Name = str.replace(Name, "_", "/")
            DevInterface.objects.filter(Name=Name).delete()
            response = self.list(request)
            return response
        except Exception as e:
            return Response({"device_interface is not deleted" : '{}'.format(e)},
                    status=status.HTTP_412_PRECONDITION_FAILED)

    def put(self, request, Name=None):
        response = self.update(request, Name)
        return response

    def patch(self, request, Name=None):
        response = self.partial_update(request, Name)
        return response

    def delete(self, request, Name=None):
        response = self.destroy(request, Name)
        return response

class VlanViewSet(viewsets.ModelViewSet):
    queryset = Vlan.objects.all().order_by('Name')
    serializer_class = VlanSerializer
    lookup_field = 'Name'

    def list(self, request):
        self.queryset = Vlan.objects.all().order_by('Name')
        serializer = self.get_serializer(self.queryset, many=True)
        return Response(serializer.data)

    def create(self, request):
        try:
            Owner = User.objects.get(username=request.data.get('Owner'))

            vlan = Vlan(Name=request.data['Name'], Description=request.data.get('Description',""), Owner=Owner)
            vlan.save()

            serializer = self.get_serializer(vlan, many=False)
            return Response(serializer.data)
        except Exception as e:
            return Response({"vlan is not created" : '{}'.format(e)},
                    status=status.HTTP_412_PRECONDITION_FAILED)

    def retrieve(self, request, Name=None):

        try:
            Name = int(request.data.get('Name', Name))
            self.queryset = Vlan.objects.get(Name=Name)
            serializer = self.get_serializer([self.queryset], many=True)
            return Response(serializer.data)
        except Exception as e:
            return Response("An error occured when retrieve Device info: {}".format(e))

    def partial_update(self, request, Name=None):
        try:
            Name = request.data.get('Name', Name)
            vlan = Vlan.objects.filter(Name=request.data['Name']).first()
            # Device_id = Device.objects.get(Name=request.data.get('Device', device_interface.Device.Name))
            Owner = User.objects.get(username=request.data.get('Owner', vlan.Owner.username))
            vlan.Name = request.data.get('NewName', request.data['Name'])
            vlan.Description = request.data.get('Description', vlan.Description)
            # vlan.Device = Device_id
            vlan.Owner = Owner

            vlan.save()

            serializer = self.get_serializer(vlan, many=False)
            return Response(serializer.data)
        except Exception as e:
            return Response({"vlan is not updated" : '{}'.format(e)},
                    status=status.HTTP_412_PRECONDITION_FAILED)

    def destroy(self, request, Name=None):
        try:
            Name = request.data.get('Name', Name)
            Vlan.objects.filter(Name=Name).delete()
            response = self.list(request)
            return response
        except Exception as e:
            return Response({"vlan is not deleted" : '{}'.format(e)},
                    status=status.HTTP_412_PRECONDITION_FAILED)

    def put(self, request, Name=None):
        response = self.update(request, Name)
        return response

    def patch(self, request, Name=None):
        response = self.partial_update(request, Name)
        return response

    def delete(self, request, Name=None):
        response = self.destroy(request, Name)
        return response

class IpViewSet(viewsets.ModelViewSet):
    queryset = Ip.objects.all().order_by('IntIp')
    serializer_class = IpSerializer
    lookup_field = 'Name'

    def list(self, request):
        self.queryset = Ip.objects.all().order_by('IntIp')
        serializer = self.get_serializer(self.queryset, many=True)
        return Response(serializer.data)

    def create(self, request):
        try:
            Net_id = Net.objects.get(Name=request.data.get('Net'))
            Device_interface = DevInterface.objects.filter(Name=request.data.get('Device_interface')).first()
            Name = request.data['Name']

            if ip_included_in_net(request.data['Name'], Net_id.Name):

                int_ip = struct.unpack("!I", socket.inet_aton(Name))[0]

                ip = Ip(Name=Name, IntIp=int_ip ,Description=request.data.get('Description',""), 
                        Network=Net_id, Device_interface=Device_interface)
                ip.save()

                serializer = self.get_serializer(ip, many=False)
                return Response(serializer.data)
            else:
                return Response({"ip is not created" : 'ip is not included in the network'},
                    status=status.HTTP_412_PRECONDITION_FAILED)
        except Exception as e:
            return Response({"ip is not created" : '{}'.format(e)},
                    status=status.HTTP_412_PRECONDITION_FAILED)

    def retrieve(self, request, Name=None):
        try:
            is_pool = False
            Name = request.data.get("Name", Name)

            if(str.startswith(Name, "Pool_")):
                is_pool = True
                Name = str.replace(Name, "Pool_", "")

            Name = str.replace(Name, "_", ".")
            Name = str.replace(Name, "|", "/")

            if(is_pool is True):
                pool = Ip_pool.objects.get(Name=Name)
                user = User.objects.get(pk=1)

                self.queryset = []
                first = Ip(Name=pool.First,
                           Pool=pool,
                           Owner=user,
                           updated_at=datetime.datetime.now(),
                           Description="First_address_of_the_pool")
                last = Ip(Name=pool.Last,
                          Pool=pool,
                          Owner=user,
                          updated_at=datetime.datetime.now(),
                          Description="Last_address_of_the_pool")

                self.queryset = Ip.objects.filter(Pool=Name).order_by('IntIp')
                first_ser = self.get_serializer([first], many=True)
                serializer = self.get_serializer(self.queryset, many=True)
                last_ser = self.get_serializer([last], many=True)
                data = first_ser.data + serializer.data + last_ser.data

                return Response(data=data)
            else:
                self.queryset = Ip.objects.filter(Network=Name).order_by('IntIp')
                serializer = self.get_serializer(self.queryset, many=True)
                return Response(serializer.data)
        except Exception as e:
            return Response("An error occured when retrieve IP adresses info: {}".format(e))

    def partial_update(self, request, Name=None):
        try:
            Name = request.data.get("Name", Name)
            Name = str.replace(Name, "_", ".")
            ip = Ip.objects.filter(Name=request.data['Name']).first()
            Device_interface = DevInterface.objects.filter(Name=request.data.get('Device_interface', ip.Device_interface)).first()
            Net_id = Net.objects.get(Name=request.data.get('Network', ip.Network))
            
            if ip_included_in_net(request.data['Name'], Net_id.Name):
                ip.Name = request.data.get('NewName', request.data['Name'])
                ip.Description = request.data.get('Description', ip.Description)
                ip.Device_interface = Device_interface
                ip.Network = Net_id

                ip.save()

                serializer = self.get_serializer(ip, many=False)
                return Response(serializer.data)
            else:
                return Response({"ip is not updated" : 'ip is not included in the network'},
                    status=status.HTTP_412_PRECONDITION_FAILED)
        except Exception as e:
            return Response({"ip is not updated" : '{}'.format(e)},
                    status=status.HTTP_412_PRECONDITION_FAILED)

    def destroy(self, request, Name=None):
        try:
            Name = request.data.get("Name", Name)
            Name = str.replace(Name, "_", ".")
            Ip.objects.filter(Name=Name).delete()
            response = self.list(request)
            return response
        except Exception as e:
            return Response({"ip is not deleted" : '{}'.format(e)},
                    status=status.HTTP_412_PRECONDITION_FAILED)

    def put(self, request, Name=None):
        response = self.update(request, Name)
        return response

    def patch(self, request, Name=None):
        response = self.partial_update(request, Name)
        return response

    def delete(self, request, Name=None):
        response = self.destroy(request, Name)
        return response