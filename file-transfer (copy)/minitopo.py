#!/usr/bin/env python
from mininet.net import Mininet
from mininet.topo import Topo
from mininet.cli import CLI
from mininet.log import setLogLevel, info
from mininet.link import TCLink
from mininet.node import RemoteController, OVSKernelSwitch, Host
import os
import time

class CustomHost(Host):
    def config(self, **params):
        r = super(CustomHost, self).config(**params)
        return r

class MultiPathTopo(Topo):
    def build(self):
        # Create hosts
        client = self.addHost('client')
        server = self.addHost('server')
        router = self.addHost('router')
        
        # Create switches
        sw0 = self.addSwitch('sw0')
        sw1 = self.addSwitch('sw1')
        
        # Link 0: Client-eth0 to sw0 to Router-eth0
        self.addLink(client, sw0,
                    intfName1='Client-eth0',
                    # intfName2='sw0-eth1',
                    # params1={'ip': '10.0.0.1/24'},
                    cls=TCLink)
        
        self.addLink(sw0, router,
                    # intfName1='sw0-eth2',
                    intfName2='Router-eth0',
                    # params2={'ip': '10.0.0.2/24'},
                    cls=TCLink)
        
        # Link 1: Client-eth1 to sw1 to Router-eth1
        self.addLink(client, sw1,
                    intfName1='Client-eth1',
                    # intfName2='sw1-eth1',
                    # params1={'ip': '10.0.1.1/24'},
                    cls=TCLink)
        
        self.addLink(sw1, router,
                    # intfName1='sw1-eth2',
                    intfName2='Router-eth1',
                    # params2={'ip': '10.0.1.2/24'},
                    cls=TCLink)
        
        # Server link
        self.addLink(router, server,
                    intfName1='Router-eth2',
                    params1={'ip': '10.1.0.2/24'},
                    intfName2='Server-eth0',
                    params2={'ip': '10.1.0.1/24'})

