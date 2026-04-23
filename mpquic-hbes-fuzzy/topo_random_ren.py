import random

bandwidth_min, bandwidth_max = 0.1, 10.0
delay_min, delay_max = 0, 200

mptcpTopos_random = []
for _ in range(100):

    bandwidth_values = [round(random.uniform(bandwidth_min, bandwidth_max), 2) for _ in range(2)]
    delay_values = [round(random.uniform(delay_min, delay_max), 2) for _ in range(2)]

    topology = {
        'paths': [
            {'queuingDelay': '0.048', 'bandwidth': "%.2f" % bandwidth_values[0], 'delay': "%.2f" % delay_values[0],
             'jitter': '0'},
            {'queuingDelay': '0.048', 'bandwidth': "%.2f" % bandwidth_values[1], 'delay': "%.2f" % delay_values[1],
             'jitter': '0'}
        ],
        'netem': [(0, 0, 'loss 0.00%'), (1, 0, 'loss 0.00%')]
    }
    mptcpTopos_random.append(topology)


i = 0
for topos in mptcpTopos_random:
    print(mptcpTopos_random[i]['paths'])
    print("\n")
    i = i + 1