def configure_network(net):
    """Configure network interfaces, ARP, and routing"""
    client = net.get('client')
    server = net.get('server')
    router = net.get('router')
    sw0 = net.get('sw0')
    sw1 = net.get('sw1')
    
    print("[Phase 1] Configuring network interfaces and ARP")
    
    # First bring up interfaces
    client.cmd('ifconfig Client-eth0 10.0.0.1 netmask 255.255.255.0')
    # client.cmd('route add default gw 10.0.0.2')
    router.cmd('ifconfig Router-eth0 10.0.0.2 netmask 255.255.255.0')
    
    client.cmd('ifconfig Client-eth1 10.0.1.1 netmask 255.255.255.0')
    # client.cmd('route add default gw 10.0.1.2')
    router.cmd('ifconfig Router-eth1 10.0.1.2 netmask 255.255.255.0')
    
    router.cmd('ifconfig Router-eth2 10.1.0.2 netmask 255.255.255.0')
    server.cmd('ifconfig Server-eth0 10.1.0.1 netmask 255.255.255.0')
    
    # Get MAC addresses after interfaces are up
    print("Getting MAC addresses...")
    
    # Get Client MAC addresses
    client_eth0_mac = client.cmd("ifconfig Client-eth0 | grep -o -E '([[:xdigit:]]{1,2}:){5}[[:xdigit:]]{1,2}' | head -1").strip()
    client_eth1_mac = client.cmd("ifconfig Client-eth1 | grep -o -E '([[:xdigit:]]{1,2}:){5}[[:xdigit:]]{1,2}' | head -1").strip()
    
    # Get Router MAC addresses
    router_eth0_mac = router.cmd("ifconfig Router-eth0 | grep -o -E '([[:xdigit:]]{1,2}:){5}[[:xdigit:]]{1,2}' | head -1").strip()
    router_eth1_mac = router.cmd("ifconfig Router-eth1 | grep -o -E '([[:xdigit:]]{1,2}:){5}[[:xdigit:]]{1,2}' | head -1").strip()
    router_eth2_mac = router.cmd("ifconfig Router-eth2 | grep -o -E '([[:xdigit:]]{1,2}:){5}[[:xdigit:]]{1,2}' | head -1").strip()
    
    # Get Server MAC address
    server_eth0_mac = server.cmd("ifconfig Server-eth0 | grep -o -E '([[:xdigit:]]{1,2}:){5}[[:xdigit:]]{1,2}' | head -1").strip()
    
    print("Client-eth0 MAC:", client_eth0_mac)
    print("Client-eth1 MAC:", client_eth1_mac)
    print("Router-eth0 MAC:", router_eth0_mac)
    print("Router-eth1 MAC:", router_eth1_mac)
    print("Router-eth2 MAC:", router_eth2_mac)
    print("Server-eth0 MAC:", server_eth0_mac)
    
    # Configure static ARP entries using actual MAC addresses
    print("\nConfiguring static ARP entries...")
    
    # Path 0: Client <-> Router
    print("Router: arp -s 10.0.0.1 " + client_eth0_mac)
    router.cmd('arp -s 10.0.0.1 ' + client_eth0_mac)
    
    print("Client: arp -s 10.0.0.2 " + router_eth0_mac)
    client.cmd('arp -s 10.0.0.2 ' + router_eth0_mac)
    
    # Path 1: Client <-> Router
    print("Router: arp -s 10.0.1.1 " + client_eth1_mac)
    router.cmd('arp -s 10.0.1.1 ' + client_eth1_mac)
    
    print("Client: arp -s 10.0.1.2 " + router_eth1_mac)
    client.cmd('arp -s 10.0.1.2 ' + router_eth1_mac)
    
    # Server <-> Router
    print("Server: arp -s 10.1.0.2 " + router_eth2_mac)
    server.cmd('arp -s 10.1.0.2 ' + router_eth2_mac)
    
    print("Router: arp -s 10.1.0.1 " + server_eth0_mac)
    router.cmd('arp -s 10.1.0.1 ' + server_eth0_mac)
    
    print("[Phase 2] Configuring routing tables")
    
    # Clear existing routes
    # client.cmd('ip route flush table main')
    # client.cmd('ip rule flush')
    
    # Table 1: traffic from 10.0.0.1
    client.cmd('ip rule add from 10.0.0.1 table 1')
    client.cmd('ip route add 10.0.0.0/24 dev Client-eth0 scope link table 1')
    client.cmd('ip route add 10.1.0.0/24 via 10.0.0.2 dev Client-eth0 table 1')
    
    # Table 2: traffic from 10.0.1.1
    client.cmd('ip rule add from 10.0.1.1 table 2')
    client.cmd('ip route add 10.0.1.0/24 dev Client-eth1 scope link table 2')
    client.cmd('ip route add 10.1.0.0/24 via 10.0.1.2 dev Client-eth1 table 2')
    
    # Default route
    client.cmd('ip route add default scope global nexthop via 10.0.0.2 dev Client-eth0')
    
    # Server routing
    server.cmd('ip route add default via 10.1.0.2')
    
    # Router configuration
    router.cmd('sysctl -w net.ipv4.ip_forward=1')
    # router.cmd('ip route add 10.0.0.0/24 dev Router-eth0')
    # router.cmd('ip route add 10.0.1.0/24 dev Router-eth1')
    # router.cmd('ip route add 10.1.0.0/24 dev Router-eth2')
    
    # Show ARP tables
    print("\nARP tables after configuration:")
    print("Client ARP table:")
    print(client.cmd('arp -n'))
    print("\nRouter ARP table:")
    print(router.cmd('arp -n'))
    print("\nServer ARP table:")
    print(server.cmd('arp -n'))
    
    return client, server, router, sw0, sw1

def configure_tcp_optimization(host, host_type="mininet"):
    """Configure TCP/MPTCP optimization parameters"""
    if host_type == "not_ns":
        print("[Not_NS] Configuring TCP optimization on physical host")
        cmds = [
            'sysctl -w net.ipv4.tcp_early_retrans="3"',
            'sysctl -w net.ipv4.tcp_congestion_control="olia"',
            'sysctl -w net.ipv4.tcp_autocorking="1"',
            'sysctl -w net.ipv4.tcp_rmem="10240 87380 16777216"',
            'sysctl -w net.mptcp.mptcp_scheduler="default"',
            'sysctl -w net.ipv4.tcp_moderate_rcvbuf="1"',
            'sysctl -w net.mptcp.mptcp_path_manager="fullmesh"',
            'sysctl -w net.ipv4.tcp_wmem="4096 16384 4194304"',
        ]
        for cmd in cmds:
            os.system(cmd)
    else:
        print("[%s] Configuring TCP optimization" % host.name)
        cmds = [
            'sysctl -w net.ipv4.tcp_early_retrans="3"',
            'sysctl -w net.ipv4.tcp_congestion_control="olia"',
            'sysctl -w net.ipv4.tcp_autocorking="1"',
            'sysctl -w net.ipv4.tcp_rmem="10240 87380 16777216"',
            'sysctl -w net.mptcp.mptcp_scheduler="default"',
            'sysctl -w net.ipv4.tcp_moderate_rcvbuf="1"',
            'sysctl -w net.mptcp.mptcp_path_manager="fullmesh"',
            'sysctl -w net.ipv4.tcp_wmem="4096 16384 4194304"',
        ]
        for cmd in cmds:
            host.cmd(cmd)

def disable_tso(host, interface):
    """Disable TCP Segmentation Offload"""
    print("[%s] Disabling TSO on %s" % (host.name, interface))
    host.cmd('ethtool -K %s tso off' % interface)

def configure_tc_parameters(net):
    """Configure traffic control parameters"""
    client = net.get('client')
    server = net.get('server')
    router = net.get('router')
    sw0 = net.get('sw0')
    sw1 = net.get('sw1')
    
    print("[Phase 3] Configuring traffic control")
    
    # Start packet capture
    print("[Client] Starting packet capture")
    client.cmd('tcpdump -i any -s 100 -w client.pcap > /dev/null 2>&1 &')
    print("[Server] Starting packet capture")
    server.cmd('tcpdump -i any -s 100 -w server.pcap > /dev/null 2>&1 &')
    
    time.sleep(5)
    
    # Disable TSO on all interfaces (as per your script)
    # Note: In your script, sw0-eth2 connects to Router-eth0
    disable_tso(sw0, 'sw0-eth2')
    disable_tso(router, 'Router-eth0')
    disable_tso(sw1, 'sw1-eth2')
    disable_tso(router, 'Router-eth1')
    disable_tso(server, 'Server-eth0')
    disable_tso(router, 'Router-eth2')
    
    # Configure TC parameters with delays
    time.sleep(0.1)
    
    # Path 0: sw0 links
    # sw0-eth1 connects to Client-eth0
    sw0.cmd('tc qdisc add dev sw0-eth1 root handle 1:0 netem loss 0.7%% delay 200ms 10ms')
    # sw0-eth2 connects to Router-eth0
    sw0.cmd('tc qdisc del dev sw0-eth2 root')
    sw0.cmd('tc qdisc add dev sw0-eth2 root netem loss 0.7%% delay 200ms 10ms')
    
    # Path 0: Client and Router interfaces
    client.cmd('tc qdisc add dev Client-eth0 root handle 1:0 tbf rate 15mbit burst 15000 latency 1ms')
    router.cmd('tc qdisc del dev Router-eth0 root')
    router.cmd('tc qdisc add dev Router-eth0 root handle 1:0 tbf rate mbit burst 15000 latency 1ms')
    
    # Path 1: sw1 links
    # sw1-eth1 connects to Client-eth1
    sw1.cmd('tc qdisc add dev sw1-eth1 root handle 1:0 netem loss 1.9%% delay 200ms 10ms')
    # sw1-eth2 connects to Router-eth1
    sw1.cmd('tc qdisc del dev sw1-eth2 root')
    sw1.cmd('tc qdisc add dev sw1-eth2 root netem loss 1.9%% delay 200ms 10ms')
    
    # Path 1: Client and Router interfaces
    client.cmd('tc qdisc add dev Client-eth1 root handle 1:0 tbf rate 10mbit burst 15000 latency 1ms')
    router.cmd('tc qdisc del dev Router-eth1 root')
    router.cmd('tc qdisc add dev Router-eth1 root handle 1:0 tbf rate 10mbit burst 15000 latency 1ms')

def run_ping_tests(client):
    """Run ping tests"""
    print("[Phase 4] Running ping tests")
    
    # Remove old ping log
    client.cmd('rm -f ping.log')
    
    # Ping via path 0
    print("[Client] Pinging via 10.0.0.1")
    client.cmd('ping -c 5 -I 10.0.0.1 10.1.0.1 >> ping.log 2>&1')
    
    # Ping via path 1
    print("[Client] Pinging via 10.0.1.1")
    client.cmd('ping -c 5 -I 10.0.1.1 10.1.0.1 >> ping.log 2>&1')
    
    # Show ping results
    print("\nPing test results:")
    print(client.cmd('cat ping.log'))

def run_experiments(client, server, rounds, timeout):
    """
    Automatically run multiple client-server experiments in Mininet.
    """

    server_bin = "./server/server-multipath"
    client_bin = "./client/client-multipath"
    print("\n[Phase X] Running automated experiments")
    print("Rounds:", rounds)

    for i in range(1, rounds + 1):
        print("\n" + "-" * 50)
        print("[Round %d] Starting server" % i)

        # sever listening
        # server.cmd("%s > server_%d.log 2>&1 &" % (server_bin, i))
        server.cmd("%s &" % server_bin)

        time.sleep(1)

        print("[Round %d] Starting client" % i)

        # client.cmd("EXP_ROUND=%d %s > client_%d.log 2>&1 &" % (i, client_bin, i))
        client.cmd("EXP_ROUND=%d %s &" % (i, client_bin))

        time.sleep(timeout)

        # clean client / server
        client.cmd("pkill -f client-multipath")
        server.cmd("pkill -f server-multipath")
        
        print("[Round %d] Done" % i)

def main():
    # Clean up existing processes
    print("Cleaning up existing Mininet processes")
    os.system('sudo mn -c 2>/dev/null')
    os.system('sudo pkill -f controller 2>/dev/null')
    
    # Configure physical host (Not_NS) TCP optimization
    configure_tcp_optimization(None, "not_ns")
    
    # Create network with custom controller port (6633 to avoid conflict)
    print("\nCreating network with controller port 6633")
    topo = MultiPathTopo()
    net = Mininet(topo=topo,
                #   switch=OVSKernelSwitch,
                #   controller=lambda name: RemoteController(name, ip='127.0.0.1', port=6633),
                  link=TCLink,
                  autoSetMacs=True)
    
    net.start()
    
    # Configure network (including ARP with actual MAC addresses)
    client, server, router, sw0, sw1 = configure_network(net)
    
    # Configure Mininet hosts TCP optimization
    configure_tcp_optimization(client, "mininet")
    configure_tcp_optimization(server, "mininet")
    
    # Run initial ping tests
    # run_ping_tests(client)
    
    # # Configure traffic control
    configure_tc_parameters(net)
    
    # Run ping tests after TC configuration
    # print("\n[Phase 5] Running ping tests after TC configuration")
    # client.cmd('ping -c 5 -I 10.0.0.1 10.1.0.1 >> ping.log 2>&1')
    # client.cmd('ping -c 5 -I 10.0.1.1 10.1.0.1 >> ping.log 2>&1')
    
    # # Show final ping results
    # print("\nFinal ping test results:")
    # print(client.cmd('tail -10 ping.log'))
    
    # # Show TC configuration
    # print("\nTraffic control configuration:")
    # print("Client TC:")
    # print(client.cmd('tc qdisc show'))
    # print("\nRouter TC:")
    # print(router.cmd('tc qdisc show'))
    # print("\nSwitch sw0 TC:")
    # print(sw0.cmd('tc qdisc show'))
    # print("\nSwitch sw1 TC:")
    # print(sw1.cmd('tc qdisc show'))
    
    # Enter CLI for manual testing
    # print("\n" + "="*60)
    # print("Entering Mininet CLI")
    # print("="*60)
    # print("\nTest commands you can use:")
    # print("  client ping -c 3 -I 10.0.0.1 server")
    # print("  client ping -c 3 -I 10.0.1.1 server")
    # print("  client tc qdisc show")
    # print("  router tc qdisc show")

    CLI(net)
    # run_experiments(client, server, rounds=50, timeout=20)
    
    # Cleanup
    print("\nCleaning up...")
    client.cmd('killall tcpdump 2>/dev/null')
    server.cmd('killall tcpdump 2>/dev/null')
    net.stop()

if __name__ == '__main__':
    setLogLevel('info')
    main()